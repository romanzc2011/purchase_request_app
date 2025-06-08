# api/services/ldap_service.py

import os
import asyncio
import re
import ssl
from typing import Optional, List, Dict
from functools import lru_cache
from urllib.parse import urlparse

from ldap3 import Server, Connection, ALL, SUBTREE, Tls
from ldap3.core.exceptions import LDAPExceptionError
from aiocache import cached, Cache
from loguru import logger

from api.schemas.auth_schemas import LDAPUser
from api.settings import settings


class LDAPService:

    def __init__(
        self,
        ldap_url: str,
        bind_dn: str,
        bind_password: str,
        group_dns: List[str],
    ):
        """
        ldap_url: e.g. "ldaps://adu.dcn" or "ldap://adu.dcn:389"
        bind_dn / bind_password: your service account credentials
        group_dns: list of DN strings for PurchaseRequest_IT, _CUE, _Access
        """
        self.ldap_url     = ldap_url
        self.bind_dn      = bind_dn
        self.bind_password= bind_password
        self.group_dns    = group_dns

    def tls_config(self) -> Tls:
        # Skip certificate verification; for production use CERT_REQUIRED + ca_certs_file
        return Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1_2)

    #-------------------------------------------------------------------
    # Make connection
    #-------------------------------------------------------------------
    @lru_cache(maxsize=1)
    def _make_connection(self) -> Connection:
        # Parse out host and port from the URL
        parsed  = urlparse(self.ldap_url)
        host    = parsed.hostname or parsed.path
        port    = parsed.port or (636 if parsed.scheme == "ldaps" else 389)

        # Implicit TLS over 636
        server = Server(
            host,
            port=port,
            use_ssl=True,
            get_info=ALL
        )

        conn = Connection(
            server,
            user=self.bind_dn,
            password=self.bind_password,
            auto_bind=True,
            receive_timeout=10
        )
        return conn
    
    #-------------------------------------------------------------------
    # Get connection
    #-------------------------------------------------------------------
    def get_connection(self) -> Connection:
        conn = self._make_connection()
        if not conn.bound:
            # clear cache so next call will re-bind
            self._make_connection.cache_clear()
            conn = self._make_connection()
        return conn

    #-------------------------------------------------------------------
    # Get email address
    #-------------------------------------------------------------------
    def _get_email_sync(self, username: str) -> Optional[str]:
        """Blocking call: looks up sAMAccountName → mail"""
        logger.info(f"Getting email for {username}")
        conn = self.get_connection()

        raw_name = username.split("\\")[-1]
        try:
            conn = self._make_connection()
            conn.search(
                search_base=settings.search_base,
                search_filter=f"(sAMAccountName={raw_name})",
                search_scope=SUBTREE,
                attributes=["mail"],
                time_limit=5
            )
            if conn.entries:
                return conn.entries[0].mail.value
        except LDAPExceptionError as e:
            logger.error(f"LDAP error fetching email for {username}: {e}")
        logger.info(f"Going back with {username}")
        return None

    #-------------------------------------------------------------------
    # Check user membership
    #-------------------------------------------------------------------
    def _get_membership_sync(self, username: str) -> Dict[str, bool]:
        """
        Blocking call: iterates over self.group_dns,
        checks group members, and flags IT/CUE/ACCESS.
        """
        results = {
            "IT_GROUP":      False,
            "CUE_GROUP":     False,
            "ACCESS_GROUP":  False,
        }
        
        try:
            conn = self.get_connection()
            for group_dn in self.group_dns:
                conn.search(
                    search_base=group_dn,
                    search_filter="(objectClass=group)",
                    search_scope=SUBTREE,
                    attributes=["member"],
                    time_limit=3
                )
                if not conn.entries:
                    continue

                m = re.search(r"CN=LAWB_([^,]+)", group_dn)
                if not m:
                    continue
                suffix = m.group(1)  # e.g. "PurchaseRequest_IT"

                if suffix == "PurchaseRequest_IT":
                    key = "IT_GROUP"
                elif suffix == "PurchaseRequest_CUE":
                    key = "CUE_GROUP"
                elif suffix == "PurchaseRequest_Access":
                    key = "ACCESS_GROUP"
                else:
                    continue

                # check members
                for member_dn in conn.entries[0].member.values or []:
                    conn.search(
                        search_base=member_dn,
                        search_filter="(objectClass=person)",
                        search_scope=SUBTREE,
                        attributes=["sAMAccountName"],
                        time_limit=2
                    )
                    if conn.entries and conn.entries[0].sAMAccountName.value.lower() == username.lower():
                        results[key] = True
                        break

        except LDAPExceptionError as e:
            logger.error(f"LDAP error fetching membership for {username}: {e}")

        return results
    
    #-------------------------------------------------------------------
    # Fetch usernames
    #-------------------------------------------------------------------
    def _fetch_usernames_sync(self, query: str) -> List[str]:
        # LDAP structure to search for
        # OU=LAWB,OU=USCOURTS,DC=ADU,DC=DCN
        conn = self.get_connection()

        # Perform subtree search
        try:
            conn.search(
                search_base='OU=LAWB,OU=USCOURTS,DC=ADU,DC=DCN',
                search_filter=f'(sAMAccountName={query}*)',
                search_scope=SUBTREE,
                attributes=['sAMAccountName'],
                size_limit=10  # Limit to 10 results
            )
            
            if conn.entries:
                logger.info(f"Found {len(conn.entries)} entries for query: {query}")
                logger.info(f"Raw entries: {conn.entries}")
                logger.info(f"Entry attributes: {[entry.entry_attributes for entry in conn.entries]}")
                logger.info(f"Entry JSON: {[entry.entry_to_json() for entry in conn.entries]}")
                return [entry.sAMAccountName.value for entry in conn.entries]
            else:
                logger.error(f"No user found for query: {query}")
                return ["Error"]
        except Exception as e:
            logger.error(f"Error getting username: {e}")
            return ["Error"]
    
    #-------------------------------------------------------------------
    # ASYNC FUNCTIONS
    #-------------------------------------------------------------------
    
    #-------------------------------------------------------------------
    # Check user membership - async
    #-------------------------------------------------------------------
    async def check_user_membership(self, username: str) -> Dict[str, bool]:
        """Async wrapper for _get_membership_sync"""
        return await asyncio.to_thread(self._get_membership_sync, username)

    #-------------------------------------------------------------------
    # Fetch user - async
    #-------------------------------------------------------------------
    @cached(
        ttl=300,
        cache=Cache.MEMORY,
        key_builder=lambda fn, self, username: f"ldap_email:{username.lower()}"
    )
    async def fetch_user(self, username: str) -> LDAPUser:
        """
        High-level: get both email + group list,
        and return a Pydantic LDAPUser.
        """
        groups = await self.check_user_membership(username)
        email  = await self.get_email_address(username)
        approved = [g for g, allowed in groups.items() if allowed]
        logger.info(f"List of groups {username} is member of:")
        logger.info(f"{approved}")
        return LDAPUser(username=username, email=email or "", groups=approved)
    
    #-------------------------------------------------------------------
    # Get email address - async
    #-------------------------------------------------------------------
    @cached(
        ttl=300,
        cache=Cache.MEMORY,
        key_builder=lambda fn, self, username: f"ldap_email:{username.lower()}"
    )
    async def get_email_address(self, username: str) -> Optional[str]:
        """Async wrapper for _get_email_sync"""
        start = asyncio.get_event_loop().time()
        email = await asyncio.to_thread(self._get_email_sync, username)
        elapsed = asyncio.get_event_loop().time() - start
        logger.info(f"LDAP email lookup for {username} took {elapsed:.2f}s")

        return email
    
    #-------------------------------------------------------------------
    # Fetch usernames - async
    #-------------------------------------------------------------------
    async def fetch_usernames(self, query: str) -> List[str]:
        """Async wrapper for fetch_usernames"""
        return await asyncio.to_thread(self._fetch_usernames_sync, query)