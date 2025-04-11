######################################################################################
# Name: SEARCH SERVICE
# Author: ROMAN CAMPBELL
# Date: 03/20/2025
# Description: Optimized search service for purchase request approvals

######################################################################################
from loguru import logger
from six import text_type
import services.db_service as dbas
from sqlalchemy import event
from sqlalchemy.orm.session import Session
from whoosh.filedb.filestore import FileStorage, RamStorage
from whoosh.analysis import RegexTokenizer, LowercaseFilter, StopFilter, StemmingAnalyzer
from whoosh.fields import Schema, TEXT, ID, NUMERIC, BOOLEAN, DATETIME
from whoosh.index import create_in
from whoosh.writing import AsyncWriter
from whoosh.qparser import MultifieldParser, AndGroup, OrGroup
from whoosh.qparser.dateparse import DateParserPlugin
from whoosh.query import Term, Prefix, Or
import whoosh.index as index
import whoosh.fields
import os
from functools import lru_cache
from typing import Dict, List, Optional, Any

############################################################
## CLASS SEARCH SERVICE
############################################################

class SearchService:
    """
    Optimized search service for purchase request approvals.
    
    Key optimizations:
    - Uses RAM storage for faster indexing when possible
    - Caches common search results
    - Batches index updates
    - Uses async writer for non-blocking index updates
    - Optimized schema with only necessary fields
    - Real-time prefix search for partial matches
    """
    
    # Optimized schema with only essential fields and appropriate field types
    approval_schema = Schema(
        ID=ID(stored=True, unique=True),
        reqID=ID(stored=True),             
        requester=TEXT(stored=True, analyzer=StemmingAnalyzer()),        
        recipient=TEXT(stored=True, analyzer=StemmingAnalyzer()),        
        budgetObjCode=ID(stored=True),    
        fund=ID(stored=True),             
        quantity=NUMERIC(stored=True, numtype=int, bits=16),  # Reduced bits
        totalPrice=NUMERIC(stored=True, numtype=float),
        priceEach=NUMERIC(stored=True, numtype=float),
        location=TEXT(stored=True),         
        status=TEXT(stored=True),
        createdTime=DATETIME(stored=True),
        approvedTime=DATETIME(stored=True),
        deniedTime=DATETIME(stored=True)
    )
    
    searchable_fields = [
        'ID', 'reqID', 'requester', 'recipient', 'budgetObjCode', 'fund', 'priceEach','totalPrice',
        'location', 'status','quantity','createdTime'
    ]
    
    def __init__(self, session: Optional[Session] = None, use_ram: bool = False):
        self.session = session
        self.primary_key = "ID"
        self.indexes: Dict[str, Any] = {}
        self._pending_updates: List[Dict] = []
        self.batch_size = 100
        
        # Use RAM storage for testing/small datasets
        if use_ram:
            self.storage = RamStorage()
            self.ix = self.storage.create_index(self.approval_schema)
        else:
            if not os.path.exists("indexdir"):
                os.makedirs("indexdir")
                self.ix = create_in("indexdir", schema=self.approval_schema, indexname="approvals")
            else:
                self.ix = index.open_dir("indexdir", indexname="approvals")
                logger.success("Index opened successfully")
            
        self.create_whoosh_index()
        self.analyzer = RegexTokenizer() | LowercaseFilter() | StopFilter()
        
        # Register event listeners
        event.listen(Session, "before_commit", self.before_commit)
        event.listen(Session, "after_commit", self.after_commit)
    
    @lru_cache(maxsize=1000)
    def _get_schema_and_primary(self, model_class):
        """Cached schema generation for model classes"""
        schema = {}
        primary = None
        for field in model_class.__table__.columns:
            if field.primary_key:
                schema[field.name] = whoosh.fields.ID(stored=True, unique=True)
                primary = field.name
            if hasattr(model_class, '__searchable__') and field.name in model_class.__searchable__:
                schema[field.name] = whoosh.fields.TEXT(analyzer=StemmingAnalyzer())
        return Schema(**schema), primary

    def create_whoosh_index(self):
        """Create/update Whoosh index using batch processing"""
        writer = AsyncWriter(self.ix)
        session = next(dbas.get_session())
        
        try:
            approvals = dbas.get_all_approval(session)
            batch = []
            
            for approval in approvals:
                doc = {field: getattr(approval, field) for field in self.searchable_fields}
                doc['ID'] = str(doc['ID'])
                batch.append(doc)
                
                if len(batch) >= self.batch_size:
                    # Process each document individually
                    for document in batch:
                        writer.update_document(**document)
                    batch = []
            
            if batch:  # Process remaining documents
                # Process each document individually
                for document in batch:
                    writer.update_document(**document)
                
            writer.commit()
            logger.success("Whoosh Index created successfully")
            
        except Exception as e:
            writer.cancel()
            logger.error(f"Error creating index: {e}")
            raise
        finally:
            session.close()

    def alter_approval_doc(self, id: str, record: Dict):
        """Update a single document asynchronously"""
        writer = AsyncWriter(self.ix)
        try:
            record['ID'] = str(id)
            writer.update_document(**record)
            writer.commit()
            logger.success("Approval doc updated")
        except Exception as e:
            writer.cancel()
            logger.error(f"Error updating doc: {e}")
            raise

    @lru_cache(maxsize=100)
    def _exact_singleton_search(self, term: str, query: str, db: Session):
        """Cached exact match search"""
        with self.ix.searcher() as searcher:
            column_term = Term(term, query)
            result = searcher.search(column_term, limit=1)
            
            if result:
                session = self.session or db
                return session.query(dbas.Approval).filter(getattr(dbas.Approval, term) == query).all()
        return None

    def execute_search(self, query: str, db: Session, limit: int = 10):
        """Execute optimized search with prefix matching for partial queries"""
        with self.ix.searcher() as searcher:
            # Filter out date and numeric fields from searchable fields
            searchable_non_date_fields = []
            for field in self.searchable_fields:
                field_type = type(self.ix.schema[field])
                # Skip date fields and numeric fields
                if field_type != whoosh.fields.DATETIME and field_type != whoosh.fields.NUMERIC:
                    searchable_non_date_fields.append(field)
            
            # Build prefix queries for each non-date, non-numeric field
            prefix_queries = []
            for field in searchable_non_date_fields:
                prefix_queries.append(Prefix(field, query))
            
            # Combine with OR for any field matches
            combined_query = Or(prefix_queries)
            
            # Search with prefix matching
            results = searcher.search(combined_query, limit=limit)
            
            if not results:
                # Fall back to fuzzy search with OrGroup for partial matches
                parser = MultifieldParser(searchable_non_date_fields, schema=self.ix.schema, group=OrGroup)
                query_obj = parser.parse(query)
                results = searcher.search(query_obj, limit=limit)
            
            return [dict(hit) for hit in results]

    def before_commit(self, session):
        """Prepare batch updates before commit"""
        self._pending_updates = []
        for model in session.new | session.dirty | session.deleted:
            if hasattr(model.__class__, '__searchable__'):
                change_type = "deleted" if model in session.deleted else "new" if model in session.new else "changed"
                self._pending_updates.append((change_type, model))

    def after_commit(self, session):
        """Process batch updates after commit"""
        if not self._pending_updates:
            return
            
        writer = AsyncWriter(self.ix)
        try:
            for change_type, model in self._pending_updates:
                if change_type == "deleted":
                    writer.delete_by_term(self.primary_key, text_type(getattr(model, self.primary_key)))
                else:
                    attrs = {
                        key: getattr(model, key) 
                        for key in model.__class__.__searchable__
                    }
                    attrs[self.primary_key] = text_type(getattr(model, self.primary_key))
                    writer.add_document(**attrs)
            writer.commit()
        except Exception as e:
            writer.cancel()
            logger.error(f"Error in after_commit: {e}")
            raise