import streamlit as st
from models.inventorymanagement import Model

st.set_page_config(page_title="EOQ Calculator", page_icon="📦", layout="wide")

st.title("📦 Economic Order Quantity (EOQ)")

st.markdown("""
The **EOQ model** determines the optimal order quantity that minimizes
the combined cost of ordering and holding inventory.

This tool helps answer:

- 📦 How much should I order?
- 💰 What inventory cost can I expect?
- 🔄 How often should I replenish stock?
- 📈 What ordering policy minimizes total cost?
""")

st.divider()

r = st.number_input(
    "Demand Rate (r)",
    min_value=0.0,
    value=1000.0
)

col1, col2, col3 = st.columns(3)

with col1:
    k = st.number_input(
        "Ordering Cost (k)",
        min_value=0.0,
        value=50.0
    )

with col2:
    h = st.number_input(
        "Holding Cost (h)",
        min_value=0.0,
        value=2.0
    )

with col3:
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

st.divider()

calculate = st.button(
    "🚀 Calculate EOQ",
    use_container_width=True
)

if calculate:

    results = calculate_results(r, k, h, c)
    st.session_state["eoq_results"] = results

if "eoq_results" in st.session_state:

    results = st.session_state["eoq_results"]

    with st.container(border=True):
        st.subheader("📊 Inventory Policy Summary")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "EOQ",
                f"{results['EOQ']:.2f} units"
            )

        with col2:
            st.metric(
                "Total Cost",
                f"${results['Total Cost']:,.2f}"
            )

        with col3:
            st.metric(
                "Variable Cost",
                f"${results['Total Variable Cost']:,.2f}"
            )

        col4, col5, col6 = st.columns(3)

        with col4:
            st.metric(
                "Replenishment Time",
                f"{results['Optimal Replenishment Time']:.2f}"
            )

        with col5:
            st.metric(
                "Ordering Frequency",
                f"{results['Ordering Frequency']:.2f}"
            )
    
    show_analysis = st.checkbox(
        "Business Analysis",
        value=False,
    )

    if show_analysis:
        st.subheader("📝 Interpretation")

        st.info(
            f"""
            Based on the provided demand and cost parameters,
            the optimal order quantity is **{results['EOQ']:.0f} units**.

            This ordering policy:

            • Minimizes inventory-related costs

            • Results in a total annual cost of
            **${results['Total Cost']:,.2f}**

            • Requires replenishment approximately every
            **{results['Optimal Replenishment Time']:.2f} time units**

            • Corresponds to
            **{results['Ordering Frequency']:.2f} orders**
            per planning period
            """
        )