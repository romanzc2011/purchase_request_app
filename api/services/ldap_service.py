from dotenv import load_dotenv
from ldap3 import Server, Connection, Tls, ALL, SUBTREE
from ldap3.core.exceptions import LDAPExceptionError
from loguru import logger
from requests_ntlm import HttpNtlmAuth
from typing import Optional, List
import ssl
import os
import re
from api.schemas.pydantic_schemas import LDAPUser
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
    def build_user_object(username: str, groups: dict[str,bool], email: Optional[str]) -> LDAPUser:
        group_names = [k for k,v in groups.items() if v]
        return LDAPUser(username, email or "unknown", group_names)
    
    #####################################################################################
    # GET CONNECTION of ldap service
    def create_connection(self, username, password):
        tls = None
        if self.using_tls:
            tls = self.tls_config()
        logger.info("""
            #####################################################################
            Creating Connection()
            #####################################################################""")
        
        # Remove ldaps:// prefix if present
        server_name = self.server_name.replace('ldaps://', '').replace('ldap://', '')
        logger.info(f"Cleaned server name: {server_name}")
        
        server = Server(server_name, port=self.port, use_ssl=self.using_tls, tls=tls, get_info=ALL)
        logger.info(f"SERVER: {server}")
        try:
            logger.info(f"Attempting connection to {server_name}:{self.port} with SSL={self.using_tls}")
            # Try with domain prefix if username doesn't have it
            if not '\\' in username and not '@' in username:
                user = f"ADU\\{username}"
            else:
                user = username
            logger.info(f"Using user format: {user}")
            
            connection = Connection(server, user=user, password=password, auto_bind=True)
            
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
                logger.error(f"Connection status: {connection.result}")
                self.set_is_authenticated(False)
                self.set_connection(None)
                return None
        
        except LDAPExceptionError as e:
            logger.error("❌ LDAP Server Returned an Error:")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            logger.error(f"Server details: {self.server_name}:{self.port}")
            logger.error(f"Using SSL: {self.using_tls}")
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
                logger.info(f"Checking group: {group}")
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
                    logger.info(f"Extracted group name: {group_name}")
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

    #########################################################################
    # EMAIL ADDRESS LOOKUP
    #########################################################################
    def get_email_address(self, connection: Connection, username: str):
        logger.info(f"Retrieving email address for {username}")
        
        # Check if legitimate user
        if not self.check_legitimate_user(connection, username):
            logger.error(f"LDAPUser {username} is not a legitimate user")
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
                logger.error(f"LDAPUser {username} not found in LDAP.")
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
    # FETCH USER
    #####################################################################################
    def fetch_user(self, username: str) -> LDAPUser:
        connection = self.get_connection()
        if connection is None:
            logger.info(f"Creating new LDAP connection for user {username}")
            connection = self.create_connection(self.service_user, self.service_password)
            if connection is None:
                logger.warning(f"Failed to create LDAP connection for user {username}, using default user object")
                return LDAPUser(username=username, email="unknown@unknown.com", groups=[])
        
        groups = self.check_user_membership(connection, username)
        email = self.get_email_address(connection, username)
        return LDAPUser(username=username, email=email, groups=list(groups.keys()))
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

    def get_approver_emails(self) -> List[str]:
        """
        Get email addresses of users in the CUE group who are approvers.
        Returns a list of email addresses.
        
        """
        test_email = "roman_campbell@lawb.uscourts.gov"
        logger.info(f"TESTING: Returning test email: {test_email}")
        return [test_email]
        # try:
        #     connection = self.get_connection()
        #     if not connection:
        #         logger.error("Failed to establish LDAP connection")
        #         return []

        #     # Search for users in the CUE group
        #     cue_group_dn = "CN=LAWB_PurchaseRequest_CUE,OU=Groups,OU=LAWB,OU=USCOURTS,DC=ADU,DC=DCN"
        #     search_filter = f"(&(objectClass=user)(memberOf={cue_group_dn}))"
        #     search_base = 'DC=ADU,DC=DCN'
            
        #     logger.info(f"Searching for approvers with filter: {search_filter}")
            
        #     # Search for users
        #     connection.search(
        #         search_base=search_base,
        #         search_filter=search_filter,
        #         attributes=['mail', 'sAMAccountName']
        #     )
            
        #     # Extract email addresses
        #     approver_emails = []
        #     for entry in connection.entries:
        #         if hasattr(entry, 'mail') and entry.mail.value:
        #             logger.info(f"Found approver: {entry.sAMAccountName.value} - {entry.mail.value}")
        #             approver_emails.append(entry.mail.value)
            
        #     logger.info(f"Found {len(approver_emails)} approver emails: {approver_emails}")
        #     return approver_emails
            
        # except Exception as e:
        #     logger.error(f"Error getting approver emails: {e}")
        #     return []
        # finally:
        #     if connection:
        #         connection.unbind()
