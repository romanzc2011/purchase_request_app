from abc import ABC, abstractmethod
from email.message import EmailMessage
from typing import List
from win32com.client import Dispatch
import pythoncom
import asyncio
from loguru import logger
from pathlib import Path

class EmailTransport(ABC):
    @abstractmethod
    async def send(self, msg: EmailMessage) -> None:
        pass
    
class OutlookTransport(EmailTransport):
    def __init__(self):
        self._outlook = None
        
    def _get_outlook(self):
        if self._outlook is None:
            pythoncom.CoInitialize()
            self._outlook = Dispatch("Outlook.Application")
        return self._outlook
        
    async def send(self, msg: EmailMessage, attachments: List[str] = None):
        try:
            # Run the Outlook operations in a thread pool
            await asyncio.to_thread(self._send_sync, msg, attachments)
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            raise
            
    def _send_sync(self, msg: EmailMessage, attachments: List[str] = None):
        try:
            outlook = self._get_outlook()
            mail = outlook.CreateItem(0)
            mail.Subject = msg.subject
            if msg.html_body:
                mail.HTMLBody = msg.html_body
            for addr in msg.to:
                r = mail.Recipients.Add(addr)
                r.Type = 1
            
            for addr in msg.cc or []:
                r = mail.Recipients.Add(addr)
                r.Type = 2
            
            if attachments:
                for attachment in attachments:
                    # Convert to absolute path and verify it exists
                    attachment_path = Path(attachment).resolve()
                    if not attachment_path.exists():
                        raise FileNotFoundError(f"Attachment file not found: {attachment_path}")
                    logger.info(f"Adding attachment: {attachment_path}")
                    mail.Attachments.Add(str(attachment_path))
            
            mail.Recipients.ResolveAll()
            mail.Send()
        except Exception as e:
            logger.error(f"Error in Outlook automation: {e}")
            raise
