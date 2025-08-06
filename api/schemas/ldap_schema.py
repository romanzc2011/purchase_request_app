# api/schemas/auth_schemas.py
from pydantic import BaseModel
from loguru import logger
from typing import List, Optional
from api.services.cache_service import cache_service

#-------------------------------------------------------------------------------------
# CONTRACTING OFFICER PAYLOAD
#-------------------------------------------------------------------------------------
class ContractingOfficerPayload(BaseModel):
    ID: str
    CO: str
    username: str
    email: str

#-------------------------------------------------------------------------------------
# TOKEN
#-------------------------------------------------------------------------------------
class Token(BaseModel):
    access_token: str

#-------------------------------------------------------------------------------------
# TOKEN DATA
#-------------------------------------------------------------------------------------
class TokenData(BaseModel):
    username: str
    groups: List[str]

#-------------------------------------------------------------------------------------
# LDAP USER
#-------------------------------------------------------------------------------------
class LDAPUser(BaseModel):
    username: str
    email: Optional[str] = None
    groups: List[str]
    
    #-------------------------------------------------------------------------------------
    # HAS GROUP
    #-------------------------------------------------------------------------------------
    def has_group(self, group_name: str) -> bool:
        return group_name in self.groups
    
    #-------------------------------------------------------------------------------------
    # FROM LDAP
    #-------------------------------------------------------------------------------------
    @classmethod
    async def from_ldap(cls, username: str, ldap_service) -> "LDAPUser":
        cache_key = f"ldap:{username.lower()}"
        
        cached_user_dict = cache_service.get("ldap_users", cache_key)
        if cached_user_dict:
            return cls(**cached_user_dict)
        
        # Not cached
        email = await ldap_service.get_email_address(username)
        group_map = await ldap_service.check_user_membership(username)
        groups = [g for g, ok in group_map.items() if ok]
        
        user = cls(username=username, email=email, groups=groups)
        
        # Store as dict so cache can serialize it easily
        cache_service.set("ldap_users", cache_key, user.model_dump())
        return user
    
	