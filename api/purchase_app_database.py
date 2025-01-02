import sqlite3

# Connect to the database
con = sqlite3.connect("./db/purchases.db")
cursor = connection.cursor()

# SQLLITE 3 DATABASE CREATION 
cursor.execute("""
    CREATE TABLE IF NOT EXISTS purchase_requests (
               id INTEGER PRIMARY KEY,
               requester TEXT NOT NULL
               )

""")
