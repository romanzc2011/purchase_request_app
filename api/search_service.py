######################################################################################
# Name: SEARCH SERVICE
# Author: ROMAN CAMPBELL
# Date: 03/20/2025
# Description:

######################################################################################
from loguru import logger
import db_alchemy_service as dbas
from sqlalchemy import event
from whoosh.filedb.filestore import FileStorage
from whoosh.analysis import RegexTokenizer, LowercaseFilter, StopFilter
from whoosh.fields import Schema, TEXT, ID, NUMERIC, BOOLEAN, DATETIME
from whoosh.index import create_in
from whoosh.writing import AsyncWriter
from whoosh.qparser import MultifieldParser, AndGroup
from whoosh.qparser.dateparse import DateParserPlugin
import whoosh.index as index
import os


############################################################
## CLASS SEARCH SERVICE
############################################################

class SearchService():
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
        newRequest=BOOLEAN(stored=True),  
        pendingApproval=BOOLEAN(stored=True),
        approved=BOOLEAN(stored=True),      
        status=TEXT(stored=True),
        createdTime=DATETIME(stored=True),
        approvedTime=DATETIME(stored=True),
        deniedTime=DATETIME(stored=True)
        
    )
    
    searchable_fields = ['ID', 'reqID', 'requester', 'recipient', 'budgetObjCode','fund', 
                      'quantity', 'totalPrice', 'priceEach', 'location', 'newRequest', 
                      'approved', 'pendingApproval', 'status', 'createdTime', 'approvedTime', 'deniedTime']
    
    storage = FileStorage("indexdir")
    
    ###################################################################################################
    ### INIT
    def __init__(self):
        # Create index dir if it doesnt already exist
        if not os.path.exists("indexdir"):
            os.mkdir("indexdir")
            self.ix = create_in("indexdir", schema=self.approval_schema, indexname="approvals")
        else:
            # Open existing index
            self.ix = index.open_dir("indexdir", indexname="approvals")
            logger.success("Index opened successfully...")
        
        self.analyzer = RegexTokenizer() | LowercaseFilter() | StopFilter()

    ############################################################
    ## CREATE WHOOSH INDEX
    def create_whoosh_index(self):
        """
        Create a Whoosh index for approval records.

        This method creates the index directory if it does not exist, builds the Whoosh index
        using the predefined schema, retrieves all approval records from the database, and adds
        them to the index.
        """
        
        writer = AsyncWriter(self.ix)
        session = next(dbas.get_db_session())
        
        # Query approval table
        approvals = dbas.get_all_approval(session)
        
        for approval in approvals:
            writer.update_document(
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
                newRequest=approval.newRequest,
                pendingApproval=approval.pendingApproval,
                approved=approval.approved,
                status=approval.status,
                createdTime=approval.createdTime,
                approvedTime=approval.approvedTime,
                deniedTime=approval.deniedTime
            )
            
        writer.commit()
        logger.success("Whoosh Index created successfully")
        
    ############################################################
    ## UPDATE DOCUMENT
    def alter_approval_doc(self, id, record):
        writer = AsyncWriter(self.ix)
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
            newRequest=record["newRequest"],
            pendingApproval=record["pendingApproval"],
            approved=record["approved"],
            status=record["status"],
            createdTime=record["createdTime"],
            approvedTime=record["approvedTime"],
            deniedTime=record["deniedTime"]
        )
        writer.commit()
        logger.success("Approval doc has been updated")
        
    ############################################################
    ## EXECUTE SEARCH
    def execute_search(self, query):
        with self.ix.searcher() as searcher:
            parser = MultifieldParser(self.searchable_fields, schema=self.ix.schema, group=AndGroup)
            query_obj = parser.parse(query)
            results = searcher.search(query_obj, limit=2)
            # Convert results to a list of dictionaries
            return [dict(hit) for hit in results]
