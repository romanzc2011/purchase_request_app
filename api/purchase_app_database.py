import sqlite3
import os


# Get database connection
def getDBConnection(db):
    connection = sqlite3.connect(db)
    connection.row_factory = sqlite3.Row
    return connection
    
# Will only create if not present
def createDB(connection):
    
    # SQLLITE 3 DATABASE CREATION 
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_requests (
                id INTEGER PRIMARY KEY NOT NULL,
                requester TEXT NOT NULL,
                phone_ext INTEGER NOT NULL,
                date_request TEXT,
                date_needed TEXT,
                order_type TEXT,
                file_attachments BLOB,
                item_description TEXT,
                justification TEXT,
                addition_comments TEXT,
                training_not_aval TEXT,
                needs_not_meet TEXT,
                budget_obj_code TEXT,
                fund TEXT,
                price REAL,
                location TEXT,
                quantity INTEGER,
                )
    """)

    connection.commit()
    connection.close()

# Function for inserting purchase request data into database
def insertPurchaseReq(id, requester, phone_ext, date_request, date_needed, order_type, 
                      file_attachments, item_desc, justification, addition_comments, 
                      training_not_aval, needs_not_meet, budget_obj_code, fund, price, location, quantity):
    connection = getDBConnection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
        INSERT INTO purchase_requests               
        (id, requester, phone_ext, date_request, date_needed, order_type, 
                      file_attachments, item_desc, justification, addition_comments, 
                      training_not_aval, needs_not_meet, budget_obj_code, fund, price, location, quantity)
        VALUES
        (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)        
        """, (id, requester, phone_ext, date_request, date_needed, order_type, 
                      file_attachments, item_desc, justification, addition_comments, 
                      training_not_aval, needs_not_meet, budget_obj_code, fund, price, location, quantity))
        connection.commit()
        print("Purchase request inserted successfully")
    except sqlite3.Error as e:
        print("Error inserting purchase request: ", e)
    finally:
        connection.close()