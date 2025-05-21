from dataclasses import dataclass
from dotenv import load_dotenv
from flask import jsonify
from ldap3 import Server, Connection, Tls, ALL, SUBTREE
from ldap3.core.exceptions import LDAPExceptionError, LDAPBindError
from loguru import logger
from requests_ntlm import HttpNtlmAuth
from typing import Optional, List
import ssl
import os
import re

"""
AUTHOR: ROMAN CAMPBELL
DATE: 01/29/2025
LDAP manager class to manage ldap3 and querying the AD for authentication
"""
load_dotenv()

# List of Group DNs to check
IT_GROUP_DNS = os.getenv("IT_GROUP_DNS")
CUE_GROUP_DNS = os.getenv("CUE_GROUP_DNS")
ACCESS_GROUP_DNS = os.getenv("ACCESS_GROUP_DNS")

# Loop thru these to determine groups approved for user
group_dns = [
    IT_GROUP_DNS,
    CUE_GROUP_DNS,
    ACCESS_GROUP_DNS
]

# Send this array of groups to frontend
user_groups = {
    "ACCESS_GROUP": False,
    "CUE_GROUP": False,
    "IT_GROUP": False
}

@dataclass
class User:
    username: str
    email: str
    group: List[str]

class LDAPService:
    def __init__(self, server_name, port, using_tls, service_user, service_password, it_group_dns=False, cue_group_dns=False, access_group_dns=False):
        self.server_name = server_name
        self.port = port
        self.using_tls = using_tls
        self.service_user = service_user
        self.service_password = service_password
        self.requester = None
        self.it_group_dns = it_group_dns
        self.cue_group_dns = cue_group_dns
        self.access_group_dns = access_group_dns
        self.is_authenticated = False
        self.groups = None
        self.connection = None
        self.username = None  # Optionally initialize username

    #####################################################################################
    # BUILD USER OBJ
    @staticmethod
    def build_user_object(username: str, groups: dict[str,bool], email: Optional[str]) -> User:
        group_names = [k for k,v in groups.items() if v]
        return User(username, email or "unknown", group_names)
    
    #####################################################################################
    # GET CONNECTION of ldap service
    def create_connection(self, username, password):
        tls = None
        if self.using_tls:
            tls = self.tls_config()
        
        server = Server(self.server_name, port=self.port, use_ssl=self.using_tls, tls=tls, get_info=ALL)
        
        try:
            connection = Connection(server, user=username, password=password, auto_bind=True)
            
            if connection.bound:
                print("\n#####################################################################")
                print(f"\n✅ --- Successfully authenticated to {self.server_name}")
                print(f"\n# ---- Authenticated as: {username}")
                print("\n#####################################################################")
                self.set_is_authenticated(True)
                self.set_connection(connection)
                self.set_username(username)
                return connection
            else:
                logger.error(f"❌ Failed to bind to LDAP server: {self.server_name}")
                self.set_is_authenticated(False)
                self.set_connection(None)
                return None
        
        except LDAPExceptionError as e:
            logger.error("❌ LDAP Server Returned an Error:", str(e))
            self.set_is_authenticated(False)
            self.set_connection(None)
            return None
            # Raised when the server returns an explicit error (e.g., invalid credentials, insufficient permissions)
        
        except Exception as e:
            logger.error("❌ Unexpected Error:", str(e))
            self.set_is_authenticated(False)
            self.set_connection(None)
            return None
    
    #####################################################################################
    # TLS CONFIG
    def tls_config(self):
        tls_configure = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1_2)
        return tls_configure
  
    #####################################################################################
    # SEARCH FOR GROUP MEMBERSHIP
    def check_user_membership(self, connection, username):
        if connection is None:
            logger.error("Cannot check user membership: LDAP connection is None")
            return {"ACCESS_GROUP": False, "CUE_GROUP": False, "IT_GROUP": False}
            
        try:
            # Iterate thru the DNS Groups and determine what user is member of
            for group in group_dns:
                # Execute search
                connection.search(
                    search_base=group,
                    search_filter='(objectClass=group)',
                    search_scope=SUBTREE,
                    attributes=['member']
                )
                
                if connection.entries:
                    logger.info(f"Group DN: {group}")
                    logger.info(f"Raw entries: {connection.entries}")
                    logger.info(f"Entry attributes: {connection.entries[0].entry_attributes}")
                    logger.info(f"Entry JSON: {connection.entries[0].entry_to_json()}")
                    # Extract full DN of all members
                    group_entry = connection.entries[0]
                    members_dn_list = group_entry.member.values
                    logger.info(f"Members DN list: {members_dn_list}")
                    
                    match = re.search(r'CN=LAWB_([^,]+)', group)
                    group_name = match.group(1) if match else "Unknown"
                    for member_dn in members_dn_list:
                        # Query LDAP for each DN to get their sAMAccountName (username)
                        connection.search(
                            search_base=member_dn,
                            search_filter="(objectClass=person)",  # search for user object
                            search_scope=SUBTREE,
                            attributes=['sAMAccountName', 'mail']
                        )
            
                        if connection.entries:
                            member_username = connection.entries[0].sAMAccountName.value
                            if member_username.lower() == username.lower():
                                # Which group does user belong to
                                if "PurchaseRequest_IT" in group_name:
                                    self.it_group_dns = True
                                    user_groups["IT_GROUP"] = self.it_group_dns
                                    continue
                                    
                                elif "PurchaseRequest_CUE" in group_name:
                                    self.cue_group_dns = True
                                    user_groups["CUE_GROUP"] = self.cue_group_dns
                                    continue
                                    
                                elif "PurchaseRequest_Access" in group_name:
                                    self.access_group_dns = True
                                    user_groups["ACCESS_GROUP"] = self.access_group_dns
                                    continue
                                
            self.set_groups(user_groups)
            return user_groups

        except Exception as e:
            logger.error(f"ERROR: {e}")
            return {"ACCESS_GROUP": False, "CUE_GROUP": False, "IT_GROUP": False}
    
    #####################################################################################
    # LEGITIMATE USER CHECK
    def check_legitimate_user(self, connection, username):
        if connection is None:
            logger.error("Cannot check legitimate user: LDAP connection is None")
            return False
            
        try:
            connection.search(
                search_base='DC=ADU,DC=DCN',
                search_filter=f'(sAMAccountName={username})',
                search_scope=SUBTREE
            )
            if connection.entries:
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"Error checking legitimate user: {e}")
            return False
    
    #####################################################################################
    # CHECK FOR LDAP CONNECTION
    def check_ldap_connection(self, username):
        if self.connection is None:
            logger.error("Cannot check LDAP connection: LDAP connection is None")
            return False
        
        try:
            # Extract username string if User obj passed
            username_str = username.username if hasattr(username, 'username') else str(username)
            
            # Escape special characters in the username
            escaped_username = username_str.replace('*', '\\*').replace('(', '\\(').replace(')', '\\)')
            self.connection.search(
                search_base='DC=ADU,DC=DCN',
                search_filter=f'(sAMAccountName={escaped_username})',
                search_scope=SUBTREE
            )
            if self.connection.entries:
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"Error checking LDAP connection: {e}")
            return False
    #########################################################################
    # EMAIL ADDRESS LOOKUP
    #########################################################################
    def get_email_address(self, connection: Connection, username: str):
        logger.info(f"Retrieving email address for {username}")
        
        # Check if legitimate user
        if not self.check_legitimate_user(connection, username):
            logger.error(f"User {username} is not a legitimate user")
            return None
            
        try:
            connection.search(
                search_base='DC=ADU,DC=DCN',
                search_filter=f'(sAMAccountName={username})',
                search_scope=SUBTREE,
                attributes=['mail']
            )
            
            if connection.entries:
                email_address = connection.entries[0].mail.value
                return email_address
            else:
                logger.error(f"User {username} not found in LDAP.")
                return None
        except Exception as e:
            logger.error(f"Error retrieving email address: {e}")
            return None
        
    #########################################################################
    # USERNAME LOOKUP
    #########################################################################
    def fetch_usernames(self, query: str) -> List[str]:
        # LDAP structure to search for
        # OU=LAWB,OU=USCOURTS,DC=ADU,DC=DCN
        if self.connection is None:
            logger.error("Cannot get username: LDAP connection is None")
            return []
        
        # Perform subtree search
        try:
            self.connection.search(
                search_base='OU=LAWB,OU=USCOURTS,DC=ADU,DC=DCN',
                search_filter=f'(sAMAccountName={query}*)',
                search_scope=SUBTREE,
                attributes=['sAMAccountName'],
                size_limit=10  # Limit to 10 results
            )
            
            if self.connection.entries:
                logger.info(f"Found {len(self.connection.entries)} entries for query: {query}")
                logger.info(f"Raw entries: {self.connection.entries}")
                logger.info(f"Entry attributes: {[entry.entry_attributes for entry in self.connection.entries]}")
                logger.info(f"Entry JSON: {[entry.entry_to_json() for entry in self.connection.entries]}")
                return [entry.sAMAccountName.value for entry in self.connection.entries]
            else:
                logger.error(f"No user found for query: {query}")
                return ["Error"]
        except Exception as e:
            logger.error(f"Error getting username: {e}")
            return ["Error"]
            
            
    #####################################################################################
    # SETTERS
    
    def set_is_authenticated(self, value):
        self.is_authenticated = value
        
    def set_username(self, username):
        self.username = username
    
    def set_requester(self, requester):
        self.requester = requester
    
    def set_connection(self, connection):
        self.connection = connection
        
    def set_groups(self, groups: dict[str, bool]):
        self.groups = groups
        
    
    
    #####################################################################################
    # GETTERS
    
    def get_requester(self):
        return self.requester
    
    def get_username(self):
        return self.username
    
    def get_groups(self):
        return self.groups
        
    def get_connection(self):
        return self.connection
    
    def get_is_authenticated(self):
        return self.is_authenticated
