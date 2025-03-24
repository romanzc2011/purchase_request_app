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
from pras_database_manager import DatabaseManager

dbManager = DatabaseManager("./db/purchase_requests.db")
class SearchService:
    def __init__(self):
        pass

    def get_search_results(self, query: str):
        logger.info("Data received from search")
        ALLOWED_COLUMNS = {'requester', 'budgetObjCode', 'fund', 'location', 'mid_uuid'}

        results = []
        results.append(query)
        
        # Column based search for records
        query = request.args.get('query', '')
        query_column = request.args.get('queryColumn', '')

        # Build query with only allowed columns
        if query_column not in ALLOWED_COLUMNS:
            query_column = None

        # Build the SQL query
        if query_column:

            try:
                sql = f"SELECT * FROM approvals WHERE {query_column} LIKE ?"
                params = [f"{query}%"]
                print(sql)
                print(params)
            except Exception as e:
                logger.error(f"{e}")

            results = dbManager.fetch_rows(sql, params)
            return results

        else:
            sql = """
                SELECT * FROM approvals
                WHERE requester LIKE ?
                OR budgetObjCode LIKE ?
                OR fund LIKE ?
                OR location LIKE ?
                OR mid_uuid LIKE ?
                """
            params = [f"{query}%"]
            print(params)
            results = dbManager.fetch_rows(sql, params)
            
            return results
