# api/schemas/auth_schemas.py
from pydantic import BaseModel, EmailStr
from typing import List

class Token(BaseModel):
    access_token: str

class TokenData(BaseModel):
    username: str
    groups: List[str]

class LDAPUser(BaseModel):
    username: str
    email: EmailStr
    groups: List[str]
