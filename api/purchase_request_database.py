import json
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "db", "purchase_requests.db")

###############################################################################################
## GET DATABASE CONNECTION
def getDBConnection(db):
    connection = sqlite3.connect(db)
    connection.execute("PRAGMA foreign_key = ON;")
    connection.row_factory = sqlite3.Row
    return connection
    
###############################################################################################
## CREATE PURCHASE REQ DATABASE
def createPurchaseReqTbl(connection):
    
    # SQLLITE 3 DATABASE CREATION
    cursor = connection.cursor() 
    cursor.execute("""
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
    """)
    connection.commit()
    
###############################################################################################
## CREATE APPROVALS DATABASE
def createApprovalsTbl(connection):
    # Create cursor for DB
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS approvals (
                req_id INTEGER PRIMARY KEY NOT NULL,
                requester TEXT NOT NULL,
                budgetObjCode TEXT,
                fund TEXT,
                estPrice REAL,
                priceEach REAL,
                location TEXT,
                approved_by TEXT,
                approved BOOLEAN,
                FOREIGN KEY (req_id) REFERENCES purchase_requests(req_id)
                    ON UPDATE CASCADE                    
                )
    """)
    connection.commit()

###############################################################################################
## PROCESS DATA


###############################################################################################
## INSERT PURCHASE REQ
def insertPurchaseReq(processed_data):
    # Convert list-type values to strings
    for key, value in processed_data.items():
        if isinstance(value, list): 
            processed_data[key] = json.dumps(value) # Converts to JSON str
    
    # Separate keys and values for dynamic SQL statement
    col_key = [key for key in processed_data.keys()]
    values = [processed_data[key] for key in col_key]
    
    try:
        # Create dynamic SQL statement
        valueholder = ", ".join(["?"] * len(col_key)) # (?,?,?)
        columns = ", ".join(col_key)
        
        query = f"INSERT INTO purchase_requests ({columns}) VALUES ({valueholder})"
        
        print(f"{query}")
        
        # Establish database connection
        connection = getDBConnection(db_path)
        createPurchaseReqTbl(connection)
        
        with connection:
            cursor = connection.cursor()
            cursor.execute(query, values)
        
    except sqlite3.Error as e:
        print("Error inserting into {table}: ", e)
        
    finally:
        connection.commit()
        connection.close()
        print("Purchase request added successfully...")

###############################################################################################
## FETCH ALL ROWS    
def fetch_all_rows(db_path, table):
        connection = getDBConnection(db_path)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        
        # Execute SELECT * query to fetch all rows from the table
        query = f"SELECT * FROM {table}"
        cursor.execute(query)
        
        # fetch all rows
        rows = cursor.fetchall()
        
        column_names = [description[0] for description in cursor.description]
        print("Columns:", column_names)
        print("Rows:")
        for row in rows:
            print(dict(row))