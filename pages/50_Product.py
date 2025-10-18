import streamlit as st
import pandas as pd
from utils.database import get_db_connection
from utils.style import load_css

# Set page config
st.set_page_config(page_title="Product Management", page_icon="⌨️", layout="wide")
load_css()
st.header("🗂️ Product Management")

# --- TABS DEFINITION ---
tab1, tab2, tab3 = st.tabs(["➕ Add New Product", "✏️ Edit Product", "👀 Display Product"])

# --- TAB 1: Input Product (Unchanged) ---
with tab1:
    st.header("Add New Product")
    product_name = st.text_input("Product Name", key="add_product_name")
    notes = st.text_area("Notes", key="add_notes")
    status = st.selectbox("Status", [1, 0], format_func=lambda x: "Active" if x == 1 else "Inactive", key="add_status")

    if st.button("Add Product"):
        if product_name:
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO Product (Product, Notes, status) VALUES (?, ?, ?)",
                        (product_name, notes, status))
                    conn.commit()
                    st.success(f"Product '{product_name}' added successfully!")
                    # Clear inputs after success
                    st.session_state.add_product_name = ""
                    st.session_state.add_notes = ""
            except Exception as e:
                st.error(f"Database connection error: {e}")

# --- TAB 2: Edit Product (Using unique keys) ---
with tab2:
    st.header("Edit Existing Product")
    products = None

    # Fetch product list
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT rowid, Product FROM Product")
            products = cursor.fetchall()
    except Exception as e:
        st.error(f"Database error when loading products: {e}")
            
    if products:
        selected = st.selectbox("Select Product to Edit", products, 
                                format_func=lambda x: x[1], 
                                key="product_select")
        rowid = selected[0]
        
        product_data = None
        # Fetch data for selected product
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT Product, Notes, status FROM Product WHERE rowid = ?", (rowid,))
                product_data = cursor.fetchone()
        except Exception as e:
            st.error(f"Database error when fetching details: {e}")
        
        if product_data:
            new_name = st.text_input("Product Name", value=product_data[0], key="edit_name")
            new_notes = st.text_area("Notes", value=product_data[1], key="edit_notes")
            
            new_status = st.selectbox("Status", [1, 0], 
                                      index=0 if product_data[2] == 1 else 1,
                                      format_func=lambda x: "Active" if x == 1 else "Inactive",
                                      key="edit_status")

            # Update operation
            if st.button("Update Product"):
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("UPDATE Product SET Product = ?, Notes = ?, status = ? WHERE rowid = ?",
                                       (new_name, new_notes, new_status, rowid))
                        conn.commit()
                        st.success(f"Product '{new_name}' updated successfully!")
                        # Note: st.rerun() could be used here to refresh the UI
                except Exception as e:
                    st.error(f"Database error during update: {e}")
    else:
        st.info("No products available to edit.")

# --- TAB 3: Display Product (NEW) ---
with tab3:
    st.header("All Products List")
    
    def fetch_all_products():
        try:
            with get_db_connection() as conn:
                # Select rowid to serve as a unique ID/index
                df = pd.read_sql_query("SELECT rowid, Product, Notes, status FROM Product", conn)
            # Map the 'status' column from 1/0 to Active/Inactive for display
            df['status'] = df['status'].map({1: 'Active', 0: 'Inactive'})
            df.rename(columns={'rowid': 'ID', 'Product': 'Product Name'}, inplace=True)
            return df
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            return pd.DataFrame() # Return empty DataFrame on error

    df_products = fetch_all_products()

    if not df_products.empty:
        st.dataframe(
            df_products, 
            hide_index=True,
            width='stretch'
        )
        st.caption(f"Total products: **{len(df_products)}**")
    else:
        st.info("No products found in the database.")


