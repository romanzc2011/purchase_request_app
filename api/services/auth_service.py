from asyncio import Server
from api.services.cache_service import cache_service
import os, jwt
from urllib.parse import urlparse
from sqlite3 import Connection
from datetime import datetime, timedelta, timezone
from typing import Optional
from jwt.exceptions import InvalidTokenError
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from loguru import logger
from ldap3.core.exceptions import LDAPBindError
from ldap3 import Server, Connection, ALL, SUBTREE, Tls

from api.services.ldap_service import LDAPService
from api.settings import settings 
from api.schemas.auth_schemas import LDAPUser
"""
AUTHOR: ROMAN CAMPBELL
DATE: 04/10/2025
AUTH SERVICE -- handles JWT creation and verification
"""
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

class AuthService:
    def __init__(self, ldap_service: LDAPService):
        self.ldap_service = ldap_service
        self.JWT_SECRET_KEY = settings.jwt_secret_key
        self.ALGORITHM = "HS256"
    
    async def get_user(self, username: str) -> LDAPUser:
        return await self.ldap_service.fetch_usernames(username)
    
    #####################################################################################
    ## CREATE ACCESS TOKEN
    def create_access_token(
        self,
        user: LDAPUser,
        expires_delta: timedelta | None = None
    ) -> str:
        to_encode = {
            "sub": user.username,
            "email": user.email,
            "groups": user.groups
        }
        
        expire = (
            datetime.now(timezone.utc) + expires_delta
            if expires_delta
            else datetime.now(timezone.utc) + timedelta(minutes=15)
        )
        to_encode["exp"] = expire
        return jwt.encode(to_encode, self.JWT_SECRET_KEY, algorithm=self.ALGORITHM)
        
    #####################################################################################
    ## AUTHENTICATE USER
    async def authenticate_user(
        self,
        form_data: OAuth2PasswordRequestForm
    ) -> Optional[LDAPUser]:
        logger.info("🔑 Authenticating User()")
        username = form_data.username
        password = form_data.password
        logger.info(f"Username: {username}")
        
        # Verify users creds by binding
        parsed = urlparse(settings.ldap_server)
        host = parsed.hostname or parsed.path
        port = parsed.port or settings.ldap_port

        if not '\\' in username and not '@' in username:
            username = f"ADU\\{username}"
            
        try:
            user_conn = Connection(
                Server(host, port, use_ssl=True, get_info=ALL),
                user=username,
                password=password,
                auto_bind=True,
                receive_timeout=10,
            )
            user_conn.unbind()
        except LDAPBindError:
            logger.error(f"Failed to bind user: {username}")
            return None
        
        # Now authenticated, lookup email and groups
        email = await self.ldap_service.get_email_address(username)
        groups = await self.ldap_service.check_user_membership(username)
        
        return LDAPUser(username=username, email=email, groups=[g for g, ok in groups.items() if ok])

    #####################################################################################
    ## Get Current LDAPUser
    async def get_current_user(
        self,
        token: str = Depends(oauth2_scheme)
    ) -> LDAPUser:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, self.JWT_SECRET_KEY, algorithms=[self.ALGORITHM])
            username: str = payload.get("sub")
            
            if not username:
                raise credentials_exception
            
        except InvalidTokenError:
            raise credentials_exception
        
        user = await cache_service.get_or_set_async(
            "auth_users",
            username,
            lambda: self.ldap_service.fetch_user(username)
        )
        if user is None:
            raise credentials_exception
        
        logger.info(f"CURRENT USER VALIDATED: {user}")
        return user