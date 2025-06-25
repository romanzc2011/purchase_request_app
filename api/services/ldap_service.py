# api/services/ldap_service.py

from dataclasses import dataclass
import os
import asyncio
import re
import ssl
from typing import Optional, List, Dict
from functools import lru_cache
from urllib.parse import urlparse

from ldap3 import Server, Connection, ALL, SUBTREE, Tls
from ldap3.core.exceptions import LDAPExceptionError, LDAPSocketOpenError
from aiocache import cached, Cache
from loguru import logger

from api.schemas.ldap_schema import LDAPUser
from api.settings import settings 

def run_in_thread(fn):
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(fn, *args, **kwargs)
    return wrapper

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
        self._service_conn = self._bind(self.bind_dn, self.bind_password, use_tls=True)

    #-------------------------------------------------------------------------------------
    # TLS CONFIG
    #-------------------------------------------------------------------------------------
    def tls_config(self) -> Tls:
        # Skip certificate verification; for production use CERT_REQUIRED + ca_certs_file
        return Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1_2)
    
    #-------------------------------------------------------------------------------------
    # PARSE HOST PORT
    #-------------------------------------------------------------------------------------
    def _parse_host_port(self, url: str) -> tuple[str, int, bool]:
        parsed = urlparse(url)
        host = parsed.hostname or parsed.path
        port = parsed.port or (636 if parsed.scheme == "ldaps" else 389)
        use_ssl = parsed.scheme == "ldaps"
        return host, port, use_ssl
    
    #-------------------------------------------------------------------------------------
    # BIND
    #-------------------------------------------------------------------------------------
    def _bind(self, user_dn: str, password: str, *, use_tls: bool=False) -> Connection:
        host, port, use_ssl = self._parse_host_port(self.ldap_url)
        server = Server(host, port=port, use_ssl=use_ssl, get_info=ALL, tls=self.tls_config() if use_tls else None)
        conn = Connection(server, user=user_dn, password=password, auto_bind=True, receive_timeout=10)
        logger.info(f"LDAP BOUND: {conn.bound}")
        return conn
    
    #-------------------------------------------------------------------------------------
    # GET SERVICE CONNECTION
    #-------------------------------------------------------------------------------------
    def get_service_connection(self) -> Connection:
        try:
            if not self._service_conn or not self._service_conn.bound:
                logger.info("LDAP connection is not bound. Rebinding...")
                self._service_conn = self._bind(self.bind_dn, self.bind_password, use_tls=True)
            else:
                # Force socket use to check health of connection
                self._service_conn.search(
                search_base=settings.search_base,
                search_filter="(objectClass=*)",
                attributes=["cn"],
                size_limit=1
            )
            return self._service_conn
        except (LDAPSocketOpenError, LDAPExceptionError, ssl.SSLError, OSError) as e:
            logger.warning(f"LDAP socket error or SSL failure detected: {e}. Rebinding...")
            try:
                self._service_conn = self._bind(self.bind_dn, self.bind_password, use_tls=True)
                return self._service_conn
            except Exception as ex:
                logger.error(f"Failed to rebind LDAP connection: {ex}")
                raise
    
    async def verify_credentials(self, username: str, password: str) -> bool:
        """Async helper to test bind as an end user"""
        def _test_bind():
            try:
                conn = self._bind(username, password, use_tls=True)
                conn.unbind()
                return True
            except LDAPExceptionError as e:
                logger.error(f"LDAP error verifying credentials for {username}: {e}")
                return False
        return await asyncio.to_thread(_test_bind)

    #-------------------------------------------------------------------------------------
    # SEARCH
    #-------------------------------------------------------------------------------------
    def _search(
    self,
    conn: Connection,
    search_base: str,
    search_filter: str,
    attributes: List[str],
    search_scope=SUBTREE,
    size_limit: int | None = None,
    time_limit: int | None = None,
):
        params: dict[str,int] = {}
        if size_limit  is not None: params["size_limit"]  = size_limit
        if time_limit  is not None: params["time_limit"]  = time_limit
        return conn.search(
            search_base=search_base,
            search_filter=search_filter,
            search_scope=search_scope,
            attributes=attributes,
            **params,
        )
    
    #-------------------------------------------------------------------------------------
    # GET EMAIL
    #-------------------------------------------------------------------------------------
    def _get_email_sync(self, raw_name: str) -> str|None:
        """
        Get email address from LDAP.
        """
        try:
            raw_name = raw_name.lower()
            if "adu\\" in raw_name:
                raw_name = raw_name.replace("adu\\", "")
                logger.debug(f"Removed ADU\\ from username: {raw_name}")
            
            conn = self.get_service_connection()
            conn.search(
                search_base=settings.search_base,
                search_filter=f"(sAMAccountName={raw_name})",
                attributes=["mail"],
            )
            if conn.entries:
                return conn.entries[0].mail.value
            
        except LDAPExceptionError as e:
            logger.error(f"LDAP error fetching email for {raw_name}: {e}")
            return None
        
    #-------------------------------------------------------------------------------------
    # SUBTREE USER SEARCH
    #-------------------------------------------------------------------------------------
    def _subtree_user_search(self, username: str) -> str | None:
        """
        Sync method to fetch full DN of user
        """
        try:
            username = username.lower()
            if "adu\\" in username:
                username = username.replace("adu\\", "")
                logger.debug(f"Removed ADU\\ from username: {username}")
            
            conn = self.get_service_connection()
            conn.search(
                search_base=settings.search_base,
                search_filter=f"(sAMAccountName={username})",
                attributes=["distinguishedName"],
            )
            if conn.entries:
                return conn.entries[0].entry_dn  # Gives full DN string
            
        except LDAPExceptionError as e:
            logger.error(f"LDAP error fetching DN for {username}: {e}")
        return None
    
    #-------------------------------------------------------------------------------------
    # GET MEMBERSHIP
    #-------------------------------------------------------------------------------------
    def _get_membership_sync(self, username: str) -> Dict[str, bool]:
        """
        Sync method to fetch membership of user
        """
        try:
            # String ADU\\ from username if present
            username = username.lower()
            if "adu\\" in username:
                username = username.replace("adu\\", "")
                logger.debug(f"Removed ADU\\ from username: {username}")
            
            user_dn = self._subtree_user_search(username)
            if not user_dn:
                logger.error(f"No user DN found for {username}")
                return {"IT_GROUP": False, "CUE_GROUP": False, "ACCESS_GROUP": False}
            
            conn = self.get_service_connection()
            
            # Set results dictionary
            results = {"IT_GROUP": False, "CUE_GROUP": False, "ACCESS_GROUP": False} 
            
            for group_dn, key in zip(self.group_dns, results):
                success = self._search(conn, group_dn, "(objectClass=group)", ["member"])
                if not success:
                    logger.error(f"LDAP search for group {group_dn} failed")
                    continue
                
                entries = conn.entries
                logger.debug(f"LDAP membership search in {group_dn} returned {len(entries)} entries")
                
                for entry in entries:
                    members = entry.member.values
                    if user_dn.lower() in [m.lower() for m in members]:
                        results[key] = True
                        break
            
            logger.info(f"RESULTS OF MEMBERSHIP SEARCH: {results}")
            return results
    
        except Exception as e:
            logger.error(f"Error getting membership: {e}")
            return {"IT_GROUP": False, "CUE_GROUP": False, "ACCESS_GROUP": False}
        
    #-------------------------------------------------------------------------------------
    # FETCH USERNAMES SYNCHRONOUSLY
    #-------------------------------------------------------------------------------------
    def _fetch_usernames_sync(self, query: str) -> List[str]:
        # LDAP structure to search for
        # OU=LAWB,OU=USCOURTS,DC=ADU,DC=DCN
        conn = self.get_service_connection()

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
    
    ########################################################################################
    # FETCH USERNAMES SYNCHRONOUSLY
    ########################################################################################
    @run_in_thread
    def get_email_address(self, username: str) -> str|None:
        return self._get_email_sync(username)
    
    @run_in_thread
    def fetch_usernames(self, query: str) -> list[str]:
        return self._fetch_usernames_sync(query)
    
    @run_in_thread
    def check_user_membership(self, username: str) -> dict[str, bool]:
        return self._get_membership_sync(username)
    
    ########################################################################################
    # FETCH USERNAMES ASYNCHRONOUSLY
    ########################################################################################
    async def fetch_user_email(self, username: str) -> LDAPUser:
        groups = await self.check_user_membership(username)
        email = await self.get_email_address(username)
        user_groups = [g for g,ok in groups.items() if ok]
        return LDAPUser(username=username, email=email, groups=user_groups)
    
    #####################################################################################
    ## FETCH USER ASYNCHRONOUSLY
    @run_in_thread
    def fetch_user(self, username: str) -> LDAPUser:
        """Blocking under the hood, but exposed async and cached"""
        groups = self._get_membership_sync(username)
        email = self._get_email_sync(username)
        user_groups = [g for g,ok in groups.items() if ok]
        return LDAPUser(username=username, email=email, groups=user_groups)