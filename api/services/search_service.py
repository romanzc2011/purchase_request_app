######################################################################################
# Name: SEARCH SERVICE
# Author: ROMAN CAMPBELL
# Date: 03/20/2025
# Description: Optimized search service for purchase request approvals

from loguru import logger
from six import text_type
import api.services.db_service as dbas
from api.services.db_service import get_session
from sqlalchemy import event
from sqlalchemy.orm.session import Session
from whoosh.filedb.filestore import RamStorage
from whoosh.analysis import RegexTokenizer, LowercaseFilter, StopFilter, StemmingAnalyzer
from whoosh.fields import Schema, ID, TEXT, NUMERIC, BOOLEAN, DATETIME
from whoosh.index import create_in, open_dir
from whoosh.writing import AsyncWriter
from whoosh.qparser import MultifieldParser, OrGroup
from whoosh.query import Term, Prefix, Or
import os
from functools import lru_cache
from typing import Dict, List, Optional, Any
from datetime import datetime

# -----------------------------------------------------------------------------
# Whoosh schema: define once here, reuse in index creation and searches
approval_schema = Schema(
    ID            = ID(stored=True, unique=True),
    UUID          = ID(stored=True, unique=True),
    IRQ1_ID       = ID(stored=True),
    CO            = TEXT(stored=True),
    requester     = TEXT(stored=True, analyzer=StemmingAnalyzer()),
    datereq       = TEXT(stored=True),
    dateneed      = TEXT(stored=True),
    orderType     = TEXT(stored=True),
    itemDescription = TEXT(stored=True),
    justification = TEXT(stored=True),
    addComments   = TEXT(stored=True),
    trainNotAval  = BOOLEAN(stored=True),
    needsNotMeet  = BOOLEAN(stored=True),
    budgetObjCode = ID(stored=True),
    fund          = ID(stored=True),
    priceEach     = NUMERIC(stored=True, numtype=float),
    totalPrice    = NUMERIC(stored=True, numtype=float),
    location      = TEXT(stored=True),
    quantity      = NUMERIC(stored=True, numtype=int),
    status        = TEXT(stored=True),
    createdTime   = TEXT(stored=True)
)

# Fields used for full-text/prefix searching
searchable_fields = [
    'ID', 'IRQ1_ID', 'CO', 'requester', 'dateneed', 'datereq', 'budgetObjCode',
    'fund', 'itemDescription', 'justification', 'trainNotAval', 'needsNotMeet',
    'quantity', 'totalPrice', 'priceEach', 'location', 'status', 'createdTime'
]

