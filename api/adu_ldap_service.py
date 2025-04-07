
from dotenv import load_dotenv
from flask import jsonify
from ldap3 import Server, Connection, Tls, ALL, SUBTREE
from ldap3.core.exceptions import LDAPExceptionError, LDAPBindError
from loguru import logger
from requests_ntlm import HttpNtlmAuth
from dataclasses import dataclass, field
import ssl
import os
import re
"""
AUTHOR: ROMAN CAMPBELL
DATA: 01/29/2025
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
    "ACCESS_GROUP" : False,
    "CUE_GROUP" : False,
    "IT_GROUP" : False
}

@dataclass
class LDAPManager:
    server_name: str
    port: int
    using_tls: bool
    it_group_dns: bool = False
    cue_group_dns: bool = False
    access_group_dns: bool = False
    is_authenticated: bool = False
    conn: Connection = field(default=None, init=False)
    
    #####################################################################################
    ## GET CONNECTION of ldaps
    def get_connection(self, username, password):
        tls = None
        if(self.using_tls):
            tls = self.tls_config()
            
        server = Server(self.server_name, port=self.port, use_ssl=self.using_tls, tls=tls, get_info=ALL)
        
        try:
            conn = Connection(server,user=username, password=password, auto_bind=True)
            
            if conn.bound:
                print("\n#####################################################################")
                print(f"\n✅ --- Successfully authenticated to {self.server_name}")
                print(f"\n# ---- Authenticated as: {username}")
                print("\n#####################################################################")
                self.set_is_authenticated(True)
                self.set_conn(conn)
                
            return conn
        
        except LDAPExceptionError as e:
            logger.error("❌ LDAP Server Returned an Error:", str(e))
            # Raised when the server returns an explicit error (e.g., invalid credentials, insufficient permissions)

        except Exception as e:
            logger.error("❌ Unexpected Error:", str(e))

    #####################################################################################
    ## TLS CONFIG
    def tls_config(self):
        tls_configure = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1_2)
        return tls_configure
  
    #####################################################################################
    ## SEARCH FOR GROUP MEMBERSHIP
    def check_user_membership(self, conn, username):
        
        try:
            # Iterate thru the DNS Groups and determine what user is member of
            for group in group_dns:
                
                # Execute search
                conn.search(
                    search_base=group,
                    search_filter='(objectClass=group)',
                    search_scope=SUBTREE,
                    attributes=['member']
                )
                
                if conn.entries:
                    print(f"entries: {conn.entries}")
                    # Extract full DN of all members
                    group_entry = conn.entries[0]
                    members_dn_list = group_entry.member.values
                    print(group)
                    
                    print(members_dn_list)
                    
                    match = re.search(r'CN=LAWB_([^,]+)', group)
                    group_name = match.group(1) if match else "Uknown"
                    
                    
                    matched_user = None
                    for member_dn in members_dn_list:
                        # Query LDAP for each DN to get their sAMAccountName (username)
                        conn.search(
                            search_base=member_dn,
                            search_filter="(objectClass=person)",  # search for user object
                            search_scope=SUBTREE,
                            attributes=['sAMAccountName', 'mail']
                        )
                        
                        if conn.entries:
                            entry = conn.entries[0]
                            print(f"DN: {entry.entry_dn}")
                            for attribute, values in entry.entry_attributes_as_dict.items():
                                print(f"{attribute}: {values}")
                            print("-----------------------------\n")
                        
                        if conn.entries:
                            member_username = conn.entries[0].sAMAccountName.value
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
            
            return user_groups

        except Exception as e:
            logger.error(f"ERROR: {e}")

    #####################################################################################
    ## EMAIL ADDRESS LOOKUP
    def get_email_address(self, conn, username):
        try:
            conn.search(
                search_base='DC=ADU,DC=DCN',
                search_filter=f'(sAMAccountName={username})',
                search_scope=SUBTREE,
                attributes=['mail']
            )
            
            if conn.entries:
                email_address = conn.entries[0].mail.value
                return email_address
            else:
                logger.error(f"User {username} not found in LDAP.")
                return None
        except Exception as e:
            logger.error(f"Error retrieving email address: {e}")
            return None
        
    #####################################################################################
    ## GET/SET CONNECTION   
    def set_is_authenticated(self, value):
        self.is_authenticated = value
        
    def get_is_authenticated(self):
        return self.is_authenticated
    
    def set_conn(self, conn):
        self.conn = conn
        
    def get_conn(self):
        return self.conn
    
    def set_username(self, username):
        self.username = username
    
    def get_username(self):
        return self.username

    #####################################################################################
    ## EMAIL ADDRESS LOOKUP
    
            