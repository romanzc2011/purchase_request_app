import json
import sqlite3
import os

class DatabaseManager:
    """
    Class to manage the purchase req database with sqlite3
    """
    #####################################################################################
    ## INITIALIZE CLASS
    def __init__(self, db_path):
        # Init Database Manager
        self.db_path = db_path
       
    #####################################################################################
    ## CREATE AND GET CONNECTION 
    def get_connection(self):
        # Establish and return connection to database
        connection = sqlite3.connect(self.db_path)
        connection.execute("PRAGMA foreign_key = ON;")
        connection.row_factory = sqlite3.Row
        return connection
    
    #####################################################################################
    ## CREATE PURCHASE REQUEST TABLE
    def create_purchase_req_table(self):
        # Create purchase_requests if not already done so
        query = """
        CREATE TABLE IF NOT EXISTS purchase_requests (
            req_id INTEGER PRIMARY KEY NOT NULL,
            requester TEXT NOT NULL,
            phoneext INTEGER NOT NULL,
            datereq TEXT,
            dateneed TEXT,
            orderType TEXT,
            fileAttachments BLOB,
            itemDescription TEXT,
            justification TEXT,
            addComments TEXT,
            trainNotAval TEXT,
            needsNotMeet TEXT,
            budgetObjCode TEXT,
            fund TEXT,
            priceEach REAL,
            totalPrice REAL,
            location TEXT,
            quantity INTEGER,
            new_request BOOLEAN,
            approved BOOLEAN
        )
        """
        self._execute_query(query) # Internal use method
        
    #####################################################################################
    ## CREATE APPROVALS TABLE
    def create_approvals_table(self):
        # Create approvals table if not already existing
        query = """
        CREATE TABLE IF NOT EXISTS approvals (
            req_id INTEGER PRIMARY KEY NOT NULL,
            requester TEXT NOT NULL,
            budgetObjCode TEXT,
            fund TEXT,
            quantity INTEGER,
            totalPrice REAL,
            priceEach REAL,
            location TEXT,
            status TEXT,
            FOREIGN KEY (req_id) REFERENCES purchase_requests(req_id)
                ON UPDATE CASCADE
        )
        """
        self._execute_query(query)
        
    #####################################################################################
    ## INSERT DATA
    def insert_data(self, processed_data, table):
        # Insert data into specified table
        
        # Ensure data is a dictionary
        if not processed_data or not isinstance(processed_data, dict):
            raise ValueError("Processed data must be a non-empty dictionary")
        
        # Convert list-type values to str
        for key, value in processed_data.items():
            if isinstance(value, list):
                processed_data[key] = json.dumps(value)
                
        columns = ", ".join(processed_data.keys())
        placeholders = ", ".join(["?"] * len(processed_data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        self._execute_query(query, list(processed_data.values()))
        
    #####################################################################################
    ## UPDATE DATA
    def update_data(self, data, table, condition):
        # Update data in table based on where condition
        
        # Ensure data is non-empty dictionary
        if not data or not isinstance(data, dict):
            raise ValueError("Data must be a non-empty dictionary")
        
        if not condition:
            raise ValueError("A WHERE condition is required to update table")
        
        set_clause = ", ".join([f"{column} = ?" for column in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {condition}"
        
        self._execute_query(query, list(data.values()))
    
    #####################################################################################
    ## FETCH ROWS
    def fetch_rows(self, query):
        # Fetch all rows from specified table
        
        connection = self.get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        
        except sqlite3.Error as e:
            print(f"Error fetching rows: {e}")
            return []
        
        finally:
            connection.close()
            
    #####################################################################################
    ## EXECUTE QUERY (internal function)
    def _execute_query(self, query, params=None):
        # Exec query with optional parameters
        connection = self.get_connection()
        try:
            with connection:
                cursor = connection.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
        
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        
        finally:
            connection.close()