from loguru import logger
from adu_ldap_service import LDAPManager
from ipc_service import IPC_Service
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
ldap_mgr = LDAPManager(server_name=os.getenv("LDAP_SERVER"), port=636, using_tls=True)

class EmailService:
    """
    A class to manage email notification operations
    requester_name will be the jenie is that user entered on request firstname lastname together
    """
    def __init__(self, msg_body, first_approver, final_approver, from_sender, subject, cc_persons=None):
        # Init EmailService class
        self.msg_body = msg_body
        self.first_approver = first_approver
        self.final_approver = final_approver
        self.requester_name = None
        self.requester_email = None
        self.from_sender = from_sender
        self.subject = subject
        self.cc_persons = cc_persons or [] # optional
    
    # Send notification email to recipients
    def send_email(self, msg_body=None):
        if msg_body is not None:
            self.msg_body = msg_body

        # Send email using outlook
        try:
            pythoncom.CoInitialize()
            outlook = win32.Dispatch("Outlook.Application")
            mail = outlook.CreateItem(0)
            
            if not self.requester_email:
                logger.warning("Requester email is not set")
                raise ValueError("Requester email is not set")
            
            if not self.subject:
                logger.warning("Email subject is not set")
                raise ValueError("Email subject is not set")
            
            if not self.msg_body:
                logger.warning("Message body is not set")
                raise ValueError("Message body is not set")
            
            if not self.first_approver:
                logger.warning("First approver email is not set")
                raise ValueError("First approver email is not set") 
            
            ## Create dynamic message body
            ################################################################
            ## FIRST APPROVER
            NEW_REQUEST = False
            PENDING = False
            
            stats = IPC_Service().receive_from_shm()
            if stats == b"NEW_REQUEST":
                NEW_REQUEST = True
            elif stats == b"PENDING":
                PENDING = True
                
            if self.get_first_approver() is not None and NEW_REQUEST:
                mail.Subject = "Purchase Request Notification - First Approver"
                mail.HTMLBody = "<p>Dear {first_approver},</p><p>You have a new purchase request to review.</p>"
                self.msg_body = self.msg_body.replace("{first_approver}", self.get_first_approver())
                mail.To = self.get_first_approver()
                
                
            ## FINAL APPROVER
            if self.get_final_approver() is not None and PENDING:
                mail.Subject = "Purchase Request Notification - Final Approver"
                mail.HTMLBody = "<p>Dear {final_approver},</p><p>You have a new purchase request to review.</p>"
                self.msg_body = self.msg_body.replace("{final_approver}", self.get_final_approver())
                mail.To(self.get_final_approver())
                mail.Recipients.Add(self.get_first_approver())
            
            ## REQUESTER
            if self.get_requester_name() is not None and NEW_REQUEST:
                mail.Subject = "Purchase Request Notification - Requester"
                mail.HTMLBody = "<p>Dear {requester},</p><p>Your purchase request has been submitted.</p>"
                self.msg_body = self.msg_body.replace("{requester}", self.get_requester_name())
                mail.Recipients.Add(self.get_requester_email())
            
            mail.Subject = self.subject
            mail.HTMLBody = self.msg_body
            mail.To = self.get_requester_email()
            mail.Recipients.Add(self.get_first_approver())
            
            # Include the CC if present
            if self.cc_persons:
                mail.CC = "; ".join(self.cc_persons)
            mail.Send()
            logger.info("Email sent successfully.")
        except Exception as e:
            logger.error(f"Error sending email: {e}")
        finally:
            pythoncom.CoUninitialize()
        
    ##################################################################
    ## LOAD TEMPLATE
    def load_email_template(self, template_path):
        with open(template_path, "r") as file:
            template = file.read()
        return template

    ##################################################################
    # SETTERS
    def set_msg_body(self, value):
        self.msg_body = value
        
    def set_requester_email(self, email: str):
        self.requester_email = email
        
    def set_requester_name(self, requester):
        requester_name = ldap_mgr.get_username()
        self.requester_name = requester_name
    
    # Set roman_campbell@lawb.uscourts.gov for testing
    def set_first_approver(self, value):
        self.first_approver = value   
        
    # Set roman_campbell@lawb.uscourts.gov for testing
    def set_final_approver(self, value):
        self.final_approver = value

    def set_from_sender(self, value):
        self.from_sender = value

    def set_subject(self, value):
        selfsubject = value

    def set_cc_persons(self, value):
        self.cc_persons = value

    def set_msg_data(self, value):
        self.msg_data = value

    def set_link(self, value):
        self.link = value

    ##################################################################
    # GETTERS
    def get_msg_body(self):
        return self.msg_body
    
    def get_requester_name(self):
        return self.requester_name
    
    def get_requester_email(self):
        return self.requester_email
    
    def get_first_approver(self):
        return self.first_approver
    
    def get_final_approver(self):
        return self.final_approver

    def get_from_sender(self):
        return self.from_sender

    def get_subject(self): 
        return self.subject

    def get_cc_persons(self):
        return self.cc_persons

    def get_msg_data(self): 
        return self.msg_data

    def get_link(self):
        return self.link