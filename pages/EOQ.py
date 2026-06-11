import streamlit as st
from models.inventorymanagement import Model

st.set_page_config(page_title="EOQ Calculator", layout="wide")

st.title("Economic Order Quantity (EOQ)")

r = st.number_input(
    "Demand Rate (r)",
    min_value=0.0,
    value=1000.0
)

k = st.number_input(
    "Ordering / Setup Cost (k)",
    min_value=0.0,
    value=50.0
)

h = st.number_input(
    "Holding Cost per Unit (h)",
    min_value=0.0,
    value=2.0
)

c = st.number_input(
    "Unit Cost (c)",
    min_value=0.0,
    value=10.0
)

@st.cache_data
def calculate_results(r, k, h, c):

    model = Model()
    model.r = r
    model.k = k
    model.h = h
    model.c = c

    eoq = model.calculate_eoq()

    return {
        "EOQ": eoq,
        "Total Cost": model.calculate_total_cost(eoq, "eoq"),
        "Total Variable Cost": model.total_variable_cost(eoq, "eoq"),
        "Optimal Replenishment Time": model.optimal_replenishment_time("eoq"),
        "Ordering Frequency": model.ordering_frequency(eoq)
    }

if st.button("Calculate EOQ"):

    results = calculate_results(r, k, h, c)
    st.session_state["eoq_results"] = results

if "eoq_results" in st.session_state:

    results = st.session_state["eoq_results"]

    st.success(f"Calculated EOQ = {results['EOQ']:.2f} units")

    option = st.sidebar.selectbox(
        "Display Additional Result",
        [
            "Total Cost",
            "Total Variable Cost",
            "Optimal Replenishment Time",
            "Ordering Frequency"
        ]
    )

    st.sidebar.metric(option, f"{results[option]:.4f}")