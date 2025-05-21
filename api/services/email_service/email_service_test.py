import pythoncom
from win32com.client import Dispatch, constants
import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from typing import List, Optional
from loguru import logger
from dataclasses import dataclass
from services.db_service import ITDeptMembers
from services.db_service import RequestApprovers
from services.db_service import FinanceDeptMembers
from pydantic_schemas import GroupCommentPayload, ItemStatus

"""
AUTHOR: Roman Campbell
DATE: 01/07/2025
Used to send purchase request notifications.
"""

@dataclass
class EmailMessage:
    subject: str
    to: List[str]
    cc: Optional[List[str]] = None
    html_body: Optional[str] = None
    text_body: Optional[str] = None
    attachments: List[str] = None
    
class TemplateRenderer:
    def __init__(self, template_dir: str):
        self.env = Environment(loader=FileSystemLoader(template_dir))
        
    def render(self, template_name: str, context: dict) -> str:
        template = self.env.get_template(template_name)
        return template.render(**context)

class EmailService:
    """
    A class to manage email notification operations for purchase request workflows
    """
    # TODO: Add a method to send an email to a single recipient, approvers, finance etc
    def __init__(self, from_sender, subject, cc_persons=None):
        self.outlook = Dispatch("Outlook.Application")
        self.from_sender = from_sender
        self.subject = subject
        self.cc_persons = cc_persons or []
        self.recipients = {
            'requester': {'name': None, 'email': None},
            'first_approver': { 'name': None, 'email': None },
            'final_approver': { 'name': None, 'email': None }
        }
        # Get the project root directory (where the api folder is located)
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Create rendered_templates directory if it doesn't exist
        self.rendered_dir = os.path.join(self.project_root, "rendered_templates")
        os.makedirs(self.rendered_dir, exist_ok=True)
       
        self.request_status = None
        
    def get_routing_group(self):
        if group == "IT":
            return ITDeptMembers
        elif group == "FINANCE":
            return FinanceDeptMembers
        else:
            raise ValueError(f"Invalid routing group: {group}")
        
    def  build_comment_email(self, payload: GroupCommentPayload):
        """
        Build an email to the requester with the comment
        """
        template_dir = os.path.join(self.project_root, "templates")
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template("comment_template.html")
        
        # Prepare the data for the template
        items = list(zip(payload.item_desc, payload.comment))
        context = {
            "groupKey": payload.groupKey,
            "items": items,
            "requestor_name": self.recipients['requester']['name']
        }
        
        # Render the template
        html = template.render(**context)
        return html
    
    # Send an email to the requester with the comment
    def send_comment_email(self, payload: GroupCommentPayload):
        """
        Send an email to the requester with the comment
        """
        
        html = self.build_comment_email(payload)
        self._send_email(outlook=None, to_email=self.recipients['requester']['email'], subject=f"Comments on {payload.groupKey}", body=html)

    def send_notification(self, template_path=None, template_data=None, subject=None, request_status=None, custom_msg=None):
        """
        Send notifications based on request status or directly to a recipient
        """
        try:
            pythoncom.CoInitialize()
            outlook = win32.Dispatch("Outlook.Application")
            
            # Set request status if provided
            if request_status:
                self.request_status = request_status
            
            # Validate required fields
            self._validate_required_fields()
            
            # If custom message is provided, send it directly
            if custom_msg:
                self._send_email(
                    outlook=outlook,
                    to_email=self.recipients['requester']['email'],
                    subject=subject or self.subject,
                    body=custom_msg
                )
                logger.info("Email notifications sent successfully.")
                return
            
            # Otherwise use status-based approach
            if self.request_status == 'NEW REQUEST':
                self._send_email(
                    outlook=outlook,
                    to_email=self.recipients['first_approver']['email'],
                    subject=self.msg_templates['NEW_REQUEST']['first_approver']['subject'],
                    body=self.msg_templates['NEW_REQUEST']['first_approver']['body'].format(
                        first_approver=self.recipients['first_approver']['name']
                    ),
                    template_data=template_data,
                    cc=self.cc_persons,
                )
                self._send_email(
                    outlook=outlook,
                    to_email=self.recipients['requester']['email'],
                    subject=self.msg_templates['NEW_REQUEST']['requester']['subject'],
                    body=self.msg_templates['NEW_REQUEST']['requester']['body'].format(
                        requester=self.recipients['requester']['name']
                    ),
                    template_data=template_data,
                    cc=self.cc_persons,
                )
            elif self.request_status == 'PENDING':
                self._send_email(
                    outlook=outlook,
                    to_email=self.recipients['final_approver']['email'],
                    subject=self.msg_templates['PENDING']['final_approver']['subject'],
                    body=self.msg_templates['PENDING']['final_approver']['body'].format(
                        final_approver=self.recipients['final_approver']['name']
                    ),
                    template_data=template_data,
                    cc=self.cc_persons,
                )
            else:
                logger.error(f"Unknown request status: {self.request_status}")
                return
            logger.info("Email notifications sent successfully.")
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            raise
        finally:
            pythoncom.CoUninitialize()
            
    
    # Send email
    def _send_email(self, outlook, to_email, subject, body=None, cc=None, template_path=None, template_data=None):
        """
        Helper method to send an email using Outlook
        """
        try:  
            pythoncom.CoInitialize()
            
            mail = self.outlook.CreateItem(0)  # 0 is the constant for olMailItem
            mail.Subject = subject
            
            # Create a simple HTML template for the body
            if body:
                mail.HTMLBody = body
                
            recipient = mail.Recipients.Add(to_email)
            recipient.Type = 1  # 1 is the constant for olTo
            mail.Recipients.ResolveAll()
            
            # Add CC recipients
            if cc:
                for email in cc:
                    cc_recipient = mail.Recipients.Add(email)
                    cc_recipient.Type = 2  # 2 is the constant for olCC
                mail.Recipients.ResolveAll()
                
            mail.Send()
            logger.info(f"Email sent to {to_email} with subject: {subject}")
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            raise
        
    def _validate_required_fields(self):
        """
        Validate that all required fields are set based on the current request status
        """
        # Always check subject
        if not self.subject:
            raise ValueError("Email subject is not set")
            
        # Check fields based on request status
        if self.request_status == 'NEW REQUEST':
            if not self.recipients['requester']['email']:
                raise ValueError("Requester email is not set")
            if not self.recipients['first_approver']['email']:
                raise ValueError("First approver email is not set")
        elif self.request_status == 'PENDING':
            if not self.recipients['final_approver']['email']:
                raise ValueError("Final approver email is not set")
        else:
            # For custom notifications, check if recipient is set
            if not hasattr(self, 'recipients') or not any(self.recipients.values()):
                raise ValueError("No recipient email is set")

   #################################################################################
    ## SETTER METHODS
    def set_requester(self, name: str, email: str):
        self.recipients['requester'] = {'name': name, 'email': email}

    def set_first_approver(self, name: str, email: str):
        self.recipients['first_approver'] = {'name': name, 'email': email}

    def set_final_approver(self, name: str, email: str):
        self.recipients['final_approver'] = {'name': name, 'email': email}      

    def set_cc_persons(self, cc_persons: list):
        self.cc_persons = cc_persons
        
    def set_request_status(self, request_status: str):
        self.request_status = request_status
        
    def set_template_path(self, template_path: str):
        self.template_path = template_path
        
    def set_rendered_dir(self, rendered_dir: str):
        self.rendered_dir = rendered_dir
        
    def set_rendered_docx_path(self, rendered_docx_path: str):
        self.rendered_docx_path = rendered_docx_path
    
    #################################################################################
    ## GETTER METHODS

    # Getter methods
    def get_requester(self):
        return self.recipients['requester']

    def get_first_approver(self):
        return self.recipients['first_approver']

    def get_final_approver(self):
        return self.recipients['final_approver']

    def get_cc_persons(self):
        return self.cc_persons
    
    def get_request_status(self):
        return self.request_status
    
    def get_template_path(self):
        return self.template_path
    
    def get_rendered_dir(self):
        return self.rendered_dir
    
    def get_rendered_docx_path(self):
        return self.rendered_docx_path
