import os
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
    def __init__(self, msg_body, to_recipient, from_sender, subject, link=None, msg_data=None, cc_persons=None):
        # Init NotificationManager class
        self.msg_body = msg_body
        self.to_recipient = to_recipient
        self.from_sender = from_sender
        self.subject = subject
        self.cc_persons = cc_persons or [] # optional
        self.msg_data = msg_data or [] # optional (used to add data from variables dynamically)
        self.link = link # optional
    
    # Send notification email to recipients
    def send_email(self, template_path):
        # Init COM for thread to computer with microsoft components
        pythoncom.CoInitialize()
        notification = self._generate_notification(template_path)
        
        # Send email using outlook
        print("SENDING EMAIL...")
        outlook = win32.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)
        mail.Subject = self.subject
        mail.Body = notification
        mail.To = self.to_recipient
        
        # Include the CC if present
        if self.cc_persons:
            mail.CC = "; ".join(self.cc_persons)
        mail.Send()
        print("Email sent successfully...")
            
    # Load the email notification message template and generate notification
    def _generate_notification(self, file_path):
        with open(file_path, 'r') as file:
            template = file.read()
            
        return template.format(**self.msg_data)