class SearchService:
    """
    Optimized search service for purchase request approvals.
    - RAM storage option
    - Cached schema lookup
    - Batched, async index updates
    - Prefix + fuzzy search
    """

    def __init__(self, session: Optional[Session] = None, use_ram: bool = False):
        self.session = session
        self.primary_key = "ID"
        self._pending_updates: List[Any] = []
        self.index_dir = "indexdir"

        # Initialize Whoosh index
        if use_ram:
            self.ix = RamStorage().create_index(approval_schema)
        else:
            if not os.path.exists(self.index_dir):
                os.makedirs(self.index_dir)
                self.ix = create_in(self.index_dir, schema=approval_schema)
            else:
                self.ix = open_dir(self.index_dir)
                logger.success("Index opened successfully")

        # Build or rebuild the index
        self.create_whoosh_index()

        # Analyzer for custom parsers
        self.analyzer = RegexTokenizer() | LowercaseFilter() | StopFilter()

        # Listen for ORM events
        event.listen(Session, "before_commit", self.before_commit)
        event.listen(Session, "after_commit", self.after_commit)

    def create_whoosh_index(self, db=None):
        """Create a new Whoosh index for purchase requests and their approvals."""
        try:
            # Create the index directory if it doesn't exist
            if not os.path.exists(self.index_dir):
                os.makedirs(self.index_dir)
            
            # Create the index using the global schema
            ix = create_in(self.index_dir, approval_schema)
            
            # Get all purchase requests and their approvals
            with get_session() as session:
                purchase_requests = dbas.get_all_purchase_requests(session)
                
                if not purchase_requests:
                    logger.info("No purchase requests found in database")
                    return
                
                # Create a writer for the index
                writer = ix.writer()
                
                # Index each purchase request and its approval
                for pr in purchase_requests:
                    # Get the approval for this purchase request
                    approval = dbas.get_approval_by_id(session, pr.ID)
                    if not approval:
                        continue
                        
                    # Convert approval to dict and handle enum values
                    doc = {}
                    for key, value in approval.__dict__.items():
                        if key.startswith('_'):
                            continue
                        # Handle enum values
                        if isinstance(value, dbas.ItemStatus):
                            doc[key] = value.value  # Use the enum's value (string)
                        elif isinstance(value, datetime):
                            # Store datetime as string in YYYY-MM-DD format
                            doc[key] = value.strftime('%Y-%m-%d')
                        elif isinstance(value, str) and key in ['datereq', 'dateneed', 'createdTime']:
                            # Handle string dates - try to parse and reformat
                            try:
                                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                                doc[key] = dt.strftime('%Y-%m-%d')
                            except ValueError:
                                # If parsing fails, use the original string
                                doc[key] = value
                        else:
                            doc[key] = value
                    
                    # Filter to only include fields that exist in the schema
                    filtered_doc = {k: v for k, v in doc.items() if k in approval_schema.names()}
                    
                    # Add the document to the index
                    writer.add_document(**filtered_doc)
                
                # Commit the changes
                writer.commit()
                
            logger.info("Search index created successfully")
            
        except Exception as e:
            logger.error(f"Error creating search index: {e}")
            raise

    def execute_search(self, query: str, db: Session, limit: int = 10) -> List[Dict]:
        """Perform a prefix-then-fuzzy search across multiple fields."""
        with self.ix.searcher() as searcher:
            # Build prefix queries for non-date/numeric fields
            prefixes = [Prefix(f, query) for f in searchable_fields
                        if not self.ix.schema[f].__class__ in (NUMERIC, DATETIME)]
            combined = Or(prefixes)
            results = searcher.search(combined, limit=limit)

            # Fallback to fuzzy if empty
            if not results:
                parser = MultifieldParser(searchable_fields, schema=self.ix.schema, group=OrGroup)
                query_obj = parser.parse(query)
                results = searcher.search(query_obj, limit=limit)

            return [dict(hit) for hit in results]

    def before_commit(self, session):
        """Cache pending ORM changes."""
        self._pending_updates = [ ("deleted" if m in session.deleted else
                                    "new" if m in session.new else
                                    "updated", m)
                                  for m in session.new | session.dirty | session.deleted
                                  if hasattr(m.__class__, '__searchable__') ]

    def after_commit(self, session):
        """Apply batched changes to the index."""
        if not self._pending_updates:
            return
        writer = AsyncWriter(self.ix)
        try:
            for change, model in self._pending_updates:
                key = getattr(model, self.primary_key)
                if change == 'deleted':
                    writer.delete_by_term(self.primary_key, text_type(key))
                else:
                    # Build attrs dict
                    attrs = {}
                    for f in model.__class__.__searchable__:
                        if f not in self.ix.schema.names():
                            continue  # Skip fields not in schema
                        v = getattr(model, f, None)
                        if isinstance(v, dbas.ItemStatus):
                            attrs[f] = v.value
                        elif isinstance(v, datetime):
                            attrs[f] = v.strftime('%Y-%m-%d')
                        else:
                            attrs[f] = v
                    attrs[self.primary_key] = text_type(key)
                    writer.update_document(**attrs)
            writer.commit()
        except Exception as e:
            writer.cancel()
            logger.error(f"Error in after_commit: {e}")
            raise
