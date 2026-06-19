import streamlit as st
import pandas as pd
from models.inventorymanagement import Model

st.set_page_config(
    page_title="Probabilistic Inventory Model",
    page_icon="📦",
    layout="wide"
)

st.title("📦 Probabilistic Inventory Model")
st.divider()

st.subheader("⚙️ Economic Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    selling_price = st.number_input(
        "Selling Price",
        min_value=0.0,
        value=20.0,
        step=1.0
    )

with col2:
    unit_cost = st.number_input(
        "Unit Cost",
        min_value=0.0,
        value=10.0,
        step=1.0
    )

with col3:
    salvage_price = st.number_input(
        "Salvage Value",
        min_value=0.0,
        value=0.0,
        step=1.0
    )

st.subheader("Demand Probability Distribution")
st.caption(
    "Enter demand levels and their corresponding probabilities. "
    "The probabilities must sum to 1."
)

default_df = pd.DataFrame({
    "Demand (D)": [10, 20, 30, 40, 50],
    "f(D)": [0.10, 0.20, 0.30, 0.25, 0.15]
})

df = st.data_editor(
    default_df,
    num_rows="dynamic",
    use_container_width=True
)

total_probability = df["f(D)"].sum()

if abs(total_probability - 1) < 1e-6:
    st.success(f"✓ Total Probability = {total_probability:.3f}")
else:
    st.error(
        f"✗ Probability Sum = {total_probability:.3f} "
        "(must equal 1.000)"
    )

@st.cache_data
def calculate_probability(
        selling_price,
        unit_cost,
        salvage_price):

    model = Model()

    model.c = unit_cost

    return model.calculate_spm(
        selling_price,
        salvage_price
    )

st.divider()

calculate = st.button(
    "🚀 Calculate Optimal Quantity",
    use_container_width=True
)

if calculate:

    probability = calculate_probability(
        selling_price,
        unit_cost,
        salvage_price
    )

    work_df = df.copy()

    work_df["F(D)"] = work_df["f(D)"].cumsum()

    work_df["Distance"] = (
        work_df["F(D)"] - probability
    ).abs()

    optimal_row = work_df.loc[
        work_df["Distance"].idxmin()
    ]

    optimal_q = optimal_row["Demand (D)"]

    st.divider()

    st.subheader("📈 Results")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Optimal Probability",
            f"{probability:.4f}"
        )

    with col2:
        st.metric(
            "Optimal Order Quantity",
            f"{int(optimal_q)} units"
        )

    st.subheader("Cumulative Distribution Table")

    work_df["Optimal"] = work_df["Demand (D)"] == optimal_q

    st.dataframe(
        work_df[
            ["Demand (D)", "f(D)", "F(D)", "Optimal"]
        ],
        use_container_width=True
    )