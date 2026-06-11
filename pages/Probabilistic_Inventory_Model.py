import streamlit as st
import pandas as pd
from models.inventorymanagement import Model

st.set_page_config(
    page_title="Probabilistic Inventory Model",
    layout="wide"
)

st.title("Probabilistic Inventory Model")

selling_price = st.number_input(
    "Selling Price",
    min_value=0.0,
    value=20.0
)

unit_cost = st.number_input(
    "Unit Cost",
    min_value=0.0,
    value=10.0
)

salvage_price = st.number_input(
    "Salvage Value",
    min_value=0.0,
    value=0.0
)

st.subheader("Demand Probability Distribution")

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
    st.success(f"Total Probability = {total_probability:.4f}")
else:
    st.warning(
        f"Total Probability = {total_probability:.4f} "
        "(should equal 1)"
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

if st.button("Calculate Optimal Quantity"):

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

    st.success(
        f"Optimal Probability = {probability:.4f}"
    )

    st.success(
        f"Optimal Order Quantity (Q) = {optimal_q}"
    )

    st.subheader("Cumulative Distribution Table")

    st.dataframe(
        work_df[
            ["Demand (D)", "f(D)", "F(D)"]
        ],
        use_container_width=True
    )