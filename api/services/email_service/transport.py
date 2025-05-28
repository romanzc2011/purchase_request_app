from abc import ABC, abstractmethod
from email.message import EmailMessage
from typing import List
from win32com.client import Dispatch
import pythoncom

class EmailTransport(ABC):
    @abstractmethod
    def send(self, msg: EmailMessage) -> None:
        pass
    
class OutlookTransport(EmailTransport):
    def __init__(self):
        pythoncom.CoInitialize()
        self.outlook = Dispatch("Outlook.Application")
        
    def send(self, msg: EmailMessage, attachments: List[str] = None):
        mail = self.outlook.CreateItem(0)
        mail.Subject = msg.subject
        if msg.html_body:
            mail.HTMLBody = msg.html_body
        for addr in msg.to:
            r = mail.Recipients.Add(addr); r.Type = 1
        
        for addr in msg.cc or []:
            r = mail.Recipients.Add(addr); r.Type = 2
        
        if attachments:
            for attachment in attachments:
                mail.Attachments.Add(attachment)
        
        mail.Recipients.ResolveAll()
        mail.Send()
