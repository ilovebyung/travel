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
    st.header("Add New Pickup")
    Pickup_name = st.text_input("Pickup Name", key="add_Pickup_name")
    notes = st.text_area("Notes", key="add_notes")
    status = st.selectbox("Status", [1, 0], format_func=lambda x: "Active" if x == 1 else "Inactive", key="add_status")

    if st.button("Add Pickup"):
        if Pickup_name:
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO Pickup (Pickup, Notes, status) VALUES (?, ?, ?)",
                        (Pickup_name, notes, status))
                    conn.commit()
                    st.success(f"Pickup '{Pickup_name}' added successfully!")
                    # Clear inputs after success
                    st.session_state.add_Pickup_name = ""
                    st.session_state.add_notes = ""
            except Exception as e:
                st.error(f"Database connection error: {e}")

# --- TAB 2: Edit Pickup (Using unique keys) ---
with tab2:
    st.header("Edit Existing Pickup")
    Pickups = None

    # Fetch Pickup list
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT rowid, Pickup FROM Pickup")
            Pickups = cursor.fetchall()
    except Exception as e:
        st.error(f"Database error when loading Pickups: {e}")
            
    if Pickups:
        selected = st.selectbox("Select Pickup to Edit", Pickups, 
                                format_func=lambda x: x[1], 
                                key="Pickup_select")
        rowid = selected[0]
        
        Pickup_data = None
        # Fetch data for selected Pickup
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT Pickup, Notes, status FROM Pickup WHERE rowid = ?", (rowid,))
                Pickup_data = cursor.fetchone()
        except Exception as e:
            st.error(f"Database error when fetching details: {e}")
        
        if Pickup_data:
            new_name = st.text_input("Pickup Name", value=Pickup_data[0], key="edit_name")
            new_notes = st.text_area("Notes", value=Pickup_data[1], key="edit_notes")
            
            new_status = st.selectbox("Status", [1, 0], 
                                      index=0 if Pickup_data[2] == 1 else 1,
                                      format_func=lambda x: "Active" if x == 1 else "Inactive",
                                      key="edit_status")

            # Update operation
            if st.button("Update Pickup"):
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("UPDATE Pickup SET Pickup = ?, Notes = ?, status = ? WHERE rowid = ?",
                                       (new_name, new_notes, new_status, rowid))
                        conn.commit()
                        st.success(f"Pickup '{new_name}' updated successfully!")
                        # Note: st.rerun() could be used here to refresh the UI
                except Exception as e:
                    st.error(f"Database error during update: {e}")
    else:
        st.info("No Pickups available to edit.")

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