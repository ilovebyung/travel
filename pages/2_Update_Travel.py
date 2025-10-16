import streamlit as st
import sqlite3
import pandas as pd
from utils.database import update_row, delete_row, get_table_data  
from utils.style import load_css

# --- Login Check ---
# if not st.session_state.get('authentication_status'):
# # if not st.session_state.get('username') in ['byungsoo','bada','i4u']:
#     try:
#         st.warning("Please log in to access the Travel Data Manager.")
#         st.switch_page("Home.py")

#     except Exception as e:
#         st.error(e)

# Set page config
st.set_page_config(page_title="Travel Management System", page_icon="🧳", layout="wide")
load_css()
st.header("🛠️ Update Travel", divider='green')

df = get_table_data("Travel")

try: 
    col1, col2 = st.columns([1, 3])  # col1 is narrower
    with col1:
        row_index = st.number_input("Select row index to edit", min_value=0, max_value=len(df)-1, step=1)
        row_data = df.iloc[row_index].to_dict()

        row_id_col = [col for col in df.columns if col.endswith("_id")][0]
        edited_data = {}

    # Distribute input fields across 4 columns
    col1, col2, col3, col4 = st.columns(4)

    columns = [col1, col2, col3, col4]
    for i, (col, val) in enumerate(row_data.items()):
        with columns[i % 4]:
            edited_data[col] = st.text_input(f"{col}", str(val))

    # Distribute buttons across 4 columns
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("Update"):
            update_row("Travel", row_id_col, edited_data)
            st.success(f"Row {edited_data[row_id_col]} updated successfully!")
    with col2:
        if st.button("Delete"):
            delete_row("Travel", row_id_col, edited_data[row_id_col])
            st.warning(f"Row {edited_data[row_id_col]} deleted successfully!")



    st.subheader("Full Table View")
    st.dataframe(get_table_data("Travel"), width='stretch')

except sqlite3.OperationalError:
    # Table might not exist yet during initial run
    st.warning(f"Table Travel does not exist.")
except Exception as e:
    st.error(f"Error fetching data from Table Travel: {e}")
    st.warning(f"Row does not exist.")
