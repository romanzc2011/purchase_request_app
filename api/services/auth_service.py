import os, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from loguru import logger

from api.services.ldap_service import LDAPService, User as LDAPUser
from api.settings import settings 

"""
AUTHOR: ROMAN CAMPBELL
DATE: 04/10/2025
AUTH SERVICE -- handles JWT creation and verification
"""

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

class AuthService:
    def __init__(self, ldap_service: LDAPService):
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")
        self.ldap_service = ldap_service
        
    #####################################################################################
    ## CREATE ACCESS TOKEN
    def create_access_token(self, identity: str, expires_delta: timedelta = timedelta(hours=1)) -> str:
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode = {"sub": identity, "exp": expire}
        token = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm="HS256")
        return token
    
    #####################################################################################
    ## VERIFY JWT TOKEN
    def verify_jwt_token(self, token: str):
        try: 
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
            return payload.get("sub")
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            logger.error(f"Error verifying JWT token: {e}")
            raise HTTPException(status_code=500, detail="Error verifying JWT token")
        
    #####################################################################################
    ## AUTHENTICATE USER
    def authenticate_user(
        self, form_data: OAuth2PasswordRequestForm = Depends()
    ) -> Optional[LDAPUser]:
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
        return LDAPUser(username=username, email=email, group=list(groups.keys()))
    
    #####################################################################################
    ## Login
    async def login(
        self, form_data: OAuth2PasswordRequestForm = Depends()
    ) -> dict:
        user = self.authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = self.create_access_token(user.username)      
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "user": user.model_dump(),
        }
        
    #####################################################################################
    ## Get Current User
    async def get_current_user(
        self,
        token: str = Depends(OAuth2PasswordBearer(tokenUrl="/api/login")),
    ) -> LDAPUser:
        username = self.verify_jwt_token(token)
        # Light weight lookup
        conn = self.ldap_service.create_connection(
            settings.ldap_service_user,
            settings.ldap_service_password,
        )
        if not conn:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        email = self.ldap_service.get_email_address(conn, username)
        groups = self.ldap_service.check_user_membership(conn, username)
        return LDAPUser(username=username, email=email, group=list(groups.keys()))

