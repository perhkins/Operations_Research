import streamlit as st
from models.transportation import TransportationProblem


def update_supply_data(st, df):
    st.session_state.supply_data = df["Supply"].to_dict()


def update_demand_data(st, df):
    st.session_state.demand_data = df["Demand"].to_dict()


def update_cost_data(st, df):
    st.session_state.cost_data = df.to_dict(orient="index")


def build_table_with_constraints(solution, problem, original_rows, original_cols):
    row_labels = [f"S{i+1}" for i in range(original_rows)]
    col_labels = [f"D{j+1}" for j in range(original_cols)]

    if len(solution.allocations) > original_rows:
        row_labels.append("Sº")
    if solution.allocations and len(solution.allocations[0]) > original_cols:
        col_labels.append("Dº")

    table_columns = col_labels + ["Supply"]
    table_rows = []
    table_index = []

    for i, row_label in enumerate(row_labels):
        row_data = {"Supply": ""}
        row_total = 0
        for j, col_label in enumerate(col_labels):
            if i < len(solution.allocations) and j < len(solution.allocations[i]):
                allocated = solution.allocations[i][j]
            else:
                allocated = None

            row_data[col_label] = allocated if allocated is not None else ""
            if allocated is not None:
                row_total += allocated

        row_data["Supply"] = row_total if i < len(problem.supply) else ""
        table_rows.append(row_data)
        table_index.append(row_label)

    bottom_row = {"Supply": f"{sum(problem.supply)}/{sum(problem.demand)}"}
    for j, col_label in enumerate(col_labels):
        demand_value = problem.demand[j] if j < len(problem.demand) else ""
        bottom_row[col_label] = demand_value
    table_rows.append(bottom_row)
    table_index.append("Demand")

    return pd.DataFrame(table_rows, index=table_index, columns=table_columns)


def build_schedule_graph(solution, problem, original_rows, original_cols):
    supply_labels = [f"S{i+1}" for i in range(original_rows)]
    demand_labels = [f"D{j+1}" for j in range(original_cols)]

    if len(solution.allocations) > original_rows:
        supply_labels.append("Sº")
    if solution.allocations and len(solution.allocations[0]) > original_cols:
        demand_labels.append("Dº")

    lines = [
        "digraph TransportationSchedule {",
        "  rankdir=LR;",
        "  graph [pad=0.2, nodesep=0.7, ranksep=1.1];",
        "  node [style=filled, fontsize=11, fontname=\"Helvetica\"];",
    ]

    for i, label in enumerate(supply_labels):
        supply_value = problem.supply[i] if i < len(problem.supply) else ""
        node_name = f"S{i}"
        lines.append(
            f'  {node_name} [shape=box, fillcolor="#dbeafe", label="{label} ({supply_value})"];'
        )

    for j, label in enumerate(demand_labels):
        demand_value = problem.demand[j] if j < len(problem.demand) else ""
        node_name = f"D{j}"
        lines.append(
            f'  {node_name} [shape=ellipse, fillcolor="#fde68a", label="{label} ({demand_value})"];'
        )

    for i, row in enumerate(solution.allocations):
        for j, allocated in enumerate(row):
            if allocated is None or allocated <= 0:
                continue
            unit_cost = problem.costs[i][j] if i < len(problem.costs) and j < len(problem.costs[i]) else 0
            lines.append(f'  S{i} -> D{j} [label="{allocated} @ #{unit_cost}", penwidth=1.7];')

    lines.append("}")
    return "\n".join(lines)


