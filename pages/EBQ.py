import streamlit as st
from models.inventorymanagement import Model

st.set_page_config(page_title="EBQ Calculator", layout="wide")

st.title("Economic Batch Quantity (EBQ)")

r = st.number_input(
    "Demand Rate (r)",
    min_value=0.0,
    value=1000.0
)

R = st.number_input(
    "Production Rate (R)",
    min_value=0.0,
    value=5000.0
)

k = st.number_input(
    "Setup Cost (k)",
    min_value=0.0,
    value=50.0
)

h = st.number_input(
    "Holding Cost (h)",
    min_value=0.0,
    value=2.0
)

c = st.number_input(
    "Unit Cost (c)",
    min_value=0.0,
    value=10.0
)

@st.cache_data
def calculate_results(r, R, k, h, c):

    model = Model()

    model.r = r
    model.R = R
    model.k = k
    model.h = h
    model.c = c

    ebq = model.calculate_ebq()

    return {
        "EBQ": ebq,
        "Total Cost": model.calculate_total_cost(ebq, "ebq"),
        "Total Variable Cost": model.total_variable_cost(ebq, "ebq"),
        "Optimal Replenishment Time": model.optimal_replenishment_time("ebq", ebq),
        "Ordering Frequency": model.ordering_frequency(ebq)
    }

if st.button("Calculate EBQ"):

    if R <= r:
        st.error("Production Rate (R) must be greater than Demand Rate (r)")
        st.stop()

    results = calculate_results(r, R, k, h, c)
    st.session_state["ebq_results"] = results

if "ebq_results" in st.session_state:

    results = st.session_state["ebq_results"]

    st.success(f"Calculated EBQ = {results['EBQ']:.2f}")

    option = st.sidebar.selectbox(
        "Display Additional Result",
        [
            "Total Cost",
            "Total Variable Cost",
            "Optimal Replenishment Time",
            "Ordering Frequency"
        ]
    )

    if option == "Total Cost":
        st.info(f"Total Cost = ${results['Total Cost']:.2f}")
    elif option == "Total Variable Cost":
        st.info(f"Total Variable Cost = ${results['Total Variable Cost']:.2f}")
    elif option == "Optimal Replenishment Time":
        st.info(f"Optimal Replenishment Time = {results['Optimal Replenishment Time']:.2f} time units")
    elif option == "Ordering Frequency":
        st.info(f"Ordering Frequency = {results['Ordering Frequency']:.2f} orders per unit time")