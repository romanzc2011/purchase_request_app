# Dictionary for sql column
purchase_cols = {
    'ID': None,
    'reqID': None,
    'recipient': None,
    'requester': None,
    'phoneext': None,
    'datereq': None,
    'dateneed': None,
    'orderType': None,
    'fileAttachments': None,
    'itemDescription': None,
    'justification': None,
    'addComments': None,
    'learnAndDev': { 'trainNotAval': False, 'needsNotMeet': False },
    'budgetObjCode': None,
    'fund': None,
    'price': None,
    'location': None,
    'quantity': None,
}

# Dictionary for approval data
approvals_cols = {
    'ID': None,
    'reqID': None,
    'requester': None,
    'recipient': None,
    'budgetObjCode': None,
    'fund': None,
    'location': None,
    'quantity': None,
    'priceEach': None,
    'totalPrice': None,
    'new_request': None,
    'status': None
}