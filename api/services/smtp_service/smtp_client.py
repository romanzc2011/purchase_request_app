import aiosmtplib
from api.settings import settings
from loguru import logger
from typing import Optional

class AsyncSMTPClient:
    def __init__(
        self,
        hostname: str,
        port: int,
    ):
        self.hostname = hostname
        self.port = port
        self._client: Optional[aiosmtplib.SMTP] = None
        
    async def __aenter__(self) -> aiosmtplib.SMTP:
        self._client = aiosmtplib.SMTP(
            hostname=self.hostname,
            port=self.port,
            use_tls=settings.smtp_tls,
            timeout=10
        )
        await self._client.connect()
        return self._client
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        if self._client is not None:
            await self._client.quit()
            