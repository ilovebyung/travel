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
# Input widgets
    Client_name = st.text_input("Client Name", key="add_Client_name")
    notes = st.text_area("Notes", key="add_notes")
    status = st.selectbox(
        "Status", [1, 0],
        format_func=lambda x: "Active" if x == 1 else "Inactive",
        key="add_status"
    )

    # Add Client button
    if st.button("Add Client"):
        if Client_name:
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO Client (Client, Notes, status) VALUES (?, ?, ?)",
                        (Client_name, notes, status)
                    )
                    conn.commit()
                    st.success(f"Client '{Client_name}' added successfully!")

                    # Clear inputs by resetting session state and rerunning
                    for key in ["add_Client_name", "add_notes"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()

            except Exception as e:
                st.error(f"Database connection error: {e}")

# --- TAB 2: Edit Client (Using unique keys) ---
with tab2:
    # Fetch Client list
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT rowid, Client FROM Client")
            Clients = cursor.fetchall()
    except Exception as e:
        st.error(f"Database error when loading Clients: {e}")
        Clients = []

    if Clients:
        selected = st.selectbox(
            "Select Client to Edit",
            Clients,
            format_func=lambda x: x[1],
            key="Client_select"
        )

        rowid = selected[0]

        # Fetch Client details when selection changes
        if "last_selected" not in st.session_state or st.session_state.last_selected != rowid:
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT Client, Notes, status FROM Client WHERE rowid = ?", (rowid,))
                    client_data = cursor.fetchone()
                    if client_data:
                        st.session_state.edit_name = client_data[0]
                        st.session_state.edit_notes = client_data[1]
                        st.session_state.edit_status = client_data[2]
                        st.session_state.last_selected = rowid
            except Exception as e:
                st.error(f"Database error when fetching details: {e}")

        # Editable fields
        new_name = st.text_input("Client Name", value=st.session_state.get("edit_name", ""), key="edit_name")
        new_notes = st.text_area("Notes", value=st.session_state.get("edit_notes", ""), key="edit_notes")
        new_status = st.selectbox(
            "Status",
            [1, 0],
            index=0 if st.session_state.get("edit_status", 1) == 1 else 1,
            format_func=lambda x: "Active" if x == 1 else "Inactive",
            key="edit_status"
        )

        # Create two columns for buttons
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("Update Client"):
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE Client SET Client = ?, Notes = ?, status = ? WHERE rowid = ?",
                            (new_name, new_notes, new_status, rowid)
                        )
                        conn.commit()
                        st.success(f"Client '{new_name}' updated successfully!")
                        st.session_state.last_selected = None
                        st.rerun()
                except Exception as e:
                    st.error(f"Database error during update: {e}")

        with col2:
            if st.button("Delete Client"):
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM Client WHERE rowid = ?", (rowid,))
                        conn.commit()
                        st.success(f"Client '{new_name}' deleted successfully!")
                        st.session_state.last_selected = None
                        st.rerun()
                except Exception as e:
                    st.error(f"Database error during deletion: {e}")
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