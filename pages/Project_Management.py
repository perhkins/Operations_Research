import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

from streamlit.components.v1 import html

from models.projectmanagement import Project, Activity, Event, TimeAnalysis, CostAnalysis, ActivityExtended, PERT, PERTActivity

# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title="CPM / PERT Project Management",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Project Management Dashboard")
st.caption("Critical Path Method (CPM) & Project Evaluation Review Technique (PERT)")

# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:

    st.header("Navigation")

    module = st.radio(
        "Select Method",
        ["CPM", "PERT"]
    )

    if module == "CPM":

        analysis_type = st.radio(
            "Analysis",
            [
                "Time Analysis",
                "Cost Analysis",
                "Both"
            ]
        )

    st.divider()

    n_activities = st.number_input(
        "Number of Activities",
        min_value=1,
        value=5,
        step=1
    )

# ==========================================
# INPUT SECTION
# ==========================================

st.subheader("Project Activities")

activities_data = []

activity_names = []

if module == "CPM" and analysis_type in ["Cost Analysis", "Both"]:
    #Overhead Cost per time unit
    overhead_cost = st.number_input(
        "Overhead Cost per Time Unit",
        value=20,
        step=1
    )
    st.caption("If your normal costs and crash costs are in units of thousand/any other unit, make sure to adjust the overhead cost accordingly to maintain consistency in the analysis.")

for i in range(n_activities):

    st.markdown(f"### Activity {i+1}")

    c1, c2, c3 = st.columns([1,1,2])

    name = c1.text_input(
        "Activity",
        key=f"name_{i}",
        value=chr(65+i)
    )

    activity_names.append(name)

    if module == "CPM":

        duration = c2.number_input(
            "Duration",
            min_value=1,
            value=1,
            key=f"dur_{i}"
        )

        available_preds = ["--"] + activity_names[:-1]

        preds = c3.multiselect(
            "Predecessors",
            available_preds,
            default=[],
            key=f"pred_{i}"
        )

        row = {
            "Activity": name,
            "Duration": duration,
            "Predecessors": preds
        }

        if analysis_type in ["Cost Analysis", "Both"]:

            c4,c5,c6 = st.columns(3)

            row["Normal Cost"] = c4.number_input(
                "Normal Cost",
                value=100,
                key=f"nc_{i}"
            )

            row["Crash Cost"] = c5.number_input(
                "Crash Cost",
                value=150,
                key=f"cc_{i}"
            )

            row["Crash Time"] = c6.number_input(
                "Crash Time",
                value=1,
                key=f"ct_{i}"
            )

        activities_data.append(row)

    else:

        o,m,p = st.columns(3)

        optimistic = o.number_input(
            "Optimistic",
            value=1,
            key=f"o_{i}"
        )

        likely = m.number_input(
            "Most Likely",
            value=2,
            key=f"m_{i}"
        )

        pessimistic = p.number_input(
            "Pessimistic",
            value=3,
            key=f"p_{i}"
        )

        available_preds = ["--"] + activity_names[:-1]

        preds = st.multiselect(
            "Predecessors",
            available_preds,
            default=["--"],
            key=f"pred_pert_{i}"
        )

        activities_data.append(
            {
                "Activity": name,
                "Optimistic": optimistic,
                "Most Likely": likely,
                "Pessimistic": pessimistic,
                "Predecessors": preds
            }
        )

def TA_CPM(project: Project, show_floats: bool = True):
    st.write("Paths:", len(project.paths))
    ta = TimeAnalysis(project)

    ta.forward_pass()
    ta.backward_pass()

    if show_floats:

        float_table = []

        for k,v in ta.floats().items():

            float_table.append({
                "Activity": k,
                "Total Float": v[0],
                "Independent Float": v[1],
                "Free Float": v[2]
            })

        st.subheader("⏱ Time Analysis")

        st.dataframe(
            pd.DataFrame(float_table),
            use_container_width=True
        )

    draw_event_network(project)

