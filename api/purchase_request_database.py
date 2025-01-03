import json
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "db", "purchase_requests.db")

# Get database connection
def getDBConnection(db):
    connection = sqlite3.connect(db)
    connection.row_factory = sqlite3.Row
    return connection
    
# Will only create if not present
def createDB(connection):
    
    # SQLLITE 3 DATABASE CREATION
    cursor = connection.cursor() 
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_requests (
                id INTEGER PRIMARY KEY NOT NULL,
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
                price REAL,
                location TEXT,
                quantity INTEGER
                )
    """)
    connection.commit()

# Function for inserting purchase request data into database
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
        
        # Establish database connection
        connection = getDBConnection(db_path)
        createDB(connection)
        
        with connection:
            cursor = connection.cursor()
            cursor.execute(query, values)
        
    except sqlite3.Error as e:
        print("Error inserting purchase request: ", e)
        
    finally:
        connection.commit()
        connection.close()
        print("Purchase request added successfully...")
        
def fetch_all_rows(db_path):
        connection = getDBConnection(db_path)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        
        # Execute SELECT * query to fetch all rows from the table
        query = "SELECT * FROM purchase_requests"
        cursor.execute(query)
        
        # fetch all rows
        rows = cursor.fetchall()
        
        column_names = [description[0] for description in cursor.description]
        print("Columns:", column_names)
        print("Rows:")
        for row in rows:
            print(dict(row))