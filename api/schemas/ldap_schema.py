# api/schemas/auth_schemas.py
from pydantic import BaseModel, EmailStr, Field
from loguru import logger
from typing import List, Optional

class Token(BaseModel):
    access_token: str

class TokenData(BaseModel):
    username: str
    groups: List[str]

class LDAPUser(BaseModel):
    username: str
    email: Optional[str] = None
    groups: List[str]
    
    @classmethod
    async def from_ldap(cls, username: str, ldap_service) -> "LDAPUser":
        email = await ldap_service.get_email_address(username)
        group_map = await ldap_service.check_user_membership(username)
        groups = [g for g, ok in group_map.items() if ok]
        
        return cls(username=username, email=email, groups=groups)
    
    def has_group(self, group: str) -> bool:
        return group in self.groups
