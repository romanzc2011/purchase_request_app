# Dictionary for sql column
purchase_cols = {
    'req_id': None,
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
    'req_id': None,
    'requester': None,
    'budgetObjCode': None,
    'fund': None,
    'location': None,
    'quantity': None,
    'priceEach': None,
    'totalPrice': None,
    'status': None
}