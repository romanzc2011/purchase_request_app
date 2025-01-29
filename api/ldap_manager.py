from ldap3 import Server, Connection, Tls
from dataclasses import dataclass, field
import ssl
"""
AUTHOR: ROMAN CAMPBELL
DATA: 01/29/2029
LDAP manager class to manage ldap3 and querying the AD for authentication
"""
@dataclass
class LDAPManager:
    server_name: str
    port: int
    using_tls: bool
    user: str
    password: str
    connection: Connection = field(init=False) # Exclusion from __init__
    
    
    #####################################################################################
    ## POST INIT function
    def __post_init__(self):
        self.connection = self.get_connection()
    
    #####################################################################################
    ## GET CONNECTION of ldaps
    def get_connection(self):
        tls = None
        if(self.using_tls):
            tls = self.tls_config()
            
        server = Server(self.server_name, port=self.port, use_ssl=self.using_tls, tls=tls)
        conn = Connection(server,user=self.user, password=self.password, auto_bind=True)
        return conn
    
    #####################################################################################
    ## TLS CONFIG
    def tls_config(self):
        tls_configure = Tls(validate=ssl.CERT_REQUIRED, version=ssl.PROTOCOL_TLSv1_2)
        return tls_configure
    
    
    