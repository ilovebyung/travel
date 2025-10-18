import streamlit as st
import pandas as pd
from utils.database import get_db_connection
from utils.style import load_css  

# Set page config
st.set_page_config(page_title="Data Entry", page_icon="⌨️", layout="wide")
load_css()
st.header("🗂️ Client Management")

# --- TABS DEFINITION ---
tab1, tab2, tab3 = st.tabs(["➕ Add New Client", "✏️ Edit Client", "👀 Display Client"])

# --- TAB 1: Input Client (Unchanged) ---
with tab1:
    st.header("Add New Client")
    Client_name = st.text_input("Client Name", key="add_Client_name")
    notes = st.text_area("Notes", key="add_notes")
    status = st.selectbox("Status", [1, 0], format_func=lambda x: "Active" if x == 1 else "Inactive", key="add_status")

    if st.button("Add Client"):
        if Client_name:
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO Client (Client, Notes, status) VALUES (?, ?, ?)",
                        (Client_name, notes, status))
                    conn.commit()
                    st.success(f"Client '{Client_name}' added successfully!")
                    # Clear inputs after success
                    st.session_state.add_Client_name = ""
                    st.session_state.add_notes = ""
            except Exception as e:
                st.error(f"Database connection error: {e}")

# --- TAB 2: Edit Client (Using unique keys) ---
with tab2:
    st.header("Edit Existing Client")
    Clients = None

    # Fetch Client list
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT rowid, Client FROM Client")
            Clients = cursor.fetchall()
    except Exception as e:
        st.error(f"Database error when loading Clients: {e}")
            
    if Clients:
        selected = st.selectbox("Select Client to Edit", Clients, 
                                format_func=lambda x: x[1], 
                                key="Client_select")
        rowid = selected[0]
        
        Client_data = None
        # Fetch data for selected Client
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT Client, Notes, status FROM Client WHERE rowid = ?", (rowid,))
                Client_data = cursor.fetchone()
        except Exception as e:
            st.error(f"Database error when fetching details: {e}")
        
        if Client_data:
            new_name = st.text_input("Client Name", value=Client_data[0], key="edit_name")
            new_notes = st.text_area("Notes", value=Client_data[1], key="edit_notes")
            
            new_status = st.selectbox("Status", [1, 0], 
                                      index=0 if Client_data[2] == 1 else 1,
                                      format_func=lambda x: "Active" if x == 1 else "Inactive",
                                      key="edit_status")

            # Update operation
            if st.button("Update Client"):
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("UPDATE Client SET Client = ?, Notes = ?, status = ? WHERE rowid = ?",
                                       (new_name, new_notes, new_status, rowid))
                        conn.commit()
                        st.success(f"Client '{new_name}' updated successfully!")
                        # Note: st.rerun() could be used here to refresh the UI
                except Exception as e:
                    st.error(f"Database error during update: {e}")
    else:
        st.info("No Clients available to edit.")

# --- TAB 3: Display Client (NEW) ---
with tab3:
    st.header("All Clients List")
    
    def fetch_all_Clients():
        try:
            with get_db_connection() as conn:
                # Select rowid to serve as a unique ID/index
                df = pd.read_sql_query("SELECT rowid, Client, Notes, status FROM Client", conn)
            # Map the 'status' column from 1/0 to Active/Inactive for display
            df['status'] = df['status'].map({1: 'Active', 0: 'Inactive'})
            df.rename(columns={'rowid': 'ID', 'Client': 'Client Name'}, inplace=True)
            return df
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            return pd.DataFrame() # Return empty DataFrame on error

    df_Clients = fetch_all_Clients()

    if not df_Clients.empty:
        st.dataframe(
            df_Clients, 
            hide_index=True,
            width='stretch'
        )
        st.caption(f"Total Clients: **{len(df_Clients)}**")
    else:
        st.info("No Clients found in the database.")