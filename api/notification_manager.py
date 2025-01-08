import os
import pandas as pd
import pythoncom
import win32com.client as win32

"""
AUTHOR: Roman Campbell
DATE: 01/07/2025
Used to send purchase request notifications
"""

class NotificationManager:
    """
    A class to manage email notification operations
    """
    def __init__(self, msg_body, to_recipient, from_sender, subject, cc_persons=None):
        # Init NotificationManager class
        self.msg_body = msg_body
        self.to_recipient = to_recipient
        self.from_sender = from_sender
        self.subject = subject
        self.cc_persons = cc_persons or [] # optional
    
    # Send notification email to recipients
    def send_email(self, msg_body):
        self.msg_body = msg_body
        
        # Send email using outlook
        print("SENDING EMAIL...")
        pythoncom.CoInitialize()
        outlook = win32.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)
        
        if not self.to_recipient:
            raise ValueError("Receipient email is not set")
        
        if not self.subject:
            raise ValueError("Email subject is not set")
        
        if not self.msg_body:
            raise ValueError("Message body is not set")
        
        mail.Subject = self.subject
        mail.HTMLBody = self.msg_body
        mail.To = self.to_recipient
        
        # Include the CC if present
        if self.cc_persons:
            mail.CC = "; ".join(self.cc_persons)
        mail.Send()
        print("Email sent successfully...")
        
    ##################################################################
    ## LOAD TEMPLATE
    def load_email_template(self, template_path):
        with open(template_path, "r") as file:
            template = file.read()
        return template
        
    ##################################################################
    ## GENE
    ##################################################################
    ## SETTERS
    def set_msg_body(self, value):
        self._msg_body = value
        
    def set_to_recipient(self, value):
        self._to_recipient = value
        
    def set_from_sender(self, value):
        self._from_sender = value
    
    def set_subject(self, value):
        self._subject = value
    
    def set_cc_persons(self, value):
        self._cc_persons = value
        
    def set_msg_data(self, value):
        self._msg_data = value
        
    def set_link(self, value):
        self._link = value
        
    ##################################################################
    ## GETTERS
    def get_msg_body(self):
        return self._msg_body
        
    def get_to_recipient(self):
        return self._to_recipient
        
    def get_from_sender(self):
        return self._from_sender
    
    def set_subject(self):
        return self._subject
    
    def set_cc_persons(self):
        return self._cc_persons
        
    def set_msg_data(self):
        return self._msg_data
        
    def set_link(self):
        return self._link