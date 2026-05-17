# db_connector.py
# Handles database connection and table creation
# SQLite is used for portability - same SQL logic as Oracle/SAP HANA

import sqlite3
from pathlib import Path

DB_PATH = "treasury_validation.db"
SCHEMA_PATH = "sql/schema.sql"

def get_connection():
    """Open and return a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def initialise_database():
    """
    Create database tables using schema.sql.
    
    Business reason: The schema defines the structure that mirrors
    the source system data model. Running this once ensures the
    database is ready to receive transaction data.
    """
    schema = Path(SCHEMA_PATH).read_text()
    conn = get_connection()
    conn.executescript(schema)
    conn.commit()
    conn.close()
    print(f"Database initialised: {DB_PATH}")

if __name__ == "__main__":
    initialise_database()