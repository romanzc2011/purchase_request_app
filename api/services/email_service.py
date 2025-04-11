from loguru import logger
from services.ipc_service import IPC_Service
import pythoncom
import win32com.client as win32
import os

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

    def send_notification(self, recipient, template_path=None, template_data=None, subject=None, request_status=None, custom_msg=None):
        """
        Send notifications based on request status or directly to a recipient
        
        Args:
            recipient: Email address of the recipient
            template_path: Path to the HTML template file (optional)
            template_data: Data to be used in the template (optional)
            subject: Email subject (optional)
            request_status: Status of the request (optional)
            custom_msg: Custom message to send (optional)
        """
        try:
            pythoncom.CoInitialize()
            outlook = win32.Dispatch("Outlook.Application")
            
            # If template path is provided, use it to send a direct notification
            if template_path:
                # Read the template file
                with open(template_path, 'r') as file:
                    template_content = file.read()
                
                # Format the template with the provided data
                if template_data:
                    # Replace template placeholders while preserving CSS curly braces
                    formatted_content = template_content
                    for key, value in template_data.items():
                        placeholder = "{" + key + "}"
                        formatted_content = formatted_content.replace(placeholder, str(value))
                else:
                    formatted_content = template_content
                
                # Create and send the email
                mail = outlook.CreateItem(0)
                mail.Subject = subject or self.subject
                mail.HTMLBody = formatted_content
                mail.To = recipient
                
                if self.cc_persons:
                    mail.CC = "; ".join(self.cc_persons)
                
                mail.Send()
                logger.info(f"Email sent to {recipient} using template {template_path}")
                return
            
            # Otherwise, use the request_status based notification
            if request_status:
                self._validate_required_fields()
                
                if request_status == "NEW_REQUEST":
                    self._send_new_request_notifications(outlook, custom_msg)
                elif request_status == "PENDING":
                    self._send_pending_notifications(outlook, custom_msg)
                else:
                    logger.warning(f"Unknown request status: {request_status}")
                    
                logger.info("Email notifications sent successfully")
            else:
                logger.warning("No request_status provided for notification")
            
        except Exception as e:
            logger.error(f"Error sending email notifications: {e}")
            raise
        finally:
            pythoncom.CoUninitialize()

    def _send_new_request_notifications(self, outlook, custom_msg=None):
        """Send notifications for new requests to first approver and requester"""
        # Notify first approver
        self._create_and_send_mail(
            outlook,
            to_email=self.recipients['first_approver'],
            subject=self.msg_templates['NEW_REQUEST']['first_approver']['subject'],
            body=custom_msg or self.msg_templates['NEW_REQUEST']['first_approver']['body'].format(
                first_approver=self.recipients['first_approver']
            )
        )

        # Notify requester
        self._create_and_send_mail(
            outlook, 
            to_email=self.recipients['requester']['email'],
            subject=self.msg_templates['NEW_REQUEST']['requester']['subject'],
            body=custom_msg or self.msg_templates['NEW_REQUEST']['requester']['body'].format(
                requester=self.recipients['requester']['name']
            )
        )

    def _send_pending_notifications(self, outlook, custom_msg=None):
        """Send notifications for pending requests to final approver"""
        self._create_and_send_mail(
            outlook,
            to_email=self.recipients['final_approver'],
            subject=self.msg_templates['PENDING']['final_approver']['subject'],
            body=custom_msg or self.msg_templates['PENDING']['final_approver']['body'].format(
                final_approver=self.recipients['final_approver']
            ),
            cc=[self.recipients['first_approver']]
        )

    def _create_and_send_mail(self, outlook, to_email, subject, body, cc=None):
        """Helper method to create and send individual emails"""
        mail = outlook.CreateItem(0)
        mail.Subject = subject
        mail.HTMLBody = body
        mail.To = to_email
        
        if cc:
            mail.CC = "; ".join(cc)
        elif self.cc_persons:
            mail.CC = "; ".join(self.cc_persons)
            
        mail.Send()

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

    # Setter methods
    def set_requester(self, name: str, email: str):
        self.recipients['requester'] = {'name': name, 'email': email}

    def set_first_approver(self, email: str):
        self.recipients['first_approver'] = email

    def set_final_approver(self, email: str):
        self.recipients['final_approver'] = email

    def set_cc_persons(self, cc_persons: list):
        self.cc_persons = cc_persons

    # Getter methods
    def get_requester(self):
        return self.recipients['requester']

    def get_first_approver(self):
        return self.recipients['first_approver']

    def get_final_approver(self):
        return self.recipients['final_approver']

    def get_cc_persons(self):
        return self.cc_persons