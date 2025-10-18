import streamlit as st
import pandas as pd
import sqlite3
from utils.style import load_css  

# Set page config
st.set_page_config(page_title="Data Entry", page_icon="⌨️", layout="wide")
load_css()
st.header("🗂️ Pickup Management")

# Connect with type detection enabled
def get_db_connection():
    # Make sure 'travel.database' exists or will be created
    conn = sqlite3.connect('travel.database', detect_types=sqlite3.PARSE_DECLTYPES)
    conn.execute('PRAGMA journal_mode=WAL;')
    return conn

# --- TABS DEFINITION ---
tab1, tab2, tab3 = st.tabs(["➕ Add New Pickup", "✏️ Edit Pickup", "👀 Display Pickup"])

# --- TAB 1: Input Pickup (Unchanged) ---
with tab1:
# Input widgets
    Pickup_name = st.text_input("Pickup Name", key="add_Pickup_name")
    notes = st.text_area("Notes", key="add_notes")
    status = st.selectbox(
        "Status", [1, 0],
        format_func=lambda x: "Active" if x == 1 else "Inactive",
        key="add_status"
    )

    # Add Pickup button
    if st.button("Add Pickup"):
        if Pickup_name:
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO Pickup (Pickup, Notes, status) VALUES (?, ?, ?)",
                        (Pickup_name, notes, status)
                    )
                    conn.commit()
                    st.success(f"Pickup '{Pickup_name}' added successfully!")

                    # Clear inputs by resetting session state and rerunning
                    for key in ["add_Pickup_name", "add_notes"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()

            except Exception as e:
                st.error(f"Database connection error: {e}")

# --- TAB 2: Edit Pickup (Using unique keys) ---
with tab2:
    # Fetch Pickup list
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT rowid, Pickup FROM Pickup")
            Pickups = cursor.fetchall()
    except Exception as e:
        st.error(f"Database error when loading Pickups: {e}")
        Pickups = []

    if Pickups:
        selected = st.selectbox(
            "Select Pickup to Edit",
            Pickups,
            format_func=lambda x: x[1],
            key="Pickup_select"
        )

        rowid = selected[0]

        # Fetch Pickup details when selection changes
        if "last_selected" not in st.session_state or st.session_state.last_selected != rowid:
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT Pickup, Notes, status FROM Pickup WHERE rowid = ?", (rowid,))
                    pickup_data = cursor.fetchone()
                    if pickup_data:
                        st.session_state.edit_name = pickup_data[0]
                        st.session_state.edit_notes = pickup_data[1]
                        st.session_state.edit_status = pickup_data[2]
                        st.session_state.last_selected = rowid
            except Exception as e:
                st.error(f"Database error when fetching details: {e}")

        # Editable fields
        new_name = st.text_input("Pickup Name", value=st.session_state.get("edit_name", ""), key="edit_name")
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
            if st.button("Update Pickup"):
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE Pickup SET Pickup = ?, Notes = ?, status = ? WHERE rowid = ?",
                            (new_name, new_notes, new_status, rowid)
                        )
                        conn.commit()
                        st.success(f"Pickup '{new_name}' updated successfully!")
                        st.session_state.last_selected = None
                        st.rerun()
                except Exception as e:
                    st.error(f"Database error during update: {e}")

        with col2:
            if st.button("Delete Pickup"):
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM Pickup WHERE rowid = ?", (rowid,))
                        conn.commit()
                        st.success(f"Pickup '{new_name}' deleted successfully!")
                        st.session_state.last_selected = None
                        st.rerun()
                except Exception as e:
                    st.error(f"Database error during deletion: {e}")
    else:
        st.info("No Clients available to edit.")

# --- TAB 3: Display Pickup (NEW) ---
with tab3:
    st.header("All Pickups List")
    
    def fetch_all_Pickups():
        try:
            with get_db_connection() as conn:
                # Select rowid to serve as a unique ID/index
                df = pd.read_sql_query("SELECT rowid, Pickup, Notes, status FROM Pickup", conn)
            # Map the 'status' column from 1/0 to Active/Inactive for display
            df['status'] = df['status'].map({1: 'Active', 0: 'Inactive'})
            df.rename(columns={'rowid': 'ID', 'Pickup': 'Pickup Name'}, inplace=True)
            return df
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            return pd.DataFrame() # Return empty DataFrame on error

    df_Pickups = fetch_all_Pickups()

    if not df_Pickups.empty:
        st.dataframe(
            df_Pickups, 
            hide_index=True,
            width='stretch'
        )
        st.caption(f"Total Pickups: **{len(df_Pickups)}**")
    else:
        st.info("No Pickups found in the database.")