import pythoncom
import win32com.client as win32
import os

from loguru import logger
from services.ipc_service import IPC_Service
from docxtpl import DocxTemplate
from docx2pdf import convert

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

    def _convert_to_pdf(self, docx_path):
        """
        Convert a Word document to PDF
        
        Args:
            docx_path: Path to the Word document
            
        Returns:
            str: Path to the generated PDF file
        """
        try:
            # Generate PDF path in the same directory as the DOCX
            pdf_path = os.path.splitext(docx_path)[0] + '.pdf'
            
            # Convert the document
            convert(docx_path, pdf_path)
            logger.info(f"Successfully converted {docx_path} to PDF: {pdf_path}")
            
            return pdf_path
        except Exception as e:
            logger.error(f"Error converting document to PDF: {e}")
            raise

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
                    template_path=template_path,
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
                    template_path=template_path,
                    template_data=template_data,
                    cc=self.cc_persons
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
                    template_path=template_path,
                    template_data=template_data,
                    cc=self.cc_persons
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
        
        if template_path and template_data:
            try:
                # Convert template path to absolute path if it's relative
                if not os.path.isabs(template_path):
                    template_path = os.path.join(self.project_root, template_path)
                
                # Generate a unique filename for this email
                rendered_file = os.path.join(self.rendered_dir, f"rendered_template_{os.urandom(4).hex()}.docx")
                
                # Log the template data for debugging
                logger.debug(f"Template data: {template_data}")
                logger.debug(f"Template path: {template_path}")
                logger.debug(f"Rendered file path: {rendered_file}")
                
                # Render the template
                template = DocxTemplate(template_path)
                try:
                    template.render(template_data)
                except Exception as e:
                    logger.error(f"Template rendering error: {str(e)}")
                    logger.error("Template data structure:")
                    for key, value in template_data.items():
                        logger.error(f"{key}: {type(value)} = {value}")
                    raise
                
                template.save(rendered_file)
                
                # Verify the file exists before converting
                if not os.path.exists(rendered_file):
                    raise FileNotFoundError(f"Rendered file not found at: {rendered_file}")
                
                # Convert to PDF
                pdf_file = self._convert_to_pdf(rendered_file)
                
                # Attach both the DOCX and PDF
                mail.Attachments.Add(pdf_file)
                logger.info(f"Attached documents: {rendered_file} and {pdf_file}")
                
                # Set the email body
                mail.HTMLBody = body or "Please see the attached document."
                
            except Exception as e:
                logger.error(f"Error processing template: {e}")
                raise
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
        
        try:
            mail.Send()
            logger.info(f"Email sent to {to_email} with subject: {subject}")
            
            # Clean up the rendered files after sending
            if template_path and template_data:
                try:
                    if os.path.exists(rendered_file):
                        os.remove(rendered_file)
                        logger.info(f"Cleaned up rendered DOCX file: {rendered_file}")
                    if os.path.exists(pdf_file):
                        os.remove(pdf_file)
                        logger.info(f"Cleaned up rendered PDF file: {pdf_file}")
                except Exception as e:
                    logger.warning(f"Could not clean up rendered files: {e}")
                    
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
