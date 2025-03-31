######################################################################################
# Name: SEARCH SERVICE
# Author: ROMAN CAMPBELL
# Date: 03/20/2025
# Description:

######################################################################################
from loguru import logger
from sqlalchemy import or_
from sqlalchemy.orm import Session
import db_alchemy_service as dbas
from typing import Optional
from db_alchemy_service import Approval
from whoosh.filedb.filestore import FileStorage
from whoosh.fields import Schema, TEXT, ID, NUMERIC, BOOLEAN
from whoosh.index import create_in
from whoosh.writing import AsyncWriter
import whoosh.index as index
import os


############################################################
## CLASS SEARCH SERVICE
############################################################

class SearchService:
    """
    Requistion ID and Search Service for the search bar on the Approvals Table.
    Put these two services together as they will both be dealing with the reqID.
    For clarity and ease of searching the reqID will contain first 4 char of 
    Requester's name, the 4 char of the BOC, Fund, and 4 char of location with the
    4 char middle section of the uuid which will remain as the primary key of the
    database. Will also Search for NEW REQUEST, PENDING FINAL, COMPLETE
    User will be able to search for orders based on any number of the sections of
    req ID, functionality will also be added to search for requests based on status.
    
     Methods:
    - search_results: Search approval records using a query and an optional column filter.
    - create_whoosh_index: Build a Whoosh index based on the approval records from the database.
    """
    
    ############################################################
    ## APPROVAL SEARCH SCHEMA - whoosh schema for indexing approval records
    approval_schema = Schema(
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
    
    storage = FileStorage("indexdir")
    
    def __init__(self):
        pass
    
    ## SEARCH RESULTS
    def search_results(db: Session, query: str, query_column: Optional[str] = None):
        """
        Search for approval records based on a text query and an optional specific column.

        If query_column is provided and valid, the search will be restricted to that column.
        Otherwise, the search will be performed across all allowed columns.

        Allowed columns:
          - requester
          - budgetObjCode
          - fund
          - location
          - reqID
          - status

        :param db: Database session.
        :param query: The search term.
        :param query_column: Optional specific column to search.
        :return: List of matching Approval records.
        """
        
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

    ############################################################
    ## CREATE WHOOSH INDEX
    def create_whoosh_index(self):
        """
        Create a Whoosh index for approval records.

        This method creates the index directory if it does not exist, builds the Whoosh index
        using the predefined schema, retrieves all approval records from the database, and adds
        them to the index.
        """
        
        session = next(dbas.get_db_session())
        
        # Create index directory if not already created
        if not os.path.exists("indexdir"):
            os.mkdir("indexdir")
            
             # Create whoosh index from schema
            ix = create_in("indexdir", schema=self.approval_schema, indexname="approvals")

            # Query approval table
            approvals = dbas.get_all_approval(session)

            # Open whoosh writer to add docs to index
            writer = AsyncWriter(ix)
            
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
            logger.success("Whoosh Index created successfully")
        else:
            # Open existing index
            ix = index.open_dir("indexdir", indexname="approvals")
            writer = AsyncWriter(ix)
            logger.success("Writer ready for usage")
            
    ############################################################
    ## ADD APPROVAL DOC
    def add_approval_doc(writer, record):
        writer.add_document(
            ID=record["ID"],
            reqID=record["reqID"],
            requester=record["requester"],
            recipient=record["recipient"],
            budgetObjCode=record["budgetObjCode"],
            fund=record["fund"],
            quantity=record["quantity"],
            totalPrice=record["totalPrice"],
            priceEach=record["priceEach"],
            location=record["location"],
            new_request=record["new_request"],
            pending_approval=record["pending_approval"],
            approved=record["approved"],
            status=record["status"]
        )
        writer.commit()
        logger.success("Approval doc has been committed")
        
    ############################################################
    ## UPDATE DOCUMENT
    def update_approval_doc(writer, id, record):
        writer.update_document(
            ID=str(id),
            reqID=str(record["reqID"]),
            requester=record["requester"],
            recipient=record["recipient"],
            budgetObjCode=record["budgetObjCode"],
            fund=record["fund"],
            quantity=record["quantity"],
            totalPrice=record["totalPrice"],
            priceEach=record["priceEach"],
            location=record["location"],
            new_request=record["new_request"],
            pending_approval=record["pending_approval"],
            approved=record["approved"],
            status=record["status"]
        )
        writer.commit()
        logger.success("Approval doc has been updated")