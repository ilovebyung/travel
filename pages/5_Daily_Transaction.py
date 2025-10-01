import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta
from utils.util import format_price, format_timestamp
from utils.database import  get_db_connection
from utils.style import load_css 

# Page configuration
st.set_page_config(page_title="Daily Transactions", page_icon="📊", layout="wide")
st.title("📊 Daily Transactions")
st.markdown("---")


def get_transaction_data(start_date, end_date):
    """Fetch transaction data for the selected date range"""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        query = """
        SELECT 
            oh.order_id,
            CASE oh.order_status
                WHEN 1 THEN 'created'
                WHEN 2 THEN 'confirmed'
                WHEN 3 THEN 'completed'
                ELSE 'unknown'
            END AS order_status,
            oh.timestamp,
            -- pi.product_id,
            pi.description as product_description,
            pi.price,
            pi.tax,
            op.product_quantity,
            -- op.service_area_id,
            -- op.option,
            (pi.price * op.product_quantity) as subtotal,
            (pi.tax * op.product_quantity) as total_tax,
            ((pi.price + pi.tax) * op.product_quantity) as total_amount
        FROM Order_History oh
        LEFT JOIN Order_Product op ON oh.order_id = op.order_id
        LEFT JOIN Product_Item pi ON op.product_id = pi.product_id
        WHERE DATE(oh.timestamp) BETWEEN ? AND ?
        ORDER BY oh.timestamp DESC, oh.order_id, pi.product_id
        """
        
        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        return df
        
    except sqlite3.Error as e:
        st.error(f"Database query error: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_summary_data(start_date, end_date):
    """Get summary statistics for the selected date range"""
    conn = get_db_connection()
    if not conn:
        return {}
    
    try:
        query = """
        SELECT 
            COUNT(DISTINCT oh.order_id) as total_orders,
            COUNT(op.product_id) as total_items,
            SUM(op.product_quantity) as total_quantity,
            SUM((pi.price + pi.tax) * op.product_quantity) as total_revenue
        FROM Order_History oh
        LEFT JOIN Order_Product op ON oh.order_id = op.order_id
        LEFT JOIN Product_Item pi ON op.product_id = pi.product_id
        WHERE DATE(oh.timestamp) BETWEEN ? AND ? AND oh.order_status IN (3)
        """
        
        result = conn.execute(query, (start_date, end_date)).fetchone()
        return {
            'total_orders': result[0] or 0,
            'total_items': result[1] or 0,
            'total_quantity': result[2] or 0,
            'total_revenue': result[3] or 0
        }
        
    except sqlite3.Error as e:
        st.error(f"Database query error: {e}")
        return {}
    finally:
        conn.close()

# Sidebar for date selection
st.sidebar.header(" Date Selection")

# Date range selection
date_option = st.sidebar.radio(
    "Select date range:",
    ["Single Day", "Date Range", "Last 7 Days", "Last 30 Days"]
)

today = date.today()

if date_option == "Single Day":
    selected_date = st.sidebar.date_input(
        "Select date:",
        value=today,
        max_value=today
    )
    start_date = end_date = selected_date
    
elif date_option == "Date Range":
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.sidebar.date_input(
            "Start date:",
            value=today - timedelta(days=7),
            max_value=today
        )
    with col2:
        end_date = st.sidebar.date_input(
            "End date:",
            value=today,
            max_value=today,
            min_value=start_date
        )
        
elif date_option == "Last 7 Days":
    start_date = today - timedelta(days=7)
    end_date = today
    
elif date_option == "Last 30 Days":
    start_date = today - timedelta(days=30)
    end_date = today

# Display selected date range
if start_date == end_date:
    st.sidebar.info(f"Selected: {start_date}")
else:
    st.sidebar.info(f"Selected: {start_date} to {end_date}")

# Main content
if st.sidebar.button("Refresh Data", type="primary"):
    st.cache_data.clear()

# Get and display summary statistics
st.subheader(" Summary Statistics")
summary = get_summary_data(start_date, end_date)

if summary:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Orders", summary['total_orders'])
    with col2:
        st.metric("Total Items", summary['total_items'])
    with col3:
        st.metric("Total Quantity", summary['total_quantity'])
    with col4:
        st.metric("Total Revenue", format_price(summary['total_revenue']))

st.divider()

# Get transaction data
st.subheader(" Transaction Details")
df = get_transaction_data(start_date, end_date)

if df.empty:
    st.info("No transactions found for the selected date range.")
else:
    # Format the data for display
    display_df = df.copy()
    
    # Format price columns
    if 'price' in display_df.columns:
        display_df['price'] = display_df['price'].apply(format_price)
    if 'tax' in display_df.columns:
        display_df['tax'] = display_df['tax'].apply(format_price)
    if 'subtotal' in display_df.columns:
        display_df['subtotal'] = display_df['subtotal'].apply(format_price)
    if 'total_tax' in display_df.columns:
        display_df['total_tax'] = display_df['total_tax'].apply(format_price)
    if 'total_amount' in display_df.columns:
        display_df['total_amount'] = display_df['total_amount'].apply(format_price)
    
    # Format timestamp
    if 'timestamp' in display_df.columns:
        display_df['timestamp'] = display_df['timestamp'].apply(format_timestamp)
    
    # Rename columns for better display
    column_mapping = {
        'order_id': 'Order ID',
        'status': 'Status',
        'timestamp': 'Timestamp',
        # 'product_id': 'Product ID',
        'product_description': 'Product Description',
        'price': 'Unit Price',
        'tax': 'Unit Tax',
        'product_quantity': 'Quantity',
        # 'service_area_id': 'Service Area',
        # 'option': 'Option',
        'subtotal': 'Subtotal',
        'total_tax': 'Total Tax',
        'total_amount': 'Total Amount'
    }
    
    display_df = display_df.rename(columns=column_mapping)
    
    # Display options
    items_per_page = st.selectbox("Items per page", [10, 25, 50, 100], index=1)

    # Show detailed view with pagination
    total_rows = len(display_df)
    
    if total_rows > items_per_page:
        page_num = st.number_input(
            f"Page (showing {items_per_page} of {total_rows} records)",
            min_value=1,
            max_value=(total_rows - 1) // items_per_page + 1,
            value=1
        )
        start_idx = (page_num - 1) * items_per_page
        end_idx = start_idx + items_per_page
        display_df = display_df.iloc[start_idx:end_idx]
    
    # Display the data editor
    edited_df = st.data_editor(
        display_df,
        width='stretch',
        hide_index=True,
        disabled=True,
        num_rows="dynamic",
        column_config={
            "Order ID": st.column_config.NumberColumn("Order ID", width="small"),
            "Status": st.column_config.NumberColumn("Status", width="small"),
            "Timestamp": st.column_config.TextColumn("Timestamp", width="medium"),
            # "Product ID": st.column_config.NumberColumn("Product ID", width="small"),
            "Product Description": st.column_config.TextColumn("Product Description", width="large"),
            "Unit Price": st.column_config.TextColumn("Unit Price", width="small"),
            "Unit Tax": st.column_config.TextColumn("Unit Tax", width="small"),
            "Quantity": st.column_config.NumberColumn("Quantity", width="small"),
            "Service Area": st.column_config.NumberColumn("Service Area", width="small"),
            # "Option": st.column_config.TextColumn("Option", width="medium"),
            "Subtotal": st.column_config.TextColumn("Subtotal", width="small"),
            # "Total Tax": st.column_config.TextColumn("Total Tax", width="small"),
            "Total Amount": st.column_config.TextColumn("Total Amount", width="small")
        }
    )
    
    # Show record count
    st.info(f"Showing {len(display_df)} of {total_rows} records")

# # Export functionality
# if not df.empty:
#     st.divider()
#     st.subheader(" Export Data")
    
#     col1, col2 = st.columns(2)
#     with col1:
#         if st.button("📋 Copy to Clipboard"):
#             display_df.to_clipboard(index=False)
#             st.success("Data copied to clipboard!")
    
#     with col2:
#         csv = display_df.to_csv(index=False)
#         st.download_button(
#             label="💾 Download CSV",
#             data=csv,
#             file_name=f"transactions_{start_date}_{end_date}.csv",
#             mime="text/csv"
#         )