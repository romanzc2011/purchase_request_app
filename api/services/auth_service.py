from api.schemas.ldap_schema import LDAPUser
import jwt, asyncio
import time
from urllib.parse import urlparse
from datetime import datetime, timedelta, timezone
from typing import Optional
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from fastapi import HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from loguru import logger

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
        self.ldap_service = ldap_service
        self.set_test_user_override = None

    async def get_current_user_http(self, token: str = Depends(oauth2_scheme)) -> LDAPUser:
        """ FastAPI dependency for HTTP routes """
        return await self._user_from_access_token(token)
    
    # ----------------------------------------------------------------------------------
    # USER FROM ACCESS TOKEN
    # ----------------------------------------------------------------------------------
    async def _user_from_access_token(self, token: str) -> LDAPUser:
        try:
            payload = jwt.decode(token, self.JWT_SECRET_KEY, algorithms=[self.ALGORITHM])
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return LDAPUser(
            username=payload["sub"],
            email=payload.get("email"),
            groups=payload.get("groups", [])
        )
        
    # ----------------------------------------------------------------------------------
    # CREATE ACCESS TOKEN
    # ----------------------------------------------------------------------------------
    def create_access_token(
        self,
        user: LDAPUser,
        *,
        expires_seconds: int = 3600
    ) -> str:

        logger.info("########################################################")
        logger.info(f"LDAP_USER: {user}")
        logger.info(f"LDAP_USER username: {user.username}")
        logger.info(f"LDAP_USER email: {user.email}")
        logger.info(f"LDAP_USER groups: {user.groups}")
        logger.info("########################################################")
        
        payload = {
            "sub": user.username,
            "email": user.email, 
            "groups": user.groups,
            "exp": int(time.time()) + expires_seconds,
            "type": "access",
        }
        return jwt.encode(payload, self.JWT_SECRET_KEY, algorithm=self.ALGORITHM)
    
    # ----------------------------------------------------------------------------------
    # CREATE REFRESH TOKEN
    # ----------------------------------------------------------------------------------
    def create_refresh_token(self, user: LDAPUser, *, expires_seconds: int = 30 * 24 *3600) -> str:
        payload = {
            "sub": user.username,
            "email": user.email, 
            "groups": user.groups,
            "exp": int(time.time()) + expires_seconds,
            "type": "refresh",
        }
        return jwt.encode(payload, self.JWT_SECRET_KEY, algorithm=self.ALGORITHM)
    
    # ----------------------------------------------------------------------------------
    # VALIDATE ACCESS TOKEN
    # ----------------------------------------------------------------------------------
    def validate_refresh(self, refresh_token: str) -> str:
        payload = jwt.decode(refresh_token, self.JWT_SECRET_KEY, algorithms=[self.ALGORITHM])
        if payload["type"] != "refresh":
            raise InvalidTokenError("wrong token type")
        return payload["sub"]
    
    # ----------------------------------------------------------------------------------
    # TEST USER OVERRIDE
    # ----------------------------------------------------------------------------------
    def set_test_user_override(self, username: str, email: str = None, groups: list = None):
        """
        Override the current user for testing purposes
        Usage: auth_service.set_test_user_override("test_user", "test@example.com", ["IT", "ADMIN"])
        """
        self.set_test_user_override = LDAPUser(
            username=username,
            email=email or f"{username}@lawb.uscourts.gov",
            groups=groups or ["IT"]
        )
        logger.warning(f"🔧 TEST USER OVERRIDE SET: {self.set_test_user_override}")
    
    def clear_test_user_override(self):
        """Clear the test user override"""
        self.set_test_user_override = None
        logger.warning("🔧 TEST USER OVERRIDE CLEARED")


    # ----------------------------------------------------------------------------------
    # AUTHENTICATE USER
    # ----------------------------------------------------------------------------------
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
            
    # ----------------------------------------------------------------------------------
    # GET CURRENT LDAPUSER
    # ----------------------------------------------------------------------------------
    async def get_current_user(self, token: str = Depends(oauth2_scheme)) -> LDAPUser:
        # Check for test override first
        if self.set_test_user_override:
            logger.warning(f"🔧 USING TEST USER OVERRIDE: {self.set_test_user_override}")
            return self.set_test_user_override
            
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
            
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )