import win32com.client as win32
import os

"""
AUTHOR: Roman Campbell
DATE: 01/07/2025
Used to send purchase request notifications
"""

request_details = {
    'req_id': None,
    'requester': None,
    'date_req': None,
    'date_needed': None,
    'budget_obj_code': None,
    'fund': None,
    'location': None,
    'quantity': None,
    'price': None,
    'total_price': None
}


def sendNewNotification():
    # Send new request notification
    print("SENDING EMAIL")
    
    # Load notification template
    
    outlook = win32.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)

    mail.Subject = "Email Subject"
    mail.Body = "Email body,Python win32com and Outlook."
    mail.To = "roman_campbell@lawb.uscourts.gov"
    mail.Send()