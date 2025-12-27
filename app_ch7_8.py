import json
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

# ------------------------------------------------------------
# Page config
# ------------------------------------------------------------
st.set_page_config(page_title="NCERT Knowledge Graph", layout="wide")

# ------------------------------------------------------------
# Load data (Grade 7 + Grade 8 embedded)
# ------------------------------------------------------------
with open("data/grade7_knowledge_base.json", "r", encoding="utf-8") as f:
    grade7_data = json.load(f)

with open("data/grade8_knowledge_base.json", "r", encoding="utf-8") as f:
    grade8_data = json.load(f)

DATA_BY_GRADE = {
    7: grade7_data,
    8: grade8_data
}

# ------------------------------------------------------------
# Sidebar – Grade selector
# ------------------------------------------------------------
st.sidebar.markdown("## Select Grade")
grade = st.sidebar.radio("Grade", [7, 8], horizontal=True)

data = DATA_BY_GRADE[grade]
concepts = data["concepts"]

# ------------------------------------------------------------
# Color theme (domain → strand → concept)
# ------------------------------------------------------------
DOMAIN_COLORS = {
    "Physics (The Physical World)": "#2563EB",       # Deep Blue
    "Chemistry (The World of Matter)": "#16A34A",    # Green
    "Biology (The Living World)": "#EA580C",         # Orange
    "Earth & Space Science": "#7C3AED",              # Purple
    "Scientific Inquiry & Investigative Process": "#6B7280"  # Grey
}

# ------------------------------------------------------------
# Build lookups
# ------------------------------------------------------------
concept_lookup = {c["concept_name"]: c for c in concepts}
concept_names = set(concept_lookup.keys())

domains = sorted(set(c["domain"] for c in concepts))
strands = sorted(set(c["strand"] for c in concepts))

# ------------------------------------------------------------
# Session state
# ------------------------------------------------------------
if "selected_concept" not in st.session_state:
    st.session_state.selected_concept = None

if "learned_concepts" not in st.session_state:
    st.session_state.learned_concepts = {7: set(), 8: set()}

# ------------------------------------------------------------
# Graph nodes & edges
# ------------------------------------------------------------
nodes = []
edges = []

# ---- Domain nodes (RECTANGLE – BIG)
for domain in domains:
    nodes.append(Node(
        id=f"domain::{domain}",
        label=domain,
        shape="box",
        size=60,
        color=DOMAIN_COLORS.get(domain, "#9CA3AF"),
        font={"size": 20, "color": "white"}
    ))

# ---- Strand nodes (ELLIPSE – MEDIUM)
for strand in strands:
    domain = next(c["domain"] for c in concepts if c["strand"] == strand)
    nodes.append(Node(
        id=f"strand::{strand}",
        label=strand,
        shape="ellipse",
        size=40,
        color=DOMAIN_COLORS.get(domain, "#9CA3AF"),
        font={"size": 16, "color": "white"}
    ))

    edges.append(Edge(
        source=f"domain::{domain}",
        target=f"strand::{strand}",
        color="#CBD5E1",
        width=1
    ))

# ---- Concept nodes (DOT – SMALL)
for c in concepts:
    domain = c["domain"]
    concept_id = c["concept_name"]

    border_width = 3 if c.get("activities") else 1

    nodes.append(Node(
        id=f"concept::{concept_id}",
        label=concept_id,
        shape="dot",
        size=18,
        color=DOMAIN_COLORS.get(domain, "#9CA3AF"),
        borderWidth=border_width,
        borderColor="#111827",
        font={"size": 12}
    ))

    edges.append(Edge(
        source=f"strand::{c['strand']}",
        target=f"concept::{concept_id}",
        color="#E5E7EB",
        width=1
    ))

# ---- Concept ↔ Concept links
for c in concepts:
    for linked in c.get("interconnections", []):
        if linked in concept_names:
            edges.append(Edge(
                source=f"concept::{c['concept_name']}",
                target=f"concept::{linked}",
                color="#FCA5A5",
                width=1
            ))

# ------------------------------------------------------------
# Graph config
# ------------------------------------------------------------
config = Config(
    width="100%",
    height=720,
    directed=False,
    physics=True,
    hierarchical=False,
    nodeHighlightBehavior=True,
    highlightColor="#F59E0B",
    interaction={
        "hover": True,
        "selectable": True,
        "multiselect": False,
        "dragNodes": True,
        "dragView": True,
        "zoomView": True
    }
)

# ------------------------------------------------------------
# Title
# ------------------------------------------------------------
st.markdown("## 📘 NCERT Knowledge Graph")

# ------------------------------------------------------------
# Render graph
# ------------------------------------------------------------
clicked = agraph(nodes=nodes, edges=edges, config=config)

# ------------------------------------------------------------
# Handle click (ONLY concepts)
# ------------------------------------------------------------
selected_concept = None

if clicked and isinstance(clicked, dict):
    node_id = clicked.get("id", "")
    if node_id.startswith("concept::"):
        selected_concept = node_id.replace("concept::", "")
        st.session_state.selected_concept = selected_concept

# ------------------------------------------------------------
# Sidebar – Concept details
# ------------------------------------------------------------
st.sidebar.markdown("## 🔍 Concept Details")

selected_concept = st.session_state.selected_concept

if selected_concept:
    concept = concept_lookup[selected_concept]

    with st.sidebar.expander("📖 Concept Information", expanded=True):
        st.markdown(f"**Brief Explanation**")
        st.write(concept["brief_explanation"])

        st.markdown(f"**Chapter References**")
        st.write(concept["chapter_references"])

        st.markdown(f"**Concept Type**")
        st.write(concept["concept_type"])

        st.markdown(f"**Cognitive Level**")
        st.write(concept["cognitive_level"])

    if concept.get("activities"):
        with st.sidebar.expander("🧪 Learning Activities", expanded=False):
            for a in concept["activities"]:
                st.markdown(f"**{a['activity_name']}**")
                st.write(f"Type: {a['activity_type']}")
                st.write(f"Goal: {a['learning_goal']}")
                st.divider()

    learned = selected_concept in st.session_state.learned_concepts[grade]
    checked = st.sidebar.checkbox(
        "✔ Mark concept as learned",
        value=learned
    )

    if checked:
        st.session_state.learned_concepts[grade].add(selected_concept)
    else:
        st.session_state.learned_concepts[grade].discard(selected_concept)

else:
    st.sidebar.info("Click a concept node to view details.")
