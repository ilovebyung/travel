import streamlit as st
from utils.style import load_css

# Set page config
st.set_page_config(page_title="Home", page_icon="🏠", layout="wide")
st.header("🏠 Welcome Travel Home ", divider='blue')

# Add vertical space to push the caption down
for _ in range(5):
    st.write("")

# Navigation hint
st.subheader("👈 Use the sidebar to navigate")

# Add vertical space to push the caption down
for _ in range(20):
    st.write("")


# Caption at the bottom
st.caption("Built with ❤️ by BADA") 


