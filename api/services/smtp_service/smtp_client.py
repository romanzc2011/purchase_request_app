import aiosmtplib
from api.settings import settings
from loguru import logger
from typing import Optional

class AsyncSMTPClient:
    def __init__(
        self,
        hostname: str,
        port: int,
        starttls: bool = False,
        ssl: bool = False,
        timeout: Optional[int] = 10,
    ):
        self.hostname = settings.smtp_server
        self.port = settings.smtp_port
        self.starttls = starttls
        self.ssl = ssl
        self.timeout = timeout
        self._client = Optional[aiosmtplib.SMTP] = None
        
    async def __aenter__(self) -> aiosmtplib.SMTP:
        self._client = aiosmtplib.SMTP(
            hostname=self.hostname,
            port=self.port,
            starttls=self.starttls,
            ssl=self.ssl,
            timeout=self.timeout,
        )
        await self._client.connect()
        return self._client
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        if self._client is not None:
            await self._client.quit()
            