import json
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

# --------------------------------------------------
# Page configuration
# --------------------------------------------------
st.set_page_config(
    page_title="NCERT Grade 7 Knowledge Graph",
    layout="wide"
)

st.title("📘 NCERT Grade 7 – Knowledge Graph")

# --------------------------------------------------
# Load data
# --------------------------------------------------
@st.cache_data
def load_data():
    with open("data/grade7_knowledge_base.json", "r", encoding="utf-8") as f:
        return json.load(f)

data = load_data()
concepts = data.get("concepts", [])
raw_activities = data.get("activities", [])

concept_names = {c["concept_name"] for c in concepts}

# --------------------------------------------------
# Clean activities (STRICT)
# --------------------------------------------------
activities = []
for a in raw_activities:
    if isinstance(a, dict) and "activity_name" in a and "parent_concept" in a:
        activities.append(a)

# --------------------------------------------------
# Sidebar – Concept details
# --------------------------------------------------
st.sidebar.header("🔍 Concept Details")

selected_concept = st.session_state.get("selected_concept")

if st.session_state.get("selected_concept") in concept_names:
    concept = next(
        (c for c in concepts if c["concept_name"] == selected_concept),
        None
    )

    if concept:
        st.sidebar.subheader(selected_concept)
        st.sidebar.write(concept.get("brief_explanation", "—"))

        st.sidebar.markdown("**Domain**")
        st.sidebar.write(concept.get("domain", "—"))

        st.sidebar.markdown("**Strand**")
        st.sidebar.write(concept.get("strand", "—"))

        st.sidebar.markdown("**Chapters**")
        for ch in concept.get("chapter_references", []):
            st.sidebar.write(f"• {ch}")

        st.sidebar.markdown("**Cognitive Level**")
        st.sidebar.write(concept.get("cognitive_level", "—"))

        st.sidebar.markdown("**Activities**")
        linked_activities = [
            a for a in activities
            if a["parent_concept"] == selected_concept
        ]

        if linked_activities:
            for a in linked_activities:
                st.sidebar.write(f"• {a['activity_name']}")
        else:
            st.sidebar.write("No activities linked.")
else:
    st.sidebar.info("Click a concept node to view details.")

# --------------------------------------------------
# Sidebar – Data Quality Check
# --------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("🧪 Data Check")

unlinked_activities = [
    a for a in activities
    if a["parent_concept"] not in concept_names
]

if unlinked_activities:
    st.sidebar.warning("Activities NOT linked to any concept")
    for a in unlinked_activities:
        st.sidebar.write(
            f"• {a['activity_name']} (parent → {a['parent_concept']})"
        )
else:
    st.sidebar.success("All activities are properly linked")

# --------------------------------------------------
# Build graph (Tier-3 concepts only)
# --------------------------------------------------
nodes = []
edges = []

for c in concepts:
    nodes.append(
        Node(
            id=c["concept_name"],
            label=c["concept_name"],
            size=18,
            color="#1f77b4"
        )
    )

    for linked in c.get("interconnections", []):
        if linked in concept_names:
            edges.append(
                Edge(
                    source=c["concept_name"],
                    target=linked
                )
            )

config = Config(
    width=1200,
    height=650,
    directed=False,
    physics=True,
    hierarchical=False,
    nodeHighlightBehavior=True,
    highlightColor="#F7A7A6"
)

# --------------------------------------------------
# Render graph + FIX node click behavior (NO key)
# --------------------------------------------------
selected = agraph(
    nodes=nodes,
    edges=edges,
    config=config
)

# Normalize agraph output safely
normalized_selection = None

if isinstance(selected, dict):
    # Example: {"nodes": ["Groundwater"], "edges": []}
    nodes_selected = selected.get("nodes", [])
    if nodes_selected:
        normalized_selection = nodes_selected[0]

elif isinstance(selected, list) and selected:
    normalized_selection = selected[0]

elif isinstance(selected, str):
    normalized_selection = selected

# Force overwrite of selection every run
if normalized_selection and normalized_selection in concept_names:
    st.session_state["selected_concept"] = normalized_selection
else:
    # Explicitly clear when nothing valid is selected
    st.session_state["selected_concept"] = None



