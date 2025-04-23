import pythoncom
import win32com.client as win32
import os
import shutil
import uuid
from datetime import datetime

from loguru import logger
from services.ipc_service import IPC_Service
from docxtpl import DocxTemplate
from docx2pdf import convert
from docx import Document

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
        # Get the project root directory (where the api folder is located)
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Create rendered_templates directory if it doesn't exist
        self.rendered_dir = os.path.join(self.project_root, "rendered_templates")
        os.makedirs(self.rendered_dir, exist_ok=True)
        logger.info(f"Rendered templates directory: {self.rendered_dir}")
        
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

    # def _convert_to_pdf(self, docx_path):
    #     """
    #     Convert a Word document to PDF
        
    #     Args:
    #         docx_path: Path to the Word document
            
    #     Returns:
    #         str: Path to the generated PDF file
    #     """
    #     try:
    #         # Generate PDF path in the same directory as the DOCX
    #         pdf_path = os.path.splitext(docx_path)[0] + '.pdf'
            
    #         # Convert the document
    #         convert(docx_path, pdf_path)
    #         logger.info(f"Successfully converted {docx_path} to PDF: {pdf_path}")
            
    #         return pdf_path
    #     except Exception as e:
    #         logger.error(f"Error converting document to PDF: {e}")
    #         raise

    def send_notification(self, template_path=None, template_data=None, subject=None, request_status=None, custom_msg=None):
        """
        Send notifications based on request status or directly to a recipient
        
        Args:
            template_path: Path to the HTML template file (optional)
            template_data: Data to be used in the template (optional)
            subject: Email subject (optional)   
            request_status: Status of the request (optional)
            custom_msg: Custom message to send (optional)
        """
        try:
            pythoncom.CoInitialize()
            outlook = win32.Dispatch("Outlook.Application")
            
            # Set request status if provided
            if request_status:
                self.request_status = request_status
            
            # Validate required fields
            self._validate_required_fields()
            
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
                # Send email to final approver
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
            # Clear the rendered document path after sending
            logger.info("Cleared rendered document path after sending")
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
        
            # Log the template data for debugging
        logger.debug(f"Template data: {template_data}")
        logger.debug(f"Rendered docx path: {self.get_rendered_docx_path()}")
        logger.debug(f"Template path: {self.get_template_path()}")
        
        path = os.path.abspath(self.get_rendered_docx_path())
        logger.info(f"Attaching file: {path}, exists? {os.path.exists(path)}")
        mail.Attachments.Add(path)
        
        template_content = f"""
        <html>
        <body>
            <p>Please find the attached document for your review.</p>
            <p>This is an automated message from the Purchase Request System.</p>
        </body>
        </html>
        """
        # Set the email body
        mail.HTMLBody = template_content
        
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
        
        try:
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
