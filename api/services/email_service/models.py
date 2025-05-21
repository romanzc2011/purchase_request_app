from dataclasses import dataclass
from typing import Optional, List

@dataclass
class EmailMessage:
    subject: str
    sender: str;
    to: List[str]
    cc: Optional[List[str]] = None
    html_body: Optional[str] = None
    text_body: Optional[str] = None
    attachments: List[str] = None