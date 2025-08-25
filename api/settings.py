from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # -- Application URL
    app_base_url: str = Field(
        default="http://localhost:5004",  # Default for development
        env="VITE_API_URL",
    )
    link_to_request: str = f"{app_base_url}/approval"
    
    # -- Project directories
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATABASE_FILE_PATH: Path = BASE_DIR / "api" / "db" / "pras.db"
    SQL_SCRIPT_PATH: Path = BASE_DIR / "api" / "db" / "pras_sql_script.sql"
    PDF_OUTPUT_FOLDER: Path = BASE_DIR / "api" / "pdf_output"
    UPLOAD_FOLDER: Path = BASE_DIR / "api" / "uploads"
    TLS_CERT_DIR: Path = BASE_DIR / "api" / "tls_certs"

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
    jwt_secret_key: str = Field(env="JWT_SECRET_KEY")

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