# Custom CSS for styling
import streamlit as st
import datetime

def format_timestamp(timestamp_str):
    """Format timestamp for better display"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp_str


# Format price helper
def format_price(cents):
    return f"${cents / 100:.2f}"

