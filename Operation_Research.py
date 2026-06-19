import streamlit as st

st.set_page_config(
    page_title="Operations Research",
    page_icon="📊",
    layout="wide"
)

# Header
st.title("📊 Operations Research")

st.divider()

# Introduction
st.markdown(
    """
    Welcome! This platform provides interactive tools and models for solving
    optimization problems commonly encountered in logistics, supply chain,
    manufacturing, and business analytics.
    """
)

st.subheader("🚀 Explore Models")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🚚 Transportation Problem", use_container_width=True):
        st.switch_page("pages/Transportation_Problem.py")

with col2:
    if st.button("📈 Linear Programming", use_container_width=True):
        st.switch_page("pages/Linear_Programming.py")

with col3:
    if st.button("📦 Inventory Management", use_container_width=True):
        st.switch_page("pages/EOQ.py")