def CA_CPM(project: Project, both: bool = False):
    if not both:
        TA_CPM(project, show_floats=False)
    activity_extensions = []

    for row in activities_data:

        act = lookup[row["Activity"]]

        act_ext = ActivityExtended(
            act,
            row["Normal Cost"],
            row["Crash Cost"],
            row["Crash Time"]
        )

        activity_extensions.append(act_ext)
    
    ca = CostAnalysis(project, overhead_cost)
    ca.activity_extensions = activity_extensions

    total_normal_cost = ca.total_normal_cost()

    min_cost, min_duration = ca.minimal_cost_and_duration()

    st.subheader("💰 Cost Analysis")

    c1,c2 = st.columns(2)

    c1.metric(
        "Total Normal Cost",
        total_normal_cost
    )

    c2.metric(
        "Minimal Cost",
        min_cost
    )

    c3,c4 = st.columns(2)
    c3.metric(
        "Original Duration",
        project.critical_path[1]
    )
    c4.metric(
        "Minimal Duration",
        min_duration
    )

# EVENT NETWORK GRAPH
def draw_event_network(project: Project):
    st.subheader("📌 Event Network Graph")

    G = nx.DiGraph()

    event_map = {}

    event_map[project.head.id] = project.head

    for act in project.activities:

        if act.nextEvent:
            event_map[act.nextEvent.id] = act.nextEvent

    for event_id in event_map:
        G.add_node(event_id)

    edge_labels = {}
    edge_colors = []

    critical_names = {
        a.Activity
        for a in project.critical_path[0]
    }

    for act in project.activities:

        start_event = None

        if act.predecessors:

            pred = act.predecessors[-1]

            if pred.nextEvent:
                start_event = pred.nextEvent.id

        else:
            start_event = project.head.id

        end_event = act.nextEvent.id

        G.add_edge(start_event, end_event)

        edge_labels[(start_event, end_event)] = (
            f"{act.Activity} ({act.duration})"
        )

        if act.Activity in critical_names:
            edge_colors.append("red")
        else:
            edge_colors.append("gray")
    
    from collections import defaultdict

    levels = {}

    levels[project.head.id] = 0

    changed = True

    while changed:

        changed = False

        for u, v in G.edges():

            if u in levels:

                new_level = levels[u] + 1

                if v not in levels or new_level > levels[v]:

                    levels[v] = new_level
                    changed = True
    
    level_nodes = defaultdict(list)

    for node, level in levels.items():

        level_nodes[level].append(node)

    pos = {}

    for level, nodes in level_nodes.items():

        nodes.sort()

        n = len(nodes)

        for i, node in enumerate(nodes):

            pos[node] = (
                level * 3,
                ((n - 1) / 2 - i) * 5
            )

    fig, ax = plt.subplots(figsize=(16,10))
    ax.set_aspect('equal')

    nx.draw_networkx_edges(
        G,
        pos,
        edge_color=edge_colors,
        width=3,
        arrows=True,
        ax=ax
    )

    nx.draw_networkx_edge_labels(
        G,
        pos,
        edge_labels=edge_labels,
        font_size=13,
        ax=ax
    )

    from matplotlib.patches import Circle

    for node_id, (x, y) in pos.items():

        event = event_map[node_id]

        circle = Circle(
            (x, y),
            radius=0.5,
            facecolor="#D6F0FF",
            edgecolor="black",
            linewidth=2
        )

        ax.add_patch(circle)

        # Horizontal divider

        ax.plot(
            [x - 0.5, x + 0.5],
            [y, y],
            color="black",
            linewidth=1
        )

        # Vertical divider in lower half

        ax.plot(
            [x, x],
            [y - 0.5, y],
            color="black",
            linewidth=1
        )

        # Event ID (top)

        ax.text(
            x,
            y + 0.12,
            str(event.id),
            ha="center",
            va="center",
            fontsize=13,
            fontweight="bold"
        )

        # Forward Pass

        ax.text(
            x - 0.18,
            y - 0.12,
            str(event.Fpass),
            ha="center",
            va="center",
            fontsize=13
        )

        # Backward Pass

        ax.text(
            x + 0.18,
            y - 0.12,
            str(event.Bpass),
            ha="center",
            va="center",
            fontsize=13
        )
    
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]

    ax.set_xlim(min(xs)-1, max(xs)+1)
    ax.set_ylim(min(ys)-1, max(ys)+1)
    
    ax.set_axis_off()

    plt.tight_layout()

    st.pyplot(fig)

