import sys
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # -- Application URL
    app_base_url: str = Field(
        default="http://127.0.0.1:5004",  # Default for development
        env="VITE_API_URL",
    )
    link_to_request: str = f"{app_base_url}/approval"
    
    # -- Project directories
    def _get_base_dir(self):
        if getattr(sys, 'frozen', False):
            # Running from PyInstaller executable
            return Path(sys.executable).parent
        else:
            # Running from source - check if we're in the api directory
            current_dir = Path(__file__).resolve().parent
            if current_dir.name == 'api':
                # We're in the api directory, so db is in current directory
                return current_dir
            else:
                # We're in the project root, so db is in api subdirectory
                return current_dir / "api"
    
    BASE_DIR: Path = _get_base_dir(None)
    DATABASE_FILE_PATH: Path = BASE_DIR / "db" / "pras.db"
    SQL_SCRIPT_PATH: Path = BASE_DIR / "db" /"pras_sql_script.sql"
    PDF_OUTPUT_FOLDER: Path = BASE_DIR / "pdf_output"
    UPLOAD_FOLDER: Path = BASE_DIR / "uploads"
    SEAL_IMAGE_FOLDER: Path = BASE_DIR / "img_assets" / "seal_no_border.png"

    # -- LDAP configuration
    ldap_server: str
    ldap_port: int
    ldap_use_tls: bool
    ldap_service_user: str
    ldap_service_password: str
    search_base: str
    it_group_dns: str
    cue_group_dns: str
    access_group_dns: str

    # -- Frontend API URL
    vite_api_url: str

    # -- JWT
    jwt_secret_key: str

    # -- Application settings
    approvals_link: str
    
    # -- Email settings
    smtp_server: str
    smtp_port: int
    smtp_email_addr: str
    smtp_tls: bool = False
    
    
    def model_post_init(self, __context):
        # Ensure required directories exist
        self.PDF_OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True, mode=0o750)
        self.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True, mode=0o750)

    model_config = SettingsConfigDict(
        env_file           = ".env",
        env_file_encoding  = "utf-8",
        extra              = "ignore",
    )

# Instantiate for import elsewhere
settings = Settings()