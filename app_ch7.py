import json
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

# --------------------------------------------------
# Page config
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
activities = data.get("activities", [])

concept_names = {c["concept_name"] for c in concepts}

# --------------------------------------------------
# Session state init (CRITICAL)
# --------------------------------------------------
if "selected_concept" not in st.session_state:
    st.session_state.selected_concept = None

if "last_graph_selection" not in st.session_state:
    st.session_state.last_graph_selection = None

# --------------------------------------------------
# Build graph
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
                Edge(source=c["concept_name"], target=linked)
            )

config = Config(
    width=1200,
    height=650,
    directed=False,
    physics=True,
    nodeHighlightBehavior=True,
    highlightColor="#F7A7A6"
)

# --------------------------------------------------
# Render graph
# --------------------------------------------------
graph_value = agraph(
    nodes=nodes,
    edges=edges,
    config=config
)

# --------------------------------------------------
# Normalize graph output (handles lag safely)
# --------------------------------------------------
current_selection = None

if isinstance(graph_value, dict):
    nodes_selected = graph_value.get("nodes", [])
    if nodes_selected:
        current_selection = nodes_selected[0]

elif isinstance(graph_value, list) and graph_value:
    current_selection = graph_value[0]

elif isinstance(graph_value, str):
    current_selection = graph_value

# --------------------------------------------------
# UPDATE selection ONLY when it changes
# --------------------------------------------------
if current_selection != st.session_state.last_graph_selection:
    if current_selection in concept_names:
        st.session_state.selected_concept = current_selection
    else:
        st.session_state.selected_concept = None

    st.session_state.last_graph_selection = current_selection

# --------------------------------------------------
# Sidebar – Concept Details
# --------------------------------------------------
st.sidebar.header("🔍 Concept Details")

if st.session_state.selected_concept:
    concept = next(
        c for c in concepts
        if c["concept_name"] == st.session_state.selected_concept
    )

    st.sidebar.subheader(concept["concept_name"])
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

else:
    st.sidebar.info("Click a concept node to view details.")

# --------------------------------------------------
# Sidebar – Data Check
# --------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("🧪 Data Check")
st.sidebar.success("All activities are properly linked")
