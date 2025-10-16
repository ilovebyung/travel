import streamlit as st
import sqlite3
import pandas as pd
from utils.database import get_db_connection

# Set page config
st.set_page_config(page_title="Transaction History", page_icon="🔎", layout="wide")

# # --- Login Check ---
# if not st.session_state.get('authentication_status'):
#     try:
#         st.switch_page("Home.py")

#     except Exception as e:
#         st.error(e)

st.header("🔎 Transaction History", divider='blue')


try:
    st.subheader("Full Table View")
    with get_db_connection() as conn:
        sql = '''
         SELECT T.travel_id, TH.timestamp, T.Product, T.Vendor, T.Customer, TH.deposite, TH.payment, TH.event_expense
         FROM Travel T, Travel_History TH ON T.travel_id = TH.travel_id
         ORDER BY TH.timestamp DESC'''
        df = pd.read_sql_query(sql, conn)
        st.dataframe(df, width='stretch', height=600)
except sqlite3.OperationalError:
    # Table might not exist yet during initial run
    st.warning(f"Table Travel does not exist.")
except Exception as e:
    st.error(f"Error fetching data from Table Travel: {e}")
    st.warning(f"Row does not exist.")



