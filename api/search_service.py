######################################################################################
# Name: SEARCH SERVICE
# Author: ROMAN CAMPBELL
# Date: 03/20/2025
# Description:

######################################################################################
from loguru import logger
from six import text_type
import db_service as dbas
from sqlalchemy import event
from sqlalchemy.orm.session import Session
from whoosh.filedb.filestore import FileStorage
from whoosh.analysis import RegexTokenizer, LowercaseFilter, StopFilter
from whoosh.fields import Schema, TEXT, ID, NUMERIC, BOOLEAN, DATETIME
from whoosh.index import create_in
from whoosh.writing import AsyncWriter
from whoosh.qparser import MultifieldParser, AndGroup
from whoosh.qparser.dateparse import DateParserPlugin
import whoosh.index as index
import ipc_service as ipc
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
    def __init__(self, session=None):
        self.session = session
        self.primary_key = "ID"
        
        # Create index dir if it doesnt already exist
        if not os.path.exists("indexdir"):
            os.mkdir("indexdir")
            self.ix = create_in("indexdir", schema=self.approval_schema, indexname="approvals")
        else:
            # Open existing index
            self.ix = index.open_dir("indexdir", indexname="approvals")
            logger.success("Index opened successfully...")
        
        self.analyzer = RegexTokenizer() | LowercaseFilter() | StopFilter()
        
        # Add event listeners
        event.listen(Session, "before_commit", self.before_commit)
        event.listen(Session, "after_commit", self.after_commit)
        
    ############################################################
    ## CREATE WHOOSH INDEX
    def create_whoosh_index(self):
        shm_data = ipc.ipc_instance.receive_from_shm()
        logger.success(f"{shm_data}")
        """
        Create a Whoosh index for approval records.

        This method creates the index directory if it does not exist, builds the Whoosh index
        using the predefined schema, retrieves all approval records from the database, and adds
        them to the index.
        """
        
        writer = self.ix.writer()
        session = next(dbas.get_db_session())
        
        # Query approval table
        approvals = dbas.get_all_approval(session)
        
        # Define the list of fields to index
        fields = ['ID', 'reqID', 'requester', 'recipient', 'budgetObjCode',
                'fund', 'quantity', 'totalPrice', 'priceEach', 'location',
                'newRequest', 'pendingApproval', 'approved', 'status',
                'createdTime', 'approvedTime', 'deniedTime']
        
        for approval in approvals:
            # Build dictionary dynamically via getattr
            doc = {field: getattr(approval, field) for field in fields}
            doc['ID'] = str(doc['ID'])
            writer.update_document(**doc)
            
        writer.commit()
        logger.success("Whoosh Index created successfully")
        
    ############################################################
    ## DIRTY APPROVAL -- altered but not deleted
    def alter_approval_doc(self, id, record):
        writer = AsyncWriter(self.ix)
        record['ID'] = str(id)
        writer.update_document(**record)
        writer.commit()
        logger.success("Approval doc has been updated")
        
    ############################################################
    ## GET INDEX FOR MODEL CLASS
    # Gets the whoosh index for this model, creating one if it does not exist.
    def index_for_model_class(self, model_class):
        index = self.indexes.get(model_class.__name__)
        if index is None:
            self.create_whoosh_index()
        return index
        
    ############################################################
    ## EXECUTE SEARCH
    def execute_search(self, query):
        
        with self.ix.searcher() as searcher:
            parser = MultifieldParser(self.searchable_fields, schema=self.ix.schema, group=AndGroup)
            query_obj = parser.parse(query)
            results = searcher.search(query_obj, limit=2)
            
            # Convert results to a list of dictionaries
            return [dict(hit) for hit in results]
        
    ############################################################
    ## BEFORE COMMIT
    def before_commit(self, session):
        self.to_update = {}
        logger.info("before_commit execution")
        for model in session.new:
            model_class = model.__class__
            if hasattr(model_class, 'searchable_fields'):
                self.to_update.setdefault(model_class.__name__, []).append(
                    ("new", model))
        
        for model in session.deleted:
            model_class = model.__class__
            if hasattr(model_class, 'searchable_fields'):
                self.to_update.setdefault(model_class.__name__, []).append(
                    ("deleted", model))
                
        for model in session.dirty:
            model_class = model.__class__
            if hasattr(model_class, 'searchable_fields'):
                self.to_update.setdefault(model_class.__name__, []).append(
                    ("changed", model))
        

    ############################################################
    ## AFTER COMMIT
    def after_commit(self, session):
        """
        Any db updates go through here. We check if any of these models have
        ``__searchable__`` fields, indicating they need to be indexed. With these
        we update the whoosh index for the model. If no index exists, it will be
        created here; this could impose a penalty on the initial commit of a model.
        """
        logger.info("after_commit execution")
        for typ, values in self.to_update.items():
            model_class = values[0][1].__class__
            index = self.index_for_model_class(model_class)
            with index.writer() as writer:
                searchable = model_class.__searchable__
                
                for change_type, model in values:
                    writer.delete_by_term(
                        self.primary_key, text_type(getattr(model, self.primary_key)))
                    
                    if change_type in ("new", "change"):
                        attrs = {key: getattr(model, key) for key in searchable}
                        attrs[self.primary_key] = text_type(getattr(model, self.primary_key))
                        writer.add_document(**attrs)

    ###################################################################################################
    ## MESSAGE QUEUE -- for receiving message from db_service to update index
