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
# Input widgets
    Flight_name = st.text_input("Flight Name", key="add_Flight_name")
    notes = st.text_area("Notes", key="add_notes")
    status = st.selectbox(
        "Status", [1, 0],
        format_func=lambda x: "Active" if x == 1 else "Inactive",
        key="add_status"
    )

    # Add Flight button
    if st.button("Add Flight"):
        if Flight_name:
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO Flight (Flight, Notes, status) VALUES (?, ?, ?)",
                        (Flight_name, notes, status)
                    )
                    conn.commit()
                    st.success(f"Flight '{Flight_name}' added successfully!")

                    # Clear inputs by resetting session state and rerunning
                    for key in ["add_Flight_name", "add_notes"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()

            except Exception as e:
                st.error(f"Database connection error: {e}")

# --- TAB 2: Edit Flight (Using unique keys) ---
with tab2:
    # Fetch Flight list
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT rowid, Flight FROM Flight")
            Flights = cursor.fetchall()
    except Exception as e:
        st.error(f"Database error when loading Flights: {e}")
        Flights = []

    if Flights:
        selected = st.selectbox(
            "Select Flight to Edit",
            Flights,
            format_func=lambda x: x[1],
            key="Flight_select"
        )

        rowid = selected[0]

        # Fetch Flight details when selection changes
        if "last_selected" not in st.session_state or st.session_state.last_selected != rowid:
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT Flight, Notes, status FROM Flight WHERE rowid = ?", (rowid,))
                    flight_data = cursor.fetchone()
                    if flight_data:
                        st.session_state.edit_name = flight_data[0]
                        st.session_state.edit_notes = flight_data[1]
                        st.session_state.edit_status = flight_data[2]
                        st.session_state.last_selected = rowid
            except Exception as e:
                st.error(f"Database error when fetching details: {e}")

        # Editable fields
        new_name = st.text_input("Flight Name", value=st.session_state.get("edit_name", ""), key="edit_name")
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
            if st.button("Update Flight"):
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE Flight SET Flight = ?, Notes = ?, status = ? WHERE rowid = ?",
                            (new_name, new_notes, new_status, rowid)
                        )
                        conn.commit()
                        st.success(f"Flight '{new_name}' updated successfully!")
                        st.session_state.last_selected = None
                        st.rerun()
                except Exception as e:
                    st.error(f"Database error during update: {e}")

        with col2:
            if st.button("Delete Flight"):
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM Flight WHERE rowid = ?", (rowid,))
                        conn.commit()
                        st.success(f"Flight '{new_name}' deleted successfully!")
                        st.session_state.last_selected = None
                        st.rerun()
                except Exception as e:
                    st.error(f"Database error during deletion: {e}")
    else:
        st.info("No Clients available to edit.")

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