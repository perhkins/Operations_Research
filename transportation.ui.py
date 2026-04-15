import streamlit as st
from transportation import TransportationProblem


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
    st.title("Transportation Problem Solver")
    
    # Input supply and demand
    supply_length = st.number_input("Number of Supply Points", min_value=1, step=1)
    demand_length = st.number_input("Number of Demand Points", min_value=1, step=1)
    
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
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Supply Capacities (Units)")
            supply_df = st.data_editor(
                pd.DataFrame({
                    f"S{i+1}": [0] for i in range(supply_length)
                }).T.rename_axis("Supply").rename(columns={0: "Supply"}),
                num_rows="fixed",
                key="supply_editor"
            )
        
        with col2:
            st.subheader("Demand Requirements (Units)")
            demand_df = st.data_editor(
                pd.DataFrame({
                    f"D{j+1}": [0] for j in range(demand_length)
                }).T.rename_axis("Demand").rename(columns={0: "Demand"}),
                num_rows="fixed",
                key="demand_editor"
            )
        
        # Input cost matrix using a table (supply as rows, demand as columns)
        st.subheader("Cost Matrix")
        cost_df = st.data_editor(
            pd.DataFrame(
                0,
                index=[f"S{i+1}" for i in range(supply_length)],
                columns=[f"D{j+1}" for j in range(demand_length)]
            ),
            num_rows="fixed",
            key="cost_editor"
        )

        col_method_1, col_method_2, col_method_3 = st.columns(3)
        with col_method_1:
            initial_method = st.selectbox(
                "Initial Method",
                options=["northwest", "leastcost"],
                format_func=lambda value: "North-West Corner" if value == "northwest" else "Least Cost",
            )
        with col_method_2:
            optimization_method = st.selectbox(
                "Optimization Method",
                options=["modi", "steppingstone"],
                format_func=lambda value: "MODI" if value == "modi" else "Stepping Stone",
            )
        with col_method_3:
            show_iterations = st.checkbox("Show Iterations", value=False)
        
        if st.button("Solve"):
            original_rows = supply_length
            original_cols = demand_length
            
            # Use set_supply, set_demand, set_cost to populate problem directly
            for i in range(len(supply_df)):
                problem.set_supply(i, supply_df["Supply"].iloc[i])
            for j in range(len(demand_df)):
                problem.set_demand(j, demand_df["Demand"].iloc[j])
            for i in range(len(cost_df)):
                for j in range(len(cost_df.columns)):
                    problem.set_cost(i, j, cost_df.iloc[i, j])
            
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