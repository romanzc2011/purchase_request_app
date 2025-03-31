######################################################################################
# Name: SEARCH SERVICE
# Author: ROMAN CAMPBELL
# Date: 03/20/2025
# Description:
"""
Requistion ID and Search Service for the search bar on the Approvals Table.
Put these two services together as they will both be dealing with the reqID.
For clarity and ease of searching the reqID will contain first 4 char of 
Requester's name, the 4 char of the BOC, Fund, and 4 char of location with the
4 char middle section of the uuid which will remain as the primary key of the
database. Will also Search for NEW REQUEST, PENDING FINAL, COMPLETE
User will be able to search for orders based on any number of the sections of
req ID, functionality will also be added to search for requests based on status.
"""
######################################################################################
from sqlalchemy import or_
from sqlalchemy.orm import Session
import db_alchemy_service as dbas
from typing import Optional
from db_alchemy_service import Approval
from whoosh.fields import Schema, TEXT, ID, NUMERIC, BOOLEAN
from whoosh.index import create_in
import os

############################################################3
## APPROVAL SEARCH SCHEMA - whoosh
appoval_schema = Schema(
    ID=ID(stored=True, unique=True),
    reqID=ID(stored=True),             
    requester=TEXT(stored=True),        
    recipient=TEXT(stored=True),        
    budgetObjCode=TEXT(stored=True),    
    fund=TEXT(stored=True),             
    quantity=NUMERIC(stored=True, numtype=int),
    totalPrice=NUMERIC(stored=True, numtype=float),
    priceEach=NUMERIC(stored=True, numtype=float),
    location=TEXT(stored=True),         
    new_request=BOOLEAN(stored=True),  
    pending_approval=BOOLEAN(stored=True),
    approved=BOOLEAN(stored=True),      
    status=TEXT(stored=True)  
)

############################################################3
## SEARCH RESULTS
def search_results(db: Session, query: str, query_column: Optional[str] = None):
    # Define allowed columns
    allowed_columns = {
        'requester': Approval.requester,
        'budgetObjCode': Approval.budgetObjCode,
        'fund': Approval.fund,
        'location': Approval.location,
        'reqID': Approval.reqID,
        'status': Approval.status,
    }
    
    if not query:
        return db.query(Approval).all()
    
    # if a valid column is specified search by that column
    if query_column in allowed_columns:
        filter_expr = allowed_columns[query_column].ilike(f"%{query}%")
        results = db.query(Approval).filter(filter_expr).all()
    else:
        # Otherwise search all allowed
        results = db.query(Approval).filter(
            or_(
                Approval.requester.ilike(f"%{query}%"),
                Approval.budgetObjCode.ilike(f"%{query}%"),
                Approval.fund.ilike(f"%{query}%"),
                Approval.location.ilike(f"%{query}%"),
                Approval.reqID.ilike(f"%{query}%"),
                Approval.status.ilike(f"%{query}%")
            )
        ).all()
        
    return results

############################################################3
## CREATE WHOOSH INDEX
def create_whoosh_index():
    session = next(dbas.get_db_session())
    # Create index directory if not already created
    if not os.path.exists("indexdir"):
        os.mkdir("indexdir")
        
    # Create whoosh index from schema
    ix = create_in("indexdir", appoval_schema)

    # Query approval table
    approvals = dbas.get_all_approval(session)

    # Open whoosh writer to add docs to index
    writer = ix.writer()
    
    for approval in approvals:
        writer.add_document(
            ID=str(approval.ID),
            reqID=str(approval.reqID),
            requester=approval.requester,
            recipient=approval.recipient,
            budgetObjCode=approval.budgetObjCode,
            fund=approval.fund,
            quantity=approval.quantity,
            totalPrice=approval.totalPrice,
            priceEach=approval.priceEach,
            location=approval.location,
            new_request=approval.new_request,
            pending_approval=approval.pending_approval,
            approved=approval.approved,
            status=approval.status
        )
    
    writer.commit()
    