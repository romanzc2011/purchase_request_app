from abc import ABC, abstractmethod
from email.message import EmailMessage
from typing import List
from win32com.client import Dispatch
import pythoncom
import asyncio
from loguru import logger
from pathlib import Path
import win32com.client

class EmailTransport(ABC):
    @abstractmethod
    async def send(self, msg: EmailMessage) -> None:
        pass

class OutlookTransport(EmailTransport):
    def __init__(self):
        self.outlook = None

    def _initialize_outlook(self):
        """Initialize COM and Outlook application"""
        try:
            # Initialize COM for this thread
            pythoncom.CoInitialize()
            
            # Create Outlook application
            self.outlook = Dispatch("Outlook.Application")
            return True
        except Exception as e:
            logger.error(f"Error initializing Outlook: {e}")
            return False

    def _cleanup_outlook(self):
        """Clean up COM and Outlook resources"""
        try:
            if self.outlook:
                self.outlook.Quit()
            pythoncom.CoUninitialize()
        except Exception as e:
            logger.error(f"Error cleaning up Outlook: {e}")

    async def send(self, msg: EmailMessage) -> None:
        """Send email using Outlook automation"""
        try:
            # Run the COM operations in a thread pool
            await asyncio.to_thread(self._send_sync, msg)
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            raise

    def _send_sync(self, msg: EmailMessage):
        """Synchronous method to send email using Outlook"""
        try:
            logger.info(">>>> ENTERING OUTLOOK TRANSPORT")
            self._initialize_outlook()

            mail = self.outlook.CreateItem(0)
            mail.Subject = msg.subject
            if msg.html_body:
                mail.HTMLBody = msg.html_body
            for addr in msg.to:
                r = mail.Recipients.Add(addr)
                r.Type = 1
            
            for addr in msg.cc or []:
                r = mail.Recipients.Add(addr)
                r.Type = 2
            
            if msg.attachments:
                for attachment in msg.attachments:
                    try:
                        # Convert to absolute path and verify it exists
                        attachment_path = Path(attachment).resolve()
                        if not attachment_path.exists():
                            logger.error(f"Attachment file not found: {attachment_path}")
                            continue
                            
                        logger.info(f"Adding attachment: {attachment_path}")
                        mail.Attachments.Add(str(attachment_path))
                    except Exception as e:
                        logger.error(f"Error adding attachment {attachment}: {e}")
                        continue
            
            mail.Recipients.ResolveAll()
            mail.Send()
            logger.info(f"Email sent successfully to {msg.to}")
        except Exception as e:
            logger.error(f"Error in Outlook automation: {e}")
            raise
        finally:
            self._cleanup_outlook()