if st.button("🚀 Run Analysis", type="primary"):

    if module == "CPM":

        project = Project()

        lookup = {}

        for row in activities_data:

            preds = None

            if "--" not in row["Predecessors"]:
                preds = [
                    lookup[p]
                    for p in row["Predecessors"]
                ]

            act = Activity(
                row["Activity"],
                row["Duration"],
                preds
            )

            lookup[row["Activity"]] = act
            project.add_Activity(act)

    else:

        project = PERT()

        lookup = {}

        for row in activities_data:

            preds = None

            if "--" not in row["Predecessors"]:
                preds = [
                    lookup[p]
                    for p in row["Predecessors"]
                ]

            act = PERTActivity(
                row["Activity"],
                row["Optimistic"],
                row["Most Likely"],
                row["Pessimistic"],
                preds
            )

            lookup[row["Activity"]] = act
            project.add_Activity(act)

    for a in project.activities:
        print(
            a.Activity,
            "nextEvent:",
            None if a.nextEvent is None else a.nextEvent.id
        )
    project.get_paths()

    # ======================================
    # KPIs
    # ======================================

    cp_names = [
        a.Activity
        for a in project.critical_path[0]
    ]

    duration = project.critical_path[1]

    st.divider()

    c1,c2,c3 = st.columns(3)

    c1.metric(
        "Project Duration",
        duration
    )

    c2.metric(
        "Activities",
        len(project.activities)
    )

    c3.metric(
        "Critical Path Length",
        len(cp_names)
    )

    

    # ======================================
    # CRITICAL PATH
    # ======================================

    st.subheader("🔥 Critical Paths")

    st.success(
        " → ".join(cp_names)
    )
    critical_paths = []

    for path in project.paths:

        duration = sum(a.duration for a in path)

        if duration == project.critical_path[1]:
            if path != project.critical_path[0]:
                critical_paths.append(
                    " → ".join(
                        a.Activity for a in path
                    )
                )
    
    if critical_paths:
        st.subheader("Additional Critical Paths")

        for path in critical_paths:
            st.write(path)
    
    if module == "CPM" and analysis_type == "Both":
        TA_CPM(project)
        CA_CPM(project, both=True)


    # TIME ANALYSIS
    if module == "CPM" and analysis_type == "Time Analysis":
        TA_CPM(project)

    # COST ANALYSIS
    if module == "CPM" and analysis_type == "Cost Analysis":
        CA_CPM(project)

    # PERT
    if module == "PERT":
        TA_CPM(project, show_floats=False)

        variance = project.cummulative_variance()

        sd = project.cummulative_standard_deviation()

        st.subheader("📊 PERT Results")

        c1,c2 = st.columns(2)

        c1.metric(
            "Critical Path Variance",
            round(variance,4)
        )

        c2.metric(
            "Standard Deviation",
            round(sd,4)
        )

        pert_table = []

        for a in project.activities:

            pert_table.append({
                "Activity": a.Activity,
                "Expected Time": round(
                    a.expected_time,
                    2
                ),
                "Variance": round(
                    a.variance,
                    4
                )
            })

        st.dataframe(
            pd.DataFrame(pert_table),
            use_container_width=True
        )