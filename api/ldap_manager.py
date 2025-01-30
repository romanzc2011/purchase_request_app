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
    ## POST INIT function
    def __post_init__(self):
        try:
            self.connection = self.get_connection()
        
        except LDAPExceptionError as e:
            print("❌ LDAP Server Returned an Error:", str(e))
            # Raised when the server returns an explicit error (e.g., invalid credentials, insufficient permissions)

        except Exception as e:
            print("❌ Unexpected Error:", str(e))
            # Catches non-LDAP exceptions
    
    #####################################################################################
    ## GET CONNECTION of ldaps
    def get_connection(self, username, password):
        tls = None
        if(self.using_tls):
            tls = self.tls_config()
            
        server = Server(self.server_name, get_info=ALL)
        conn = Connection(server,user=username, password=password, authentication="NTLM")
        
        # Print Loading # until connection successful
        print("\n#####################################")
        print("\nAttempting to authenticate to LDAP...", end="", flush=True)
        if conn.bind():
            return jsonify({"message": "Logged in successfully"})
        
        self.i_am = conn.extend.standard.who_am_i()
        
        print(f"\n✅ --- Successfully authenticated to {self.server_name}")
        print(f"# ---- Authenticated as: {self.i_am}")
        print("\n#####################################")
        return conn

    #####################################################################################
    ## TLS CONFIG
    def tls_config(self):
        tls_configure = Tls(validate=ssl.CERT_REQUIRED, version=ssl.PROTOCOL_TLSv1_2)
        return tls_configure
    
    
    
    
    