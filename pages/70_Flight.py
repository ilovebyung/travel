import streamlit as st
import pandas as pd
from utils.database import get_db_connection
from utils.style import load_css  

# Set page config
st.set_page_config(page_title="Data Entry", page_icon="⌨️", layout="wide")
load_css()
st.header("🗂️ Flight Management")

# --- TABS DEFINITION ---
tab1, tab2, tab3 = st.tabs(["➕ Add New Flight", "✏️ Edit Flight", "👀 Display Flight"])

# --- TAB 1: Input Flight (Unchanged) ---
with tab1:
    st.header("Add New Flight")
    Flight_name = st.text_input("Flight Name", key="add_Flight_name")
    notes = st.text_area("Notes", key="add_notes")
    status = st.selectbox("Status", [1, 0], format_func=lambda x: "Active" if x == 1 else "Inactive", key="add_status")

    if st.button("Add Flight"):
        if Flight_name:
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO Flight (Flight, Notes, status) VALUES (?, ?, ?)",
                        (Flight_name, notes, status))
                    conn.commit()
                    st.success(f"Flight '{Flight_name}' added successfully!")
                    # Clear inputs after success
                    st.session_state.add_Flight_name = ""
                    st.session_state.add_notes = ""
            except Exception as e:
                st.error(f"Database connection error: {e}")

# --- TAB 2: Edit Flight (Using unique keys) ---
with tab2:
    st.header("Edit Existing Flight")
    Flights = None

    # Fetch Flight list
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT rowid, Flight FROM Flight")
            Flights = cursor.fetchall()
    except Exception as e:
        st.error(f"Database error when loading Flights: {e}")
            
    if Flights:
        selected = st.selectbox("Select Flight to Edit", Flights, 
                                format_func=lambda x: x[1], 
                                key="Flight_select")
        rowid = selected[0]
        
        Flight_data = None
        # Fetch data for selected Flight
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT Flight, Notes, status FROM Flight WHERE rowid = ?", (rowid,))
                Flight_data = cursor.fetchone()
        except Exception as e:
            st.error(f"Database error when fetching details: {e}")
        
        if Flight_data:
            new_name = st.text_input("Flight Name", value=Flight_data[0], key="edit_name")
            new_notes = st.text_area("Notes", value=Flight_data[1], key="edit_notes")
            
            new_status = st.selectbox("Status", [1, 0], 
                                      index=0 if Flight_data[2] == 1 else 1,
                                      format_func=lambda x: "Active" if x == 1 else "Inactive",
                                      key="edit_status")

            # Update operation
            if st.button("Update Flight"):
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("UPDATE Flight SET Flight = ?, Notes = ?, status = ? WHERE rowid = ?",
                                       (new_name, new_notes, new_status, rowid))
                        conn.commit()
                        st.success(f"Flight '{new_name}' updated successfully!")
                        # Note: st.rerun() could be used here to refresh the UI
                except Exception as e:
                    st.error(f"Database error during update: {e}")
    else:
        st.info("No Flights available to edit.")

# --- TAB 3: Display Flight (NEW) ---
with tab3:
    st.header("All Flights List")
    
    def fetch_all_Flights():
        try:
            with get_db_connection() as conn:
                # Select rowid to serve as a unique ID/index
                df = pd.read_sql_query("SELECT rowid, Flight, Notes, status FROM Flight", conn)
            # Map the 'status' column from 1/0 to Active/Inactive for display
            df['status'] = df['status'].map({1: 'Active', 0: 'Inactive'})
            df.rename(columns={'rowid': 'ID', 'Flight': 'Flight Name'}, inplace=True)
            return df
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            return pd.DataFrame() # Return empty DataFrame on error

    df_Flights = fetch_all_Flights()

    if not df_Flights.empty:
        st.dataframe(
            df_Flights, 
            hide_index=True,
            width='stretch'
        )
        st.caption(f"Total Flights: **{len(df_Flights)}**")
    else:
        st.info("No Flights found in the database.")