# Dependencies for PRAS
import os

from api.settings                           import settings
from api.services.cache_service             import CacheService
from api.services.smtp_service.renderer     import TemplateRenderer
from api.services.smtp_service.smtp_service import SMTP_Service
from api.services.ldap_service              import LDAPService
from api.services.auth_service              import AuthService
from api.services.pdf_service               import PDFService
from api.services.uuid_service              import UUIDService
from api.services.search_service            import SearchService
from api.services.progress_bar_service      import ProgressBar
from api.dependencies.pras_schemas          import *

# —————————————— Email Renderer ————————————————————
renderer = TemplateRenderer(
    template_dir=str(settings.BASE_DIR / "api"/ "services" / "smtp_service" / "templates")
)

# —————————————— LDAP Service ————————————————————
ldap_service = LDAPService(
    ldap_url       = settings.ldap_server,           # e.g. "ldaps://adu.dcn"
    bind_dn        = settings.ldap_service_user,     # e.g. "ADU\\svc_account"
    bind_password  = settings.ldap_service_password, # service account password
    group_dns      = [
        settings.it_group_dns,
        settings.cue_group_dns,
        settings.access_group_dns,
    ],
)

# -----------------------------------------------------
# SMTP Service
# -----------------------------------------------------
smtp_service = SMTP_Service(
    renderer     = renderer,
    ldap_service = ldap_service,
)

# -----------------------------------------------------
# PDF Service
# -----------------------------------------------------
pdf_service = PDFService()

# -----------------------------------------------------
# UUID Service
# -----------------------------------------------------
uuid_service = UUIDService()

# -----------------------------------------------------
# Search Service
# -----------------------------------------------------
search_service = SearchService()

# -----------------------------------------------------
# Auth Service
# -----------------------------------------------------
auth_service = AuthService(ldap_service=ldap_service)

# -----------------------------------------------------
# Progress Bar
# -----------------------------------------------------
progress_bar = ProgressBar()
