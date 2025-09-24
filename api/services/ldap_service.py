# api/services/ldap_service.py

import asyncio
import ssl
from typing import List, Dict
from urllib.parse import urlparse

from ldap3 import Server, Connection, ALL, SUBTREE, Tls
from ldap3.core.exceptions import LDAPExceptionError, LDAPSocketOpenError
from aiocache import cached, Cache
from loguru import logger

from api.schemas.enums import LDAPGroup
from api.schemas.ldap_schema import LDAPUser
from api.settings import settings 
from api.utils.logging_utils import logger_init_ok
from api.services.socketio_server.sio_instance import sio
from api.services.socketio_server.sio_instance import emit_async
from api.services.socketio_server.socket_state import user_sids

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
        logger_init_ok(f"LDAP bound successful")
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
            # Send error message to frontend to show user
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
            if raw_name is None:
                return None
            raw_name = raw_name.lower()
            if "adu\\" in raw_name:
                raw_name = raw_name.replace("adu\\", "")
            
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
            if username is None:
                return None
            username = username.lower()
            if "adu\\" in username:
                username = username.replace("adu\\", "")
            
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
            if username is None:
                return {}
            # String ADU\\ from username if present
            username = username.lower()
            if "adu\\" in username:
                username = username.replace("adu\\", "")
            
            user_dn = self._subtree_user_search(username)
            if not user_dn:
                logger.error(f"No user DN found for {username}")
                return { LDAPGroup.IT_GROUP: False, LDAPGroup.CUE_GROUP: False, LDAPGroup.ACCESS_GROUP: False }
            
            conn = self.get_service_connection()
            
            # Set results dictionary
            results = { LDAPGroup.IT_GROUP: False, LDAPGroup.CUE_GROUP: False, LDAPGroup.ACCESS_GROUP: False  } 
            
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
                    
            # Find any login that has all false, then reject their login and explain they are not allowed login to submit request
            if not any(results.values()):
                # Find sid for the user to target the specific user
                target_sid = None
                if username and username in user_sids:
                    target_sid = next(iter(user_sids[username]), None)
                
                emit_async("ERROR", {
                    "event": "ERROR",
                    "status_code": "403",
                    "message": "You are not allowed to login to submit request"
                }, to=target_sid)
                return { LDAPGroup.IT_GROUP: False, LDAPGroup.CUE_GROUP: False, LDAPGroup.ACCESS_GROUP: False }
            else:
                # Find sid for the user to target the specific user
                target_sid = None
                if username and username in user_sids:
                    target_sid = next(iter(user_sids[username]), None)
                
                logger.info(f"MEMBERSHIP CHECK: target_sid={target_sid}, username={username}, user_sids={dict(user_sids)}")
                emit_async("USER_FOUND", {
                    "event": "USER_FOUND",
                    "status_code": "200",
                    "message": "You are allowed to login to submit request",
                }, to=target_sid)
            
            logger.info(f"RESULTS OF MEMBERSHIP SEARCH: {results}")
            return results
    
        except Exception as e:
            logger.error(f"Error getting membership: {e}")
            return { LDAPGroup.IT_GROUP: False, LDAPGroup.CUE_GROUP: False, LDAPGroup.ACCESS_GROUP: False }
    
    #-------------------------------------------------------------------------------------
    # PING SYNC --- keepalive strategy
    #-------------------------------------------------------------------------------------
    def _ping_sync(self):
        conn = self.get_service_connection()
        conn.search(
            search_base=settings.search_base,
            search_filter="(objectClass=*)",
            attributes=["cn"],
            size_limit=1
        )
        
    #-------------------------------------------------------------------------------------
    # KEEP ALIVE
    #-------------------------------------------------------------------------------------
    async def start_keepalive_ldap(self, interval_sec: int = 300):
        """Start LDAP keepalive in background task"""
        logger_init_ok(f"Starting LDAP keepalive with {interval_sec}s interval")
        while True:
            try:
                await asyncio.to_thread(self._ping_sync)
                logger.info("LDAP keepalive ping successful")
            except Exception as e:
                logger.error(f"Error keeping LDAP alive: {e}")
            await asyncio.sleep(interval_sec)
        
    #-------------------------------------------------------------------------------------
    # FETCH USERNAMES SYNCHRONOUSLY
    #-------------------------------------------------------------------------------------
    def _fetch_usernames_sync(self, query: str, username: str = None) -> List[str]:
        # LDAP structure to search for
        # OU=LAWB,OU=USCOURTS,DC=ADU,DC=DCN
        conn = self.get_service_connection()
        try:
            query = query.replace(" ", "")
            conn.search(
                search_base='OU=LAWB,OU=USCOURTS,DC=ADU,DC=DCN',
                search_filter=f'(sAMAccountName={query}*)',
                search_scope=SUBTREE,
                attributes=['sAMAccountName'],
                size_limit=10
            )

            if conn.entries:
                # Find sid for the user if username is provided
                target_sid = None
                if username and username in user_sids:
                    # Get the first sid for this user
                    target_sid = next(iter(user_sids[username]), None)
                
                logger.info(f"USER_FOUND: target_sid={target_sid}, username={username}, user_sids={dict(user_sids)}")
                emit_async("USER_FOUND", {
                    "event": "USER_FOUND",
                    "status_code": "200",
                    "message": "User found for query",
                }, to=target_sid)  # target specific user if sid found
                return [e.sAMAccountName.value for e in conn.entries]
            else:
                # Find sid for the user if username is provided
                target_sid = None
                if username and username in user_sids:
                    # Get the first sid for this user
                    target_sid = next(iter(user_sids[username]), None)
                
                emit_async("NO_USER_FOUND", {   
                    "event": "NO_USER_FOUND",
                    "status_code": "404",
                    "message": "No user found for query",
                }, to=target_sid)  # target specific user if sid found
                return []
        except Exception as e:
            logger.error(f"Error getting username: {e}")
            # Find sid for the user if username is provided
            target_sid = None
            if username and username in user_sids:
                # Get the first sid for this user
                target_sid = next(iter(user_sids[username]), None)
            
            emit_async("ERROR", {"message": f"LDAP error: {e}", "status_code": "500"}, to=target_sid)
            return ["Error"]
        
    ########################################################################################
    # FETCH USERNAMES SYNCHRONOUSLY
    ########################################################################################
    @run_in_thread
    def get_email_address(self, username: str) -> str|None:
        return self._get_email_sync(username)
    
    @run_in_thread
    def fetch_usernames(self, query: str, username: str = None) -> list[str]:
        return self._fetch_usernames_sync(query, username)
    
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