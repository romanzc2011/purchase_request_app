import os 
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Base paths
    BASE_DIR: Path = Path(__file__).resolve().parent
    PDF_OUTPUT_FOLDER: Path = BASE_DIR / "api" / "pdf_output"
    
    # LDAP settings
    ldap_server: str
    ldap_port: str
    ldap_use_tls: str
    ldap_service_user: str
    ldap_service_password: str
    search_base: str
    it_group_dns: str
    cue_group_dns: str
    access_group_dns: str
    
    # JWT settings
    jwt_secret_key: str
    
    # Application settings
    approvals_link: str
    upload_folder: str
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
settings = Settings()

