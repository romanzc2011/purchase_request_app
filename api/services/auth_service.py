import os, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Annotated
from jwt.exceptions import InvalidTokenError
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from loguru import logger

from api.services.ldap_service import LDAPService
from api.settings import settings 
from api.schemas.pydantic_schemas import TokenData
from api.schemas.pydantic_schemas import LDAPUser
"""
AUTHOR: ROMAN CAMPBELL
DATE: 04/10/2025
AUTH SERVICE -- handles JWT creation and verification
"""
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

class AuthService:
    def __init__(self, ldap_service: LDAPService):
        self.ldap_service = ldap_service
        self.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
        self.ALGORITHM = "HS256"
    
    def get_user(self, username: str) -> LDAPUser:
        return self.ldap_service.fetch_usernames(username)
    
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
    def authenticate_user(
        self, form_data: OAuth2PasswordRequestForm) -> Optional[LDAPUser]:
        """
        Attempt an LDAP bind. On success, return a rich User object.
        """
        logger.info("""
            #####################################################################
            Authenticating User()
            #####################################################################""")
        logger.info(f"AUTHENTICATING USER: {form_data.username}")
        logger.info(f"PASSWORD: {form_data.password}")
        username = form_data.username
        password = form_data.password
        connection = self.ldap_service.create_connection(username, password)
        if not connection:
            return None
        
        email = self.ldap_service.get_email_address(connection, username)
        groups = self.ldap_service.check_user_membership(connection, username)
        return LDAPUser(username=username, email=email, groups=list(groups.keys()))
    
    #####################################################################################
    ## Login
    async def login(
        self,
        form_data: OAuth2PasswordRequestForm = Depends()
    ) -> dict:
        user = self.authenticate_user(form_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = self.create_access_token(user)      
        return {
            "access_token": token,
            "token_type": "Bearer",
            "user": user.model_dump(),
        }
        
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
        
        user = self.ldap_service.fetch_user(username)
        if user is None:
            raise credentials_exception
        
        logger.info(f"CURRENT USER VALIDATED: {user}")
        return user
    
    #####################################################################################
    ## GET CURRENT ACTIVE USER
    async def get_current_active_user(
        self,
        current_user: Annotated[LDAPUser, Depends(lambda:self.get_current_user)]
    ) -> LDAPUser:
        if not current_user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
        return current_user

