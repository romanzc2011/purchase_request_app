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
from loguru import logger
from flask import request, jsonify
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic_schemas import AppovalSchema
from typing import Optional, List
import db_alchemy_service as dbas
from db_alchemy_service import Approval

class SearchService:
    def __init__(self):
        pass
    
    def get_search_results(
        self,
        query: str,
        db: Session,
        query_column: Optional[str] = None
    ) -> List[AppovalSchema]:
        ALLOWED_COLUMNS = {'requester', 'budgetObjCode', 'fund', 'location'}
        
        # Validate query_column
        if query_column not in ALLOWED_COLUMNS:
            query_column = None
            
        if query_column:
            filter_expr = getattr(Approval, query_column).ilike(f"{query}%")
            results = db.query(Approval).filter(filter_expr).all()
        else:
            results = db.query(Approval).filter(
                or_(
                    Approval.requester.ilike(f"{query}%"),
                    Approval.budgetObjCode.ilike(f"{query}%"),
                    Approval.fund.ilike(f"{query}%"),
                    Approval.location.ilike(f"{query}%")
                )
            ).all()
            
        # Convert SQLAlchemy objects to Pyndantic models
        return [AppovalSchema.model_validate(approval) for approval in results]