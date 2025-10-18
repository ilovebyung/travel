import streamlit as st
import sqlite3
import pandas as pd
import datetime
from utils.database import get_db_connection
from utils.style import load_css

# --- Lookup Data Fetching ---
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


# --- Customer Table CRUD ---

def add_customer(data):
    """Inserts a new customer into the Customer table."""
    try:
        with get_db_connection() as conn:
            query = """
            INSERT INTO Customer (
                first_name, middle_name, last_name, hangul_name, sex, 
                date_of_birth, credit_card, credit_card_date, is_representative
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            conn.execute(query, (
                data['first_name'], data['middle_name'], data['last_name'], 
                data['hangul_name'], data['sex'], data['date_of_birth'], 
                data['credit_card'], data['credit_card_date'], data['is_representative']
            ))
            conn.commit()
            st.success(f"Customer **{data['first_name']} {data['last_name']}** registered successfully!")
    except Exception as e:
        st.error(f"Failed to add customer. Error: {e}")

def get_all_customers():
    """Fetches all customer records for display."""
    try:
        with get_db_connection() as conn:
            # Select all columns
            cursor = conn.execute(f"SELECT * FROM Customer WHERE status = 1 ORDER BY customer_id")
            df = pd.DataFrame(cursor.fetchall(), columns=[col[0] for col in cursor.description])
            
            if not df.empty:
                # Rename columns for user interface
                df = df.rename(columns={
                    'first_name': 'First Name', 'middle_name': 'Middle Name', 'last_name': 'Last Name',
                    'hangul_name': 'Hangul Name', 'sex':'Gender',
                    'date_of_birth': 'Date of Birth', 'credit_card': 'Credit Card', 
                    'credit_card_date': 'CC Exp Date'
                })              
            return df
    except sqlite3.OperationalError:
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching customer data: {e}")
        return pd.DataFrame()

# --- Streamlit UI Components ---



st.set_page_config(
    page_title="Customer Management",
    page_icon="✈️",
    layout="wide"
)

load_css()

st.header("👤 Customer Management", divider='blue')

# --- 1. Add New Customer Form ---
with st.expander("➕ Register New Customer", expanded=True):
    with st.form(key='add_customer_form'):
        
        # --- Customer Details ---
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            first_name = st.text_input("First Name *", max_chars=50)
        with col2:
            middle_name = st.text_input("Middle Name", max_chars=50)
        with col3:
            last_name = st.text_input("Last Name *", max_chars=50)
        with col4:               
            hangul_name = st.text_input("Hangul Name (Korean Name)", max_chars=50)
        with col5:
            sex = st.selectbox("Gender *", options=["Select...", "Male", "Female", "Other"])
        with col6:
            # Use a date input and store as ISO string
            dob = st.date_input("Date of Birth *", min_value=pd.to_datetime('1900-01-01').date())

        st.markdown("---")
        # st.subheader("Payment Information ")
        col_a, col_b, col_c, col_d, col_e, col_f = st.columns(6)
        with col_a:
            # Store full CC number, but advise user that only last 4 are shown in the display
            credit_card = st.text_input("Credit Card Number", max_chars=16)
        with col_b:
            credit_card_date = st.text_input("CC Expiration Date (MM/YY)", max_chars=5)
        with col_c:
            representitive = st.checkbox("Is Representitive?")

        submit_button = st.form_submit_button(label='Register Customer')
        
        if submit_button:
            # Basic validation
            if not first_name or not last_name or sex == "Select...":
                st.error("Please fill out all required fields marked with an asterisk (*).")
            else:
                customer_data = {
                    'first_name': first_name.strip(),
                    'middle_name': middle_name.strip(),
                    'last_name': last_name.strip(),
                    'hangul_name': hangul_name.strip(),
                    'sex': sex,
                    'date_of_birth': dob.isoformat(), # Store date as ISO 8601 string
                    'credit_card': credit_card.strip() or None,
                    'credit_card_date': credit_card_date.strip() or None,
                    'is_representative': 1 if representitive else 0
                }
                add_customer(customer_data)
                st.rerun()

st.subheader("Registered Customers")

# --- 2. View All Customers ---
df = get_all_customers()

if df.empty:
    st.info("No customers registered yet.")
else:
    # Reset the index to start from 1
    df.index = df.index + 1
    # Display customers in a static dataframe
    st.dataframe(df, width='stretch')



