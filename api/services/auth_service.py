import jwt
import os
from datetime import datetime, timedelta, timezone
from loguru import logger
from typing import Optional
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from api.services.ldap_service import LDAPService, User

"""
AUTHOR: ROMAN CAMPBELL
DATE: 04/10/2025
AUTH SERVICE -- handles JWT creation and verification
"""

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

class AuthService:
    def __init__(self):
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")
        
    #####################################################################################
    ## CREATE ACCESS TOKEN
    def create_access_token(self, identity: str, expires_delta: timedelta = timedelta(hours=1)):
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