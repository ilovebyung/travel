import streamlit as st
import sqlite3
from utils.database import update_row, delete_row, get_table_data
from utils.style import load_css

# Set page config
st.set_page_config(page_title="Customer Management", page_icon="🧳", layout="wide")
load_css()

st.header("🛠️ Update Customer", divider='blue')

try:
    df = get_table_data("Customer")
    
    if df.empty:
        st.warning("No customer data available.")
    else:
        # Reset the index to start from 1 for display
        display_df = df.copy()
        display_df.index = display_df.index + 1
        
        st.subheader("Customer Data Editor")
        st.info("💡 Edit cells directly in the table below. Changes are highlighted. Click 'Save Changes' to commit updates to the database.")
        
        # Configure column settings for data_editor
        column_config = {
            "customer_id": st.column_config.NumberColumn(
                "Customer ID",
                disabled=True,  # Primary key shouldn't be edited
                help="Unique customer identifier"
            ),
            "status": st.column_config.SelectboxColumn(
                "Status",
                options=[0, 1],
                required=True,
                help="0 = Inactive, 1 = Active"
            ),
            "sex": st.column_config.TextColumn(
                "Sex",
                help="Gender"
            ),
            "date_of_birth": st.column_config.TextColumn(
                "Date of Birth",
                help="Format: YYYY-MM-DD"
            ),
            "credit_card_date": st.column_config.TextColumn(
                "Credit Card Expiry",
                help="Format: MM/YY"
            ),
            "is_representative": st.column_config.CheckboxColumn(
                "Representative",
                help="Is this customer a representative?",
                default=False
            )
        }
        
        # Use data_editor for inline editing
        edited_df = st.data_editor(
            display_df,
            column_config=column_config,
            use_container_width=True,
            num_rows="dynamic",  # Allow adding/deleting rows
            key="customer_editor",
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
                            update_row("Customer", "customer_id", row_dict)
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
        st.subheader("Delete Customer")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            customer_ids = df['customer_id'].tolist()
            selected_id = st.selectbox(
                "Select Customer ID to delete",
                options=customer_ids,
                format_func=lambda x: f"ID: {x}"
            )
        
        with col2:
            st.write("")  # Spacing
            st.write("")  # Spacing
            if st.button("🗑️ Delete Customer", type="secondary"):
                try:
                    delete_row("Customer", "customer_id", selected_id)
                    st.warning(f"Customer ID {selected_id} deleted successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting customer: {e}")
        
        # Display summary statistics
        st.divider()
        st.subheader("Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Customers", len(df))
        with col2:
            active_count = len(df[df['status'] == 1])
            st.metric("Active Customers", active_count)
        with col3:
            inactive_count = len(df[df['status'] == 0])
            st.metric("Inactive Customers", inactive_count)
        with col4:
            rep_count = len(df[df['is_representative'] == 1])
            st.metric("Representatives", rep_count)

except sqlite3.OperationalError:
    st.warning("Customer table does not exist yet.")
except Exception as e:
    st.error(f"Error fetching data from Customer table: {e}")