from api.schemas.ldap_schema import LDAPUser
import jwt, asyncio
from urllib.parse import urlparse
from datetime import datetime, timedelta, timezone
from typing import Optional
from jwt.exceptions import InvalidTokenError
from fastapi import HTTPException, Depends, status
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
        self.expire_minutes = 60
        self.ldap_service = ldap_service
        # Test override - set to None in production
        self._test_user_override = None

    #####################################################################################
    ## TEST OVERRIDE - FOR TESTING ONLY
    #####################################################################################
    def set_test_user_override(self, username: str, email: str = None, groups: list = None):
        """
        Override the current user for testing purposes
        Usage: auth_service.set_test_user_override("test_user", "test@example.com", ["IT", "ADMIN"])
        """
        self._test_user_override = LDAPUser(
            username=username,
            email=email or f"{username}@lawb.uscourts.gov",
            groups=groups or ["IT"]
        )
        logger.warning(f"🔧 TEST USER OVERRIDE SET: {self._test_user_override}")
    
    def clear_test_user_override(self):
        """Clear the test user override"""
        self._test_user_override = None
        logger.warning("🔧 TEST USER OVERRIDE CLEARED")

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
            return username
        
        return await LDAPUser.from_ldap(username, self.ldap_service)
            
    #####################################################################################
    ## Get Current LDAPUser
    async def get_current_user(self, token: str = Depends(oauth2_scheme)) -> LDAPUser:
        # Check for test override first
        if self._test_user_override:
            logger.warning(f"🔧 USING TEST USER OVERRIDE: {self._test_user_override}")
            return self._test_user_override
            
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