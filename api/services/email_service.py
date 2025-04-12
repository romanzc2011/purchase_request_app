import pythoncom
import win32com.client as win32
import os

from loguru import logger
from services.ipc_service import IPC_Service

"""
AUTHOR: Roman Campbell
DATE: 01/07/2025
Used to send purchase request notifications.
Method of execution, you have NEW REQUESTS, PENDING REQUESTS, and APPROVED REQUESTS.
For NEW REQUESTS, you will send an email to the first approver and the requester.
For PENDING REQUESTS, you will send an email to the final approver. This means that we wont send an email
to final approver until the status is set to PENDING. Will need to grab the status from the database using
request ID.
"""
class EmailService:
    """
    A class to manage email notification operations for purchase request workflows
    """
    def __init__(self, from_sender, subject, cc_persons=None):
        self.from_sender = from_sender
        self.subject = subject
        self.cc_persons = cc_persons or []
        self.recipients = {
            'requester': {'name': None, 'email': None},
            'first_approver': { 'name': None, 'email': None },
            'final_approver': { 'name': None, 'email': None }
        }
        self.msg_templates = {
            'NEW_REQUEST': {
                'first_approver': {
                    'subject': 'Purchase Request Notification - First Approver',
                    'body': '<p>Dear {first_approver},</p><p>You have a new purchase request to review.</p>'
                },
                'requester': {
                    'subject': 'Purchase Request Notification - Requester', 
                    'body': '<p>Dear {requester},</p><p>Your purchase request has been submitted.</p>'
                }
            },
            'PENDING': {
                'final_approver': {
                    'subject': 'Purchase Request Notification - Final Approver',
                    'body': '<p>Dear {final_approver},</p><p>You have a new purchase request to review.</p>'
                }
            }
        }
        self.request_status = None

    def send_notification(self, template_data=None, subject=None, request_status=None, custom_msg=None):
        """
        Send notifications based on request status or directly to a recipient
        
        Args:
            recipients: Email address(es) of the recipient(s)
            template_path: Path to the HTML template file (optional)
            template_data: Data to be used in the template (optional)
            subject: Email subject (optional)
            request_status: Status of the request (optional)
            custom_msg: Custom message to send (optional)
        """
        try:
            pythoncom.CoInitialize()
            outlook = win32.Dispatch("Outlook.Application")
            
            # Validate required fields
            self._validate_required_fields()
            
            # Otherwise use status-based approach
            if request_status == 'NEW REQUEST':
                self._send_email(
                    outlook=outlook,
                    to_email=self.recipients['first_approver']['email'],
                    subject=self.msg_templates['NEW_REQUEST']['first_approver']['subject'],
                    body=self.msg_templates['NEW_REQUEST']['first_approver']['body'].format(
                        first_approver=self.recipients['first_approver']['name']
                    ),
                    template_path='./templates/new_request_notification.html',
                    template_data=template_data,
                    cc=self.cc_persons
                )
                self._send_email(
                    outlook=outlook,
                    to_email=self.recipients['requester']['email'],
                    subject=self.msg_templates['NEW_REQUEST']['requester']['subject'],
                    body=self.msg_templates['NEW_REQUEST']['requester']['body'].format(
                        requester=self.recipients['requester']['name']
                    ),
                    template_path='./templates/requester_template.html',
                    template_data=template_data,
                    cc=self.cc_persons
                )
            elif request_status == 'PENDING':
                self._send_email(
                    outlook=outlook,
                    to_email=self.recipients['final_approver']['email'],
                    subject=self.msg_templates['PENDING']['final_approver']['subject'],
                    body=self.msg_templates['PENDING']['final_approver']['body'].format(
                        final_approver=self.recipients['final_approver']['name']
                    ),
                    template_path='./templates/final_approver_template.html',
                    template_data=template_data,
                    cc=self.cc_persons
                )
            else:
                logger.error(f"Unknown request status: {request_status}")
                return
            logger.info("Email notifications sent successfully.")
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            raise
        finally:
            pythoncom.CoUninitialize()
            
    
    # Send email
    def _send_email(self, outlook, to_email, subject, body, cc=None, template_path=None, template_data=None):
        """
        Helper method to send an email using Outlook
        
        Args:
            outlook: Outlook application instance
            to_email: Recipient email address(es)
            subject: Email subject
            body: Email body content
            cc: CC recipients (optional)
            template_path: Path to HTML template file (optional)
            template_data: Data to be used in template (optional)
        """
        mail = outlook.CreateItem(0)
        mail.Subject = subject
        
        # Handle template if provided
        if template_path and template_data:
            try:
                with open(template_path, 'r') as f:
                    template = f.read()
                
                # Check which variables are actually in the template
                missing_vars = []
                for key in template_data.keys():
                    if f"{{{key}}}" not in template:
                        missing_vars.append(key)
                
                if missing_vars:
                    logger.warning(f"Template variables not found in template: {missing_vars}")
                
                # Special case: Replace {requester} with the requester's name if it exists in the template
                if "{requester}" in template and self.recipients['requester']['name']:
                    template = template.replace("{requester}", self.recipients['requester']['name'])
                    logger.info(f"Replaced {{requester}} with {self.recipients['requester']['name']}")
                
                # Replace template variables with data
                for key, value in template_data.items():
                    # Replace {key} with value
                    template = template.replace("{" + key + "}", str(value))
                mail.HTMLBody = template
            except Exception as e:
                logger.error(f"Error processing template: {e}")
                mail.HTMLBody = body
        else:
            mail.HTMLBody = body
        
        # Handle multiple recipients
        if isinstance(to_email, list):
            mail.To = "; ".join(to_email)
        else:
            mail.To = to_email
        
        # Handle CC recipients
        if cc:
            mail.CC = "; ".join(cc)
        elif self.cc_persons:
            mail.CC = "; ".join(self.cc_persons)
        
        mail.Send()
        logger.info(f"Email sent to {to_email} with subject: {subject}")
        
    def _validate_required_fields(self):
        """Validate that all required fields are set"""
        if not self.recipients['requester']['email']:
            raise ValueError("Requester email is not set")
        if not self.recipients['first_approver']:
            raise ValueError("First approver email is not set")
        if not self.recipients['final_approver']:
            raise ValueError("Final approver email is not set")
        if not self.subject:
            raise ValueError("Email subject is not set")

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
