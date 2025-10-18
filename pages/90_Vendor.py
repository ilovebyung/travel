import streamlit as st
import pandas as pd
from utils.database import get_db_connection
from utils.style import load_css

# Set page config
st.set_page_config(page_title="Vendor Management", page_icon="⌨️", layout="wide")
load_css()
st.header("🗂️ Vendor Management")

# --- TABS DEFINITION ---
tab1, tab2, tab3 = st.tabs(["➕ Add New Vendor", "✏️ Edit Vendor", "👀 Display Vendor"])

# --- TAB 1: Input Vendor (Unchanged) ---
with tab1:
    st.header("Add New Vendor")
    Vendor_name = st.text_input("Vendor Name", key="add_Vendor_name")
    notes = st.text_area("Notes", key="add_notes")
    status = st.selectbox("Status", [1, 0], format_func=lambda x: "Active" if x == 1 else "Inactive", key="add_status")

    if st.button("Add Vendor"):
        if Vendor_name:
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO Vendor (Vendor, Notes, status) VALUES (?, ?, ?)",
                        (Vendor_name, notes, status))
                    conn.commit()
                    st.success(f"Vendor '{Vendor_name}' added successfully!")
                    # Clear inputs after success
                    st.session_state.add_Vendor_name = ""
                    st.session_state.add_notes = ""
            except Exception as e:
                st.error(f"Database connection error: {e}")

# --- TAB 2: Edit Vendor (Using unique keys) ---
with tab2:
    st.header("Edit Existing Vendor")
    Vendors = None

    # Fetch Vendor list
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT rowid, Vendor FROM Vendor")
            Vendors = cursor.fetchall()
    except Exception as e:
        st.error(f"Database error when loading Vendors: {e}")
            
    if Vendors:
        selected = st.selectbox("Select Vendor to Edit", Vendors, 
                                format_func=lambda x: x[1], 
                                key="Vendor_select")
        rowid = selected[0]
        
        Vendor_data = None
        # Fetch data for selected Vendor
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT Vendor, Notes, status FROM Vendor WHERE rowid = ?", (rowid,))
                Vendor_data = cursor.fetchone()
        except Exception as e:
            st.error(f"Database error when fetching details: {e}")
        
        if Vendor_data:
            new_name = st.text_input("Vendor Name", value=Vendor_data[0], key="edit_name")
            new_notes = st.text_area("Notes", value=Vendor_data[1], key="edit_notes")
            
            new_status = st.selectbox("Status", [1, 0], 
                                      index=0 if Vendor_data[2] == 1 else 1,
                                      format_func=lambda x: "Active" if x == 1 else "Inactive",
                                      key="edit_status")

            # Update operation
            if st.button("Update Vendor"):
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("UPDATE Vendor SET Vendor = ?, Notes = ?, status = ? WHERE rowid = ?",
                                       (new_name, new_notes, new_status, rowid))
                        conn.commit()
                        st.success(f"Vendor '{new_name}' updated successfully!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Database error during update: {e}")
    else:
        st.info("No Vendors available to edit.")

# --- TAB 3: Display Vendor (NEW) ---
with tab3:
    st.header("All Vendors List")
    
    def fetch_all_Vendors():
        try:
            with get_db_connection() as conn:
                # Select rowid to serve as a unique ID/index
                df = pd.read_sql_query("SELECT rowid, Vendor, Notes, status FROM Vendor", conn)
            # Map the 'status' column from 1/0 to Active/Inactive for display
            df['status'] = df['status'].map({1: 'Active', 0: 'Inactive'})
            df.rename(columns={'rowid': 'ID', 'Vendor': 'Vendor Name'}, inplace=True)
            return df
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            return pd.DataFrame() # Return empty DataFrame on error

    df_Vendors = fetch_all_Vendors()

    if not df_Vendors.empty:
        st.dataframe(
            df_Vendors, 
            hide_index=True,
            width='stretch'
        )
        st.caption(f"Total Vendors: **{len(df_Vendors)}**")
    else:
        st.info("No Vendors found in the database.")