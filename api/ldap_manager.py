from flask import jsonify
from ldap3 import Server, Connection, Tls, ALL
from ldap3.core.exceptions import LDAPExceptionError, LDAPBindError
from requests_ntlm import HttpNtlmAuth
from dataclasses import dataclass, field
import ssl
"""
AUTHOR: ROMAN CAMPBELL
DATA: 01/29/2025
LDAP manager class to manage ldap3 and querying the AD for authentication
"""
@dataclass
class LDAPManager:
    server_name: str
    port: int
    using_tls: bool
    
    #####################################################################################
    ## GET CONNECTION of ldaps
    def get_connection(self, username, password):
        tls = None
        if(self.using_tls):
            tls = self.tls_config()
            
        server = Server(self.server_name, get_info=ALL)
        
        try:
            conn = Connection(server,user=username, password=password, authentication="NTLM")
            return conn
        except LDAPExceptionError as e:
            print("❌ LDAP Server Returned an Error:", str(e))
            # Raised when the server returns an explicit error (e.g., invalid credentials, insufficient permissions)

        except Exception as e:
            print("❌ Unexpected Error:", str(e))

    #####################################################################################
    ## TLS CONFIG
    def tls_config(self):
        tls_configure = Tls(validate=ssl.CERT_REQUIRED, version=ssl.PROTOCOL_TLSv1_2)
        return tls_configure
    
    def print_login_banner(self, username):
        # Print Loading # until connection successful
        print("\n#####################################")
        print(f"\n✅ --- Successfully authenticated to {self.server_name}")
        print(f"\n# ---- Authenticated as: {username}")
        print("\n#####################################")
    
    
    
    
    