def main():
    st.set_page_config(
        page_title="Transportation Problem Solver",
        page_icon="🚚",
        layout="wide"
    )

    st.title("🚚 Transportation Problem Solver")

    st.markdown(
        "Define supply points, demand points, and transportation costs "
        "to find the minimum-cost transportation plan."
    )

    st.divider()

    col_a, col_b = st.columns(2)

    with col_a:
        supply_length = st.number_input(
            "Number of Supply Points",
            min_value=1,
            value=3,
            step=1,
        )

    with col_b:
        demand_length = st.number_input(
            "Number of Demand Points",
            min_value=1,
            value=3,
            step=1,
        )
    
    # Initialize session state for supply, demand, and cost data
    if "supply_length" not in st.session_state:
        st.session_state.supply_length = supply_length
    if "demand_length" not in st.session_state:
        st.session_state.demand_length = demand_length
    
    # Reset data if supply or demand length changed
    if st.session_state.supply_length != supply_length or st.session_state.demand_length != demand_length:
        st.session_state.supply_length = supply_length
        st.session_state.demand_length = demand_length
    
    if st.button("Create Problem"):
        st.session_state.problem_created = True
    
    # Show data editors if problem has been created
    if st.session_state.get("problem_created", False):
        problem = TransportationProblem(supply_length, demand_length)
        
        # Input supply and demand values side by side
        st.subheader("Problem Data")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Supply Capacities")

            supply_values = []
            for i in range(supply_length):
                value = st.number_input(
                    f"S{i+1}",
                    min_value=0,
                    value=0,
                    step=1,
                    key=f"supply_{i}",
                )
                supply_values.append(value)

        with col2:
            st.markdown("#### Demand Requirements")

            demand_values = []
            for j in range(demand_length):
                value = st.number_input(
                    f"D{j+1}",
                    min_value=0,
                    value=0,
                    step=1,
                    key=f"demand_{j}",
                )
                demand_values.append(value)

        # Cost Matrix
        st.markdown("---")
        st.subheader("Transportation Cost Matrix")

        cost_values = []

        # Header row
        header_cols = st.columns(demand_length + 1)
        header_cols[0].markdown("**Source**")

        for j in range(demand_length):
            header_cols[j + 1].markdown(f"**D{j+1}**")

        # Matrix rows
        for i in range(supply_length):
            row_cols = st.columns(demand_length + 1)

            row_cols[0].markdown(f"**S{i+1}**")

            row_costs = []

            for j in range(demand_length):
                cost = row_cols[j + 1].number_input(
                    label=f"S{i+1}-D{j+1}",
                    min_value=0,
                    value=0,
                    step=1,
                    label_visibility="collapsed",
                    key=f"cost_{i}_{j}",
                )
                row_costs.append(cost)

            cost_values.append(row_costs)

        st.markdown("---")
        st.subheader("Solution Settings")

        settings_col1, settings_col2, settings_col3 = st.columns(3)

        with settings_col1:
            initial_method = st.selectbox(
                "Initial Solution",
                ["northwest", "leastcost"],
                format_func=lambda x: {
                    "northwest": "North-West Corner",
                    "leastcost": "Least Cost",
                }[x],
            )

        with settings_col2:
            optimization_method = st.selectbox(
                "Optimization",
                ["modi", "steppingstone"],
                format_func=lambda x: {
                    "modi": "MODI",
                    "steppingstone": "Stepping Stone",
                }[x],
            )

        with settings_col3:
            show_iterations = st.checkbox(
                "Show Iterations",
                value=False,
            )
        
        if st.button("Solve"):
            original_rows = supply_length
            original_cols = demand_length
            
            # Use set_supply, set_demand, set_cost to populate problem directly
            for i, value in enumerate(supply_values):
                problem.set_supply(i, value)
            for j, value in enumerate(demand_values):
                problem.set_demand(j, value)
            for i in range(supply_length):
                for j in range(demand_length):
                    problem.set_cost(i, j, cost_values[i][j])

            try:
                solve_result = problem.solve(
                    method=initial_method,
                    optimization_method=optimization_method,
                    show_iterations=show_iterations,
                )

                history = None
                if show_iterations:
                    initial_solution, solution, history = solve_result
                else:
                    initial_solution, solution = solve_result
                cost = problem.calculate_total_cost(solution)
                
                if solution is None:
                    st.error("The transportation module returned no solution.")
                    return

                if hasattr(problem, "is_degenerate") and problem.is_degenerate(solution):
                    st.warning(
                        "The transportation module returned a degenerate or incomplete basic feasible solution. "
                        "The allocation table and graph are shown below, but the total cost may be unavailable or incomplete."
                    )

                if cost is None:
                    cost = "Unavailable for degenerate solution"
            except Exception as error:
                st.error(f"Unable to solve the transportation problem: {error}")
                return

            st.subheader("Initial Basic Feasible Solution")
            allocation_df = build_table_with_constraints(initial_solution, problem, original_rows, original_cols)
            st.table(allocation_df)

            st.subheader("Initial Schedule Graph")
            initial_graph_dot = build_schedule_graph(initial_solution, problem, original_rows, original_cols)
            st.graphviz_chart(initial_graph_dot, use_container_width=True)

            initial_cost = problem.calculate_total_cost(initial_solution)
            st.write(f"**Initial Transportation Cost: {initial_cost}**")

            if show_iterations and history:
                st.subheader("Iteration History")
                for step_index, allocation_table in enumerate(history):
                    st.write(f"Step {step_index}")
                    st.table(build_table_with_constraints(allocation_table, problem, original_rows, original_cols))

            st.subheader("Optimal Solution Graph")
            graph_dot = build_schedule_graph(solution, problem, original_rows, original_cols)
            st.graphviz_chart(graph_dot, use_container_width=True)

            st.write(f"**Total Transportation Cost: {cost}**")

import pandas as pd

if __name__ == "__main__":
    main()