import streamlit as st
import sqlite3
import pandas as pd
import datetime
from utils.database import get_db_connection
from utils.style import load_css

# --- Lookup Data Helpers ---

def get_lookup_data(table_name):
    """Fetches list of active items from a generic table for dropdowns."""
    column_name = table_name
    try:
        with get_db_connection() as conn:
            # Only fetch active items (status = 1)
            cursor = conn.execute(f"SELECT {column_name} FROM {table_name} WHERE status = 1 ORDER BY {column_name} ASC")
            # Prepend a default selection option
            return ["Select..."] + [row[0] for row in cursor.fetchall()]
    except Exception:
        return ["Select..."]

def get_customer_names_for_lookup():
    """Fetches list of customer names (First Name + Last Name) for dropdowns."""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT first_name, last_name FROM Customer WHERE status=1 ORDER BY first_name, last_name")
            # Create "First Name Last Name" string for dropdown display and storage in Travel table
            names = [f"{row['first_name']} {row['last_name']}" for row in cursor.fetchall()]
            return ["Select..."] + names
    except Exception:
        return ["Select..."]

# --- Travel Table CRUD ---

def add_travel_entry(data):
    """Inserts a new travel entry."""
    try:
        with get_db_connection() as conn:
            query = """
            INSERT INTO Travel (
                Product, Vendor, Customer, Flight, Pickup, pickup_time, 
                confirmation_code, airfair_IB, airfair_OB, time_IB, time_OB, 
                deposite, payment, event_expense, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            conn.execute(query, (
                data['Product'], data['Vendor'], data['Customer'], data['Flight'], data['Pickup'],
                data['pickup_time'], data['confirmation_code'], data['airfair_IB'], data['airfair_OB'],
                data['time_IB'], data['time_OB'], data['deposite'], data['payment'], 
                data['event_expense'], data['notes']
            ))
            conn.commit()
            st.success(f"New travel entry confirmed with code: **{data['confirmation_code']}**")
    except sqlite3.IntegrityError:
        st.error(f"Error: Confirmation Code '{data['confirmation_code']}' already exists.")
    except Exception as e:
        st.error(f"Failed to add travel entry. Error: {e}")

def get_all_travels():
    """Fetches all travel records."""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT * FROM Travel ORDER BY travel_id DESC")
            df = pd.DataFrame(cursor.fetchall(), columns=[col[0] for col in cursor.description])
            
            if not df.empty:
                # Drop system ID column
                df = df.drop(columns=['travel_id'])
            
            return df
    except sqlite3.OperationalError:
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching travel data: {e}")
        return pd.DataFrame()


st.set_page_config(
    page_title="Travel Data Manager",
    page_icon="✈️",
    layout="wide"
)

load_css()

st.header("🧳 Travel Management ", divider='green')

# Fetch lookup data
product_options = get_lookup_data("Product")
vendor_options = get_lookup_data("Vendor")
client_options = get_lookup_data("Client")
customer_options = get_customer_names_for_lookup()
flight_options = get_lookup_data("Flight")
pickup_options = get_lookup_data("Pickup")

# --- 1. Add New Travel Entry Form ---
with st.expander("➕ Add New Travel Entry", expanded=True):
    with st.form(key='add_travel_form'):
        
        st.subheader("Booking Details")
        col0, col1, col2, col3, col4 = st.columns(5)
        with col0:
            selected_representitive = st.selectbox("Representitive *", options=customer_options)  
        with col1:
            selected_customer = st.selectbox("Customer *", options=customer_options)               
        with col2:
            selected_product = st.selectbox("Product *", options=product_options)
        with col3:
            selected_client = st.selectbox("Client", options=client_options)
        with col4:
            selected_vendor = st.selectbox("Vendor", options=vendor_options)

        st.markdown("---")
        st.subheader("Flight & Pickup Details")
        
        # Flight Times
        st.caption("Flight Times (Optional)")
        col_confirmation, col_flight, col_ib_date, col_ib_time, col_ob_date, col_ob_time = st.columns(6)

        with col_confirmation:
            confirmation_code = st.text_input("Confirmation Code", max_chars=10)
        with col_flight:
            selected_flight = st.selectbox("Flight Name", options=flight_options)          
        with col_ib_date:
            ib_date = st.date_input("Inbound Date", value=None)
        with col_ib_time:
            ib_time = st.time_input("Inbound Time", value=None)
        with col_ob_date:
            ob_date = st.date_input("Outbound Date", value=None)
        with col_ob_time:
            ob_time = st.time_input("Outbound Time", value=None)
        
        # Pickup Details
        st.markdown("---")
        st.caption("Pickup Details (Optional)")
        col_pu_select, col_pu_date, col_pu_time, col_notes = st.columns(4)
        with col_pu_select:
            selected_pickup = st.selectbox("Pickup Location", options=pickup_options)
        with col_pu_date:
            pickup_date = st.date_input("Pickup Date", value=None)
        with col_pu_time:
            pickup_time = st.time_input("Pickup Time", value=None, step=600)
        with col_notes:
            notes = st.text_area("notes", max_chars=100)



        st.markdown("---")
        st.subheader("Financials & Airfare")
        
        col_fair_ib, col_fair_ob, col_deposite, col_payment, col_expense = st.columns(5)
        with col_fair_ib:
            airfair_IB = st.text_input("Airfare (Inbound)")
        with col_fair_ob:
            airfair_OB = st.text_input("Airfare (Outbound)")

        # col_deposite, col_payment, col_expense = st.columns(3)
        with col_deposite:
            deposite = st.number_input("Deposit (\\$) (Default 0)", min_value=0, value=0, step=10)
        with col_payment:
            payment = st.number_input("Payment (\\$) (Default 0)", min_value=0, value=0, step=10)
        with col_expense:
            event_expense = st.number_input("Event Expense (\\$) (Default 0)", min_value=0, value=0, step=10)
            
        submit_button = st.form_submit_button(label='Save Travel Entry')
        
        if submit_button:
            # Validation
            if not selected_product or selected_customer == "Select...":
                st.error("Please fill out the Confirmation Code and select a Customer.")
            else:
                # Format optional datetime fields to ISO 8601
                time_IB_str = None
                if ib_date and ib_time:
                    time_IB_str = datetime.datetime.combine(ib_date, ib_time).isoformat(' ', 'seconds')
                
                time_OB_str = None
                if ob_date and ob_time:
                    time_OB_str = datetime.datetime.combine(ob_date, ob_time).isoformat(' ', 'seconds')

                pickup_time_str = None
                if pickup_date and pickup_time:
                    pickup_time_str = datetime.datetime.combine(pickup_date, pickup_time).isoformat(' ', 'seconds')

                travel_data = {
                    'Product': selected_product if selected_product != "Select..." else None,
                    'Vendor': selected_vendor if selected_vendor != "Select..." else None,
                    'Client': selected_client if selected_client != "Select..." else None,
                    'Customer': selected_customer, # Full Name string
                    'Flight': selected_flight if selected_flight != "Select..." else None,
                    'Pickup': selected_pickup if selected_pickup != "Select..." else None,
                    'pickup_time': pickup_time_str,
                    'confirmation_code': confirmation_code.strip(),
                    'airfair_IB': airfair_IB.strip() or None,
                    'airfair_OB': airfair_OB.strip() or None,
                    'time_IB': time_IB_str,
                    'time_OB': time_OB_str,
                    'deposite': deposite,
                    'payment': payment,
                    'event_expense': event_expense,
                    'notes': notes.strip() or None,
                }
                add_travel_entry(travel_data)
                st.rerun()

st.subheader("All Travel Entries")

# --- 2. View All Travel Entries ---
df = get_all_travels()
# Reset the index to start from 1
df.index = df.index + 1

if df.empty:
    st.info("No travel entries registered yet.")
else:
    # Display travel entries
    st.dataframe(df, width='stretch')