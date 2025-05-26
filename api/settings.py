from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, Field

class Settings(BaseSettings):
    # -- Application URL
    app_base_url: str = Field(
        default="http://localhost:3000",  # Default for development
        env="VITE_API_URL",
    )
    
    # -- Project directories
    BASE_DIR: Path = Path(__file__).resolve().parent
    PDF_OUTPUT_FOLDER: Path = BASE_DIR / "api" / "pdf_output"

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

    model_config = SettingsConfigDict(
        env_file           = ".env",
        env_file_encoding  = "utf-8",
        extra              = "ignore",
    )

# Instantiate for import elsewhere
settings = Settings()