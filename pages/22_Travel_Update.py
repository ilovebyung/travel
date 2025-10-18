import streamlit as st
import sqlite3
import pandas as pd
from utils.database import update_row, delete_row, get_table_data  
from utils.style import load_css

# Set page config
st.set_page_config(page_title="Travel Management System", page_icon="🧳", layout="wide")
load_css()

st.header("🛠️ Update Travel", divider='green')

try:
    df = get_table_data("Travel")
    
    if df.empty:
        st.warning("No travel data available.")
    else:
        # Reset the index to start from 1 for display
        display_df = df.copy()
        display_df.index = display_df.index + 1
        
        st.subheader("Travel Data Editor")
        st.info("💡 Edit cells directly in the table below. Changes are highlighted. Click 'Save Changes' to commit updates to the database.")
        
        # Configure column settings for data_editor
        column_config = {
            "travel_id": st.column_config.NumberColumn(
                "Travel ID",
                disabled=True,  # Primary key shouldn't be edited
                help="Unique travel identifier"
            ),
            "Product": st.column_config.TextColumn(
                "Product",
                help="Travel product name"
            ),
            "Vendor": st.column_config.TextColumn(
                "Vendor",
                help="Vendor name"
            ),
            "Customer": st.column_config.TextColumn(
                "Customer",
                help="Customer name"
            ),
            "Flight": st.column_config.TextColumn(
                "Flight",
                help="Flight information"
            ),
            "Pickup": st.column_config.TextColumn(
                "Pickup",
                help="Pickup location"
            ),
            "pickup_time": st.column_config.DatetimeColumn(
                "Pickup Time",
                help="Format: YYYY-MM-DD HH:MM:SS",
                format="YYYY-MM-DD HH:mm:ss"
            ),
            "confirmation_code": st.column_config.TextColumn(
                "Confirmation Code",
                help="Booking confirmation code"
            ),
            "airfair_IB": st.column_config.NumberColumn(
                "Airfare Inbound",
                help="Inbound airfare amount",
                default=0,
                format="$%d"
            ),
            "airfair_OB": st.column_config.NumberColumn(
                "Airfare Outbound",
                help="Outbound airfare amount",
                default=0,
                format="$%d"
            ),
            "time_IB": st.column_config.DatetimeColumn(
                "Time Inbound",
                help="Format: YYYY-MM-DD HH:MM:SS",
                format="YYYY-MM-DD HH:mm:ss"
            ),
            "time_OB": st.column_config.DatetimeColumn(
                "Time Outbound",
                help="Format: YYYY-MM-DD HH:MM:SS",
                format="YYYY-MM-DD HH:mm:ss"
            ),
            "deposite": st.column_config.NumberColumn(
                "Deposit",
                help="Deposit amount",
                default=0,
                format="$%d"
            ),
            "payment": st.column_config.NumberColumn(
                "Payment",
                help="Payment amount",
                default=0,
                format="$%d"
            ),
            "event_expense": st.column_config.NumberColumn(
                "Event Expense",
                help="Event expense amount",
                default=0,
                format="$%d"
            ),
            "Notes": st.column_config.TextColumn(
                "Notes",
                help="Additional notes",
                width="large"
            )
        }
        
        # Use data_editor for inline editing
        edited_df = st.data_editor(
            display_df,
            column_config=column_config,
            width='stretch',
            num_rows="dynamic",  # Allow adding/deleting rows
            key="travel_editor",
            hide_index=False
        )
        
        # Detect changes
        if not df.equals(edited_df.reset_index(drop=True)):
            col1, col2, col3 = st.columns([1, 1, 4])
            
            with col1:
                if st.button("💾 Save Changes", type="primary"):
                    try:
                        # Find modified rows
                        modified_rows = []
                        for idx in edited_df.index:
                            original_idx = idx - 1  # Adjust for display index offset
                            if original_idx < len(df):
                                original_row = df.iloc[original_idx]
                                edited_row = edited_df.iloc[idx - 1]
                                
                                # Check if row was modified
                                if not original_row.equals(edited_row):
                                    modified_rows.append((original_idx, edited_row))
                        
                        # Update modified rows
                        success_count = 0
                        for orig_idx, row in modified_rows:
                            row_dict = row.to_dict()
                            update_row("Travel", "travel_id", row_dict)
                            success_count += 1
                        
                        if success_count > 0:
                            st.success(f"✅ {success_count} row(s) updated successfully!")
                            st.rerun()
                        else:
                            st.info("No changes detected.")
                    
                    except Exception as e:
                        st.error(f"Error saving changes: {e}")
            
            with col2:
                if st.button("🔄 Discard Changes"):
                    st.rerun()
        
        # Separate section for deletion
        st.divider()
        st.subheader("Delete Travel Record")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            travel_ids = df['travel_id'].tolist()
            selected_id = st.selectbox(
                "Select Travel ID to delete",
                options=travel_ids,
                format_func=lambda x: f"ID: {x}"
            )
        
        with col2:
            # Show details of selected travel record
            selected_row = df[df['travel_id'] == selected_id].iloc[0]
            st.write(f"**Product:** {selected_row['Product']} | **Customer:** {selected_row['Customer']} | **Vendor:** {selected_row['Vendor']}")
            
            if st.button("🗑️ Delete Travel Record", type="secondary"):
                try:
                    delete_row("Travel", "travel_id", selected_id)
                    st.warning(f"Travel ID {selected_id} deleted successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting travel record: {e}")
        
        # Display summary statistics
        st.divider()
        st.subheader("Summary Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Travel Records", len(df))
        with col2:
            total_deposits = df['deposite'].sum()
            st.metric("Total Deposits", f"${total_deposits:,.0f}")
        with col3:
            total_payments = df['payment'].sum()
            st.metric("Total Payments", f"${total_payments:,.0f}")
        with col4:
            total_expenses = df['event_expense'].sum()
            st.metric("Total Event Expenses", f"${total_expenses:,.0f}")
        
        # Additional financial summary
        col1, col2, col3 = st.columns(3)
        with col1:
            total_airfare_ib = df['airfair_IB'].sum()
            st.metric("Total Inbound Airfare", f"${total_airfare_ib:,.0f}")
        with col2:
            total_airfare_ob = df['airfair_OB'].sum()
            st.metric("Total Outbound Airfare", f"${total_airfare_ob:,.0f}")
        with col3:
            total_airfare = total_airfare_ib + total_airfare_ob
            st.metric("Total Airfare", f"${total_airfare:,.0f}")

except sqlite3.OperationalError:
    st.warning("Travel table does not exist yet.")
except Exception as e:
    st.error(f"Error fetching data from Travel table: {e}")
