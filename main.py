import streamlit as st
import sqlite3
import pandas as pd
import datetime
from utils.database import get_db_connection, DATABASE_FILE, GENERIC_TABLES, ALL_TABLES


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
            cursor = conn.execute("SELECT first_name, last_name FROM Customer ORDER BY customer_id ASC")
            # Create "First Name Last Name" string for dropdown display and storage in Travel table
            names = [f"{row['first_name']} {row['last_name']}" for row in cursor.fetchall()]
            return ["Select..."] + names
    except Exception:
        return ["Select..."]


# --- Generic Table CRUD (Product, Vendor, Flight, Pickup) ---

def get_all_items(table_name):
    """Fetches all items from a given generic table."""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute(f"SELECT * FROM {table_name} ORDER BY status DESC, {table_name} ASC")
            # Convert results to a pandas DataFrame for easy Streamlit display
            df = pd.DataFrame(cursor.fetchall(), columns=[col[0] for col in cursor.description])
            
            # FIX: Ensure 'status' column is a clean integer. This handles unexpected byte strings 
            # or non-numeric data returned by SQLite by coercing errors to NaN, filling with 
            # the default active status (1), and then safely converting to integer.
            if 'status' in df.columns:
                df['status'] = pd.to_numeric(df['status'], errors='coerce').fillna(1).astype(int)
            
            # Add a user-friendly Status Description column
            df['Status'] = df['status'].apply(lambda x: 'Active' if x == 1 else 'Inactive')
            
            return df.rename(columns={table_name: 'Name', 'status': 'status_code'})
    except sqlite3.OperationalError:
        # Table might not exist yet during initial run
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching data from {table_name}: {e}")
        return pd.DataFrame()

def add_item(table_name, item_value):
    """Inserts a new item into the specified generic table."""
    column_name = table_name
    try:
        with get_db_connection() as conn:
            conn.execute(f"INSERT INTO {table_name} ({column_name}) VALUES (?)", (item_value,))
            conn.commit()
            st.success(f"Added new {table_name}: **{item_value}**")
    except sqlite3.IntegrityError:
        st.warning(f"Error: {item_value} already exists in {table_name}.")
    except Exception as e:
        st.error(f"Failed to add {table_name}. Error: {e}")

def update_item_status(table_name, item_value, new_status):
    """Updates the status of an item in the specified generic table."""
    column_name = table_name
    try:
        with get_db_connection() as conn:
            conn.execute(
                f"UPDATE {table_name} SET status = ? WHERE {column_name} = ?",
                (new_status, item_value)
            )
            conn.commit()
            status_text = "Active" if new_status == 1 else "Inactive"
            st.success(f"Status of **{item_value}** updated to **{status_text}**.")
    except Exception as e:
        st.error(f"Failed to update status. Error: {e}")


# --- Customer Table CRUD ---

