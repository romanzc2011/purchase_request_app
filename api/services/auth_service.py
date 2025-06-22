from asyncio import Server
from api.schemas.ldap_schema import LDAPUser
from api.services.cache_service import cache_service
import os, jwt, asyncio
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
from aiocache import cached, Cache

from api.services.ldap_service import LDAPService
from api.settings import settings 
"""
AUTHOR: ROMAN CAMPBELL
DATE: 04/10/2025
AUTH SERVICE -- handles JWT creation and verification
"""
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

def run_in_thread(fn):
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(fn, *args, **kwargs)
    return wrapper

class AuthService:
    def __init__(self, ldap_service: LDAPService):
        self.JWT_SECRET_KEY = settings.jwt_secret_key
        self.ALGORITHM = "HS256"
        self.expire_minutes = 60
        self.ldap_service = ldap_service

    #####################################################################################
    ## CREATE ACCESS TOKEN
    async def create_access_token(
        self,
        user: LDAPUser,
        expires_delta: timedelta | None = None
    ) -> str:

        logger.info("########################################################")
        logger.info(f"LDAP_USER: {user}")
        logger.info(f"LDAP_USER username: {user.username}")
        logger.info(f"LDAP_USER email: {user.email}")
        logger.info(f"LDAP_USER groups: {user.groups}")
        logger.info("########################################################")
        
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=self.expire_minutes))
        
        to_encode = {
            "sub": user.username,
            "email": user.email,
            "groups": user.groups,
            "exp": expire
        }
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
        
        if not await self.ldap_service.verify_credentials(username, password):
            logger.error(f"Failed to bind user: {username}")
            return None
        
        return await LDAPUser.from_ldap(username, self.ldap_service)
            
    #####################################################################################
    ## Get Current LDAPUser
    async def get_current_user(self, token: str = Depends(oauth2_scheme)) -> LDAPUser:
        try:
            payload = jwt.decode(token, self.JWT_SECRET_KEY, algorithms=[self.ALGORITHM])
            return LDAPUser(
                username=payload["sub"],
                email=payload.get("email"),
                groups=payload.get("groups", [])
            )
        except InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
  