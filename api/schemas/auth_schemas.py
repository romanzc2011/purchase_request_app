# api/schemas/auth_schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional

class Token(BaseModel):
    access_token: str

class TokenData(BaseModel):
    username: str
    groups: List[str]

class LDAPUser(BaseModel):
    username: str
    email: Optional[str] = None
    groups: List[str] = Field(alias="approved")
