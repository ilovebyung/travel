import sqlite3
import os
import streamlit as st
from datetime import date, datetime
from contextlib import contextmanager

# --- Configuration ---
DATABASE_FILE = "travel.database"
# Tables using the simple (Name, status) structure
GENERIC_TABLES = ["Product", "Vendor", "Flight", "Pickup"]
# All tables managed by the app
ALL_TABLES = GENERIC_TABLES + ["Customer", "Travel"]

# --- Database Utilities ---

@contextmanager
def get_db_connection():
    """Provides a connection to the SQLite database using a context manager."""
    try:
        # Check if the database file exists to decide on logging for initialization
        is_new_db = not os.path.exists(DATABASE_FILE)
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row  # Access columns by name
        conn.execute('PRAGMA journal_mode=WAL;')
        if is_new_db:
             st.toast(f"Creating new database: {DATABASE_FILE}", icon="💾")
        yield conn
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        # Re-raise the exception to stop execution in case of a critical error
        raise
    finally:
        conn.close()


def init_db():
    """Initializes the database and creates all necessary tables."""
    
    # 1. Create Generic Tables (Product, Vendor, Flight, Pickup)
    for table_name in GENERIC_TABLES:
        column_name = table_name
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {column_name} TEXT NOT NULL PRIMARY KEY,
            status INTEGER DEFAULT 1
        );
        """
        try:
            with get_db_connection() as conn:
                conn.execute(create_table_query)
                conn.commit()
        except Exception as e:
            st.error(f"Failed to create table '{table_name}'. Error: {e}")

    # 2. Create Specific Customer Table
    customer_table_query = """
    CREATE TABLE IF NOT EXISTS Customer (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name  TEXT,
        middle_name  TEXT,
        last_name  TEXT,
        hangul_name  TEXT,
        sex  TEXT,
        date_of_birth TEXT,
        credit_card TEXT,
        credit_card_date TEXT
    );
    """
    try:
        with get_db_connection() as conn:
            conn.execute(customer_table_query)
            conn.commit()
    except Exception as e:
        st.error(f"Failed to create Customer table. Error: {e}")

    # 3. Create Travel Table
    travel_table_query = """
    CREATE TABLE IF NOT EXISTS Travel (
        travel_id INTEGER PRIMARY KEY AUTOINCREMENT,
        Product TEXT,
        Vendor TEXT,
        Customer TEXT, -- Stores the full customer name string (first_name + last_name)
        Flight TEXT,
        Pickup TEXT,
        pickup_time TEXT,	-- ISO 8601 format ('YYYY-MM-DD HH:MM:SS')
        confirmation_code TEXT UNIQUE,
        airfair_IB TEXT,
        airfair_OB TEXT,
        time_IB TEXT,	-- ISO 8601 format ('YYYY-MM-DD HH:MM:SS')
        time_OB TEXT,	-- ISO 8601 format ('YYYY-MM-DD HH:MM:SS')
        deposite INTEGER DEFAULT 0,
        payment INTEGER DEFAULT 0,
        event_expense INTEGER DEFAULT 0,
        special_request TEXT
        -- FOREIGN KEY constraints are omitted as they are not enforced on TEXT references in SQLite without explicit indexing
    );
    """
    try:
        with get_db_connection() as conn:
            conn.execute(travel_table_query)
            conn.commit()
    except Exception as e:
        st.error(f"Failed to create Travel table. Error: {e}")


def remove_duplicates(db_path, table_name, columns):
    """
    Removes duplicate rows from a SQLite table based on specified columns.

    Parameters:
    - db_path: path to the SQLite database file
    - table_name: name of the table to clean
    - columns: list of column names to check for duplicates
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Build the GROUP BY clause
    group_by_clause = ", ".join(columns)

    # Construct and execute the DELETE query
    query = f"""
    DELETE FROM {table_name}
    WHERE rowid NOT IN (
        SELECT MIN(rowid)
        FROM {table_name}
        GROUP BY {group_by_clause}
    );
    """
    cursor.execute(query)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    db_path = "/home/byungsoo/Documents/travel/utils/travel.database"
    table_name = "Customer"
    columns = ["first_name", "last_name", "hangul_name"]
    remove_duplicates(DATABASE_FILE, table_name, columns)