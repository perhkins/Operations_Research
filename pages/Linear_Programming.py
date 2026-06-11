import streamlit as st
import traceback
from models.linearprogramming import LinearProgramming

st.set_page_config(
    page_title="Linear Programming Solver",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Linear Programming Solver")

# --------------------------
# Problem Setup
# --------------------------

st.header("1. Problem Definition")

objective = st.selectbox(
    "Objective",
    ["max", "min"],
    format_func=lambda x: "Maximize" if x == "max" else "Minimize"
)

num_variables = st.number_input(
    "Number of Variables",
    min_value=2,
    max_value=20,
    value=2,
    step=1
)

# --------------------------
# Objective Function
# --------------------------

st.header("2. Objective Function")

st.write("Enter coefficients for:")

obj_cols = st.columns(num_variables)

objective_coeffs = []

for i in range(num_variables):
    coeff = obj_cols[i].number_input(
        f"x{i+1}",
        value=1.0,
        key=f"obj_{i}"
    )
    objective_coeffs.append(coeff)

# --------------------------
# Constraints
# --------------------------

st.header("3. Constraints")

num_constraints = st.number_input(
    "Number of Constraints",
    min_value=1,
    value=2,
    step=1
)

constraints_data = []

for c in range(num_constraints):

    st.subheader(f"Constraint {c+1}")

    cols = st.columns(num_variables + 2)

    coeffs = []

    for i in range(num_variables):
        coeff = cols[i].number_input(
            f"x{i+1}",
            value=1.0,
            key=f"c_{c}_{i}"
        )
        coeffs.append(coeff)

    operator = cols[-2].selectbox(
        "Operator",
        ["<=", ">=", "="],
        key=f"op_{c}"
    )

    rhs = cols[-1].number_input(
        "Value",
        value=1.0,
        key=f"rhs_{c}"
    )

    constraints_data.append(
        {
            "coefficients": coeffs,
            "operator": operator,
            "value": rhs
        }
    )

# --------------------------
# Solve
# --------------------------

st.divider()

if st.button("🚀 Solve Problem", use_container_width=True):

    try:

        lp = LinearProgramming(
            objective=objective,
            coefficients=objective_coeffs
        )

        for constraint in constraints_data:
            lp.add_constraint(
                coefficients=constraint["coefficients"],
                operator=constraint["operator"],
                value=constraint["value"]
            )

        # Auto-select method
        method = (
            "graphical"
            if num_variables == 2
            else "simplex"
        )

        st.info(f"Using {method.title()} Method")

        objective_expr = " + ".join(
            [
                f"{objective_coeffs[i]}x_{i+1}"
                for i in range(num_variables)
            ]
        )

        st.latex(f"Z = {objective_expr}")

        for constraint in constraints_data:
            coeffs = constraint["coefficients"]
            operator = constraint["operator"]
            rhs = constraint["value"]
            constraint_expr = " + ".join(
                [
                    f"{coeffs[i]}x_{i+1}"
                    for i in range(num_variables)
                ]
            )

            st.latex(
                f"{constraint_expr} {operator} {rhs}"
            )

        result = lp.solution(method=method)

        st.success("Solution Found")

        # ----------------------
        # Graphical Method
        # ----------------------
        if method == "graphical":

            cfs, fig = result

            st.subheader("Optimal Solution")

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Optimal Value",
                    round(cfs["optimal_value"], 4)
                )

            optimal_point = {f"x{i+1}": value for i, value in enumerate(cfs["optimal_point"])}

            with col2:
                st.write("Optimal Point")
                st.json(optimal_point)

            st.subheader("Feasible Region")

            st.pyplot(fig)

            formatted_cfs = [{f"x{i+1}": value for i, value in enumerate(point)}
                             for point in cfs["cfs"]]

            with st.expander("Full Result"):
                st.json({"cfs": formatted_cfs})

        # ----------------------
        # Simplex Method
        # ----------------------
        else:
            if objective == "min":
                st.info("Duality Applied: Problem Transformed to Maximization")
            st.subheader("Optimal Solution")

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Optimal Value",
                    round(result["optimal_value"], 4)
                )

            optimal_point = {f"x{i+1}": value for i, value in enumerate(result["optimal_point"])}

            with col2:
                st.write("Optimal Point")
                st.json(optimal_point)

            with st.expander("Full Result"):
                st.json(result)

    except Exception as e:
        st.error(str(e))
        st.code(traceback.format_exc())