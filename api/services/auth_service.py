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
from api.schemas.pydantic_schemas import AuthUser
"""
AUTHOR: ROMAN CAMPBELL
DATE: 04/10/2025
AUTH SERVICE -- handles JWT creation and verification
"""

class AuthService:
    def __init__(self, ldap_service: LDAPService):
        self.ldap_service = ldap_service
        self.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    
    def get_user(self, username: str) -> AuthUser:
        return self.ldap_service.fetch_usernames(username)
    
    #####################################################################################
    ## CREATE ACCESS TOKEN
    def create_access_token(self, data: AuthUser, expires_delta: timedelta | None = None):
        logger.info(f"user: {data}")
        to_encode = data.dict()     
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
            
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.JWT_SECRET_KEY, algorithm="HS256")
        return encoded_jwt
        
    #####################################################################################
    ## AUTHENTICATE USER
    def authenticate_user(
        self, form_data: OAuth2PasswordRequestForm) -> Optional[AuthUser]:
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
        return AuthUser(username=username, email=email, groups=list(groups.keys()))
    
    #####################################################################################
    ## Login
    async def login(
        self, form_data: OAuth2PasswordRequestForm = Depends(OAuth2PasswordBearer(tokenUrl="/api/login"))
    ) -> dict:
        user = self.authenticate_user(form_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = self.create_access_token(user)      
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "user": user.model_dump(),
        }
        
    #####################################################################################
    ## Get Current AuthUser
    async def get_current_user(self, token: str = Depends(OAuth2PasswordBearer(tokenUrl="/api/login"))) -> Optional[AuthUser]:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, self.JWT_SECRET_KEY, algorithms=["HS256"])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
            token_data = TokenData(username=username)
        except InvalidTokenError:
            raise credentials_exception
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            raise HTTPException(status_code=500, detail="Error getting current user")
        user = self.ldap_service.get_user_by_username(token_data.username)
        if user is None:
            raise credentials_exception
        return user
    
    #####################################################################################
    ## GET CURRENT ACTIVE USER
    async def get_current_active_user(
        self,
        current_user: Annotated[AuthUser, Depends(lambda:self.get_current_user)]
    ) -> AuthUser:
        if not current_user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
        return current_user

