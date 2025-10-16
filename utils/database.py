import sqlite3
import streamlit as st
import pandas as pd

# Connect with type detection enabled
def get_db_connection():
    conn = sqlite3.connect('travel.database', detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL;')
    return conn

def get_table_data(table_name):
    try:
        with get_db_connection() as conn:
            df = pd.read_sql_query(f"SELECT * FROM {table_name} ORDER BY {table_name}_id DESC", conn)
            return df
    except Exception as e:
        st.error(f"Error fetching data from Table {table_name}: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error

def update_row(table_name, row_id_col, row_data):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            set_clause = ', '.join([f"{col} = ?" for col in row_data.keys() if col != row_id_col])
            values = [row_data[col] for col in row_data.keys() if col != row_id_col]
            values.append(row_data[row_id_col])
            cursor.execute(f"UPDATE {table_name} SET {set_clause} WHERE {row_id_col} = ?", values)
            conn.commit()
    except Exception as e:
        st.error(f"Error updating row in Table {table_name}: {e}")

def delete_row(table_name, row_id_col, row_id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {table_name} WHERE {row_id_col} = ?", (row_id,))
    except Exception as e:
        st.error(f"Error deleting row in Table {table_name}: {e}")