def add_customer(data):
    """Inserts a new customer into the Customer table."""
    try:
        with get_db_connection() as conn:
            query = """
            INSERT INTO Customer (
                first_name, middle_name, last_name, hangul_name, sex, 
                date_of_birth, credit_card, credit_card_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            conn.execute(query, (
                data['first_name'], data['middle_name'], data['last_name'], 
                data['hangul_name'], data['sex'], data['date_of_birth'], 
                data['credit_card'], data['credit_card_date']
            ))
            conn.commit()
            st.success(f"Customer **{data['first_name']} {data['last_name']}** registered successfully!")
    except Exception as e:
        st.error(f"Failed to add customer. Error: {e}")

def get_all_customers():
    """Fetches all customer records, excluding the ID for display and masking sensitive data."""
    try:
        with get_db_connection() as conn:
            # Select all columns
            cursor = conn.execute(f"SELECT * FROM Customer ORDER BY customer_id DESC")
            df = pd.DataFrame(cursor.fetchall(), columns=[col[0] for col in cursor.description])
            
            if not df.empty:
                # Rename columns for user interface
                df = df.rename(columns={
                    'first_name': 'First Name', 'middle_name': 'Middle Name', 'last_name': 'Last Name',
                    'hangul_name': 'Hangul Name', 'sex':'Gender',
                    'date_of_birth': 'Date of Birth', 'credit_card': 'Credit Card', 
                    'credit_card_date': 'CC Exp Date'
                })
                # Drop internal ID column as requested
                # df = df.drop(columns=['customer_id'])
                
                # Mask sensitive data (Credit Card)
                # def mask_cc(cc):
                #     cc_str = str(cc).strip()
                #     if len(cc_str) > 4:
                #         return '**** **** **** ' + cc_str[-4:]
                #     return cc_str if cc_str else "N/A"

                # df['Credit Card'] = df['Credit Card'].apply(mask_cc)
                
            return df
    except sqlite3.OperationalError:
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching customer data: {e}")
        return pd.DataFrame()


# --- Travel Table CRUD ---

def add_travel_entry(data):
    """Inserts a new travel entry."""
    try:
        with get_db_connection() as conn:
            query = """
            INSERT INTO Travel (
                Product, Vendor, Customer, Flight, Pickup, pickup_time, 
                confirmation_code, airfair_IB, airfair_OB, time_IB, time_OB, 
                deposite, payment, event_expense, special_request
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            conn.execute(query, (
                data['Product'], data['Vendor'], data['Customer'], data['Flight'], data['Pickup'],
                data['pickup_time'], data['confirmation_code'], data['airfair_IB'], data['airfair_OB'],
                data['time_IB'], data['time_OB'], data['deposite'], data['payment'], 
                data['event_expense'], data['special_request']
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


# --- Streamlit UI Components ---

def manage_table(table_name, icon):
    """
    Renders the UI for managing a single generic table (Add, View, Update Status).
    """
    st.header(f"{icon} Manage {table_name}s", divider='gray')
    
    # --- 1. Add New Item Form ---
    with st.expander(f"➕ Add New {table_name}", expanded=False):
        with st.form(key=f'add_form_{table_name}'):
            new_item_value = st.text_input(f"{table_name} Name", max_chars=100, key=f'input_{table_name}')
            submit_button = st.form_submit_button(label=f'Save {table_name}')
            
            if submit_button and new_item_value:
                add_item(table_name, new_item_value.strip())
                st.rerun() # Rerun to refresh the list instantly

    st.subheader(f"Current {table_name} List")

    # --- 2. View All Items ---
    df = get_all_items(table_name)

    if df.empty:
        st.info(f"No {table_name}s found in the database yet. Add one above!")
    else:
        # Prepare data for display and editing
        df_display = df[['Name', 'Status']].copy()
        df_display['Action'] = False # Placeholder for a toggle/button

        # Display the data editor
        edited_df = st.dataframe(
            df_display,
            key=f'editor_{table_name}',
            column_config={
                "Name": st.column_config.TextColumn("Name", disabled=True),
                "Status": st.column_config.TextColumn("Status", disabled=True),
                "Action": st.column_config.CheckboxColumn(
                    "Toggle Status",
                    help="Check to **Deactivate**, uncheck to **Activate**.",
                    default=False,
                    width='small'
                )
            },
            hide_index=True,
            width='stretch'
        )

        # --- 3. Status Update Logic ---
        # Check if the 'Action' column (the toggle checkbox) was modified
        if st.session_state.get(f'editor_{table_name}', {}).get('edited_rows'):
            
            edited_rows = st.session_state[f'editor_{table_name}']['edited_rows']

            # Find the row(s) that were modified
            for index, edits in edited_rows.items():
                if 'Action' in edits:
                    item_name = df.iloc[index]['Name']
                    
                    # Explicitly cast the status code to an integer to resolve the TypeError.
                    try:
                        current_status_code = int(df.iloc[index]['status_code'])
                    except (TypeError, ValueError):
                        # Safely default to 1 (Active) if conversion fails
                        st.error(f"Error: Could not determine status for '{item_name}'. Defaulting to Active (1).")
                        current_status_code = 1 
                    
                    # New status is the opposite of the current status code (1 -> 0, 0 -> 1)
                    new_status = 1 - current_status_code 
                    
                    st.toast(f"Processing status change for {item_name}...", icon="🔄")
                    update_item_status(table_name, item_name, new_status)
                    
                    # Clear the edited state and rerun to reflect changes
                    del st.session_state[f'editor_{table_name}']
                    st.rerun()
                    
def manage_customer_dashboard():
    """Renders the UI for managing the Customer table."""
    st.header("👤 Manage Customers", divider='blue')

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
            st.subheader("Payment Information (Optional)")
            col6, col7 = st.columns(2)
            with col6:
                # Store full CC number, but advise user that only last 4 are shown in the display
                credit_card = st.text_input("Credit Card Number", max_chars=16, help="Full number stored but masked on display.")
            with col7:
                credit_card_date = st.text_input("CC Expiration Date (MM/YY)", max_chars=5, placeholder="e.g., 12/26")
                
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
                        'credit_card_date': credit_card_date.strip() or None
                    }
                    add_customer(customer_data)
                    st.rerun()

    st.subheader("Registered Customers")

    # --- 2. View All Customers ---
    df_customers = get_all_customers()

    if df_customers.empty:
        st.info("No customers registered yet.")
    else:
        # Display customers in a static dataframe
        st.dataframe(df_customers, width='stretch')


def manage_travel_dashboard():
    """Renders the UI for managing the Travel table."""
    st.header("🧳 Travel Management Dashboard", divider='green')

    # Fetch lookup data
    product_options = get_lookup_data("Product")
    vendor_options = get_lookup_data("Vendor")
    customer_options = get_customer_names_for_lookup()
    flight_options = get_lookup_data("Flight")
    pickup_options = get_lookup_data("Pickup")

    # --- 1. Add New Travel Entry Form ---
    with st.expander("➕ Add New Travel Entry", expanded=True):
        with st.form(key='add_travel_form'):
            
            st.subheader("Booking Details")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                confirmation_code = st.text_input("Confirmation Code *", max_chars=50)
            with col2:
                # Use customer name as the link value
                selected_customer = st.selectbox("Customer *", options=customer_options)
            with col3:
                selected_product = st.selectbox("Product", options=product_options)
            with col4:
                selected_vendor = st.selectbox("Vendor", options=vendor_options)

            st.markdown("---")
            st.subheader("Flight & Pickup Details")
            
            # Flight Times
            st.caption("Flight Times (Optional)")
            col_flight, col_ib_date, col_ib_time, col_ob_date, col_ob_time = st.columns(5)

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
            col_pu_select, col_pu_date, col_pu_time, col_special_request = st.columns(4)
            with col_pu_select:
                selected_pickup = st.selectbox("Pickup Location", options=pickup_options)
            with col_pu_date:
                pickup_date = st.date_input("Pickup Date", value=None)
            with col_pu_time:
                pickup_time = st.time_input("Pickup Time", value=None, step=600)
            with col_special_request:
                special_request = st.text_area("Special Request", max_chars=200)



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
                if not confirmation_code or selected_customer == "Select...":
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
                        'special_request': special_request.strip() or None,
                    }
                    add_travel_entry(travel_data)
                    st.rerun()

    st.subheader("All Travel Entries")

    # --- 2. View All Travel Entries ---
    df_travels = get_all_travels()
    df_travels = df_travels[1:] # Hide the travel_id column

    if df_travels.empty:
        st.info("No travel entries registered yet.")
    else:
        # Display travel entries
        st.dataframe(df_travels, width='stretch')


# --- Main Application ---

def main():
    """Main function for the Streamlit application."""
    st.set_page_config(
        page_title="Travel Data Manager",
        page_icon="✈️",
        layout="wide"
    )

    # 1. Initialize Database and Tables  
    # init_db() 
    # 2. Define tabs and icons
    tab_names = ["Travel", "Customer"] + GENERIC_TABLES
    tab_icons = {
        "Travel": "🧳",
        "Customer": "👤",
        "Product": "🗂️", 
        "Vendor": "💼", 
        "Flight": "✈️", 
        "Pickup": "🚐"
    }

    # 3. Create tabs
    tabs = st.tabs([f"{tab_icons[name]} {name}" for name in tab_names])

    # 4. Render UI for each tab
    for i, tab in enumerate(tabs):
        table_name = tab_names[i]
        icon = tab_icons[table_name]
        with tab:
            if table_name == "Travel":
                manage_travel_dashboard()
            elif table_name == "Customer":
                manage_customer_dashboard()
            else:
                # Use the generic management function for Product, Vendor, Flight, Pickup
                manage_table(table_name, icon)

if __name__ == "__main__":
    main()
