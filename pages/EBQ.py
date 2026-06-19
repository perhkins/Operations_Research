import streamlit as st
from models.inventorymanagement import Model

st.set_page_config(page_title="EBQ Calculator", page_icon="🏭", layout="wide")

st.title("🏭 Economic Batch Quantity (EBQ)")

st.markdown("""
The **Economic Batch Quantity (EBQ)** model determines the optimal production lot size
that minimizes the combined cost of setup and inventory holding.
""")

st.divider()

st.subheader("Production Parameters")

col1, col2 = st.columns(2)

with col1:
    r = st.number_input(
        "Demand Rate (r)",
        min_value=0.0,
        value=1000.0
    )

with col2:
    R = st.number_input(
        "Production Rate (R)",
        min_value=0.0,
        value=5000.0
    )

    if R <= r:
        st.error(
            "Production Rate must exceed Demand Rate."
        )

st.subheader("💵 Cost Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    k = st.number_input(
        "Setup Cost (k)",
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

st.divider()

calculate = st.button(
    "🚀 Calculate EBQ",
    use_container_width=True
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

if calculate:

    if R <= r:
        st.error("Production Rate (R) must be greater than Demand Rate (r)")
        st.stop()

    results = calculate_results(r, R, k, h, c)
    st.session_state["ebq_results"] = results

if "ebq_results" in st.session_state:

    results = st.session_state["ebq_results"]

    with st.container(border=True):
        st.subheader("📈 Optimal Production Policy")
        st.markdown("---")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "EBQ",
                f"{results['EBQ']:.2f}"
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
            To minimize setup and holding costs, produce approximately
            **{results['EBQ']:.0f} units per batch**.

            This production policy results in:

            • Total Cost of **${results['Total Cost']:,.2f}**

            • Production cycles every
            **{results['Optimal Replenishment Time']:.2f} time units**

            • Approximately
            **-{results['Ordering Frequency']: .0f} production runs** per unit time.
            """
        )