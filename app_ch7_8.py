import json
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

# ----------------------------
# Page config
# ----------------------------
st.set_page_config(
    page_title="NCERT Knowledge Graph (Grades 7–8)",
    layout="wide"
)

# ----------------------------
# Load data
# ----------------------------
with open("grade7_knowledge_base.json", "r", encoding="utf-8") as f:
    data_g7 = json.load(f)

with open("grade8_knowledge_base.json", "r", encoding="utf-8") as f:
    data_g8 = json.load(f)

DATA_BY_GRADE = {
    "7": data_g7,
    "8": data_g8
}

# ----------------------------
# Domain colour theme (LOCKED – Grade 7 style)
# ----------------------------
DOMAIN_COLORS = {
    "Physics": "#2563EB",               # Deep Blue
    "Chemistry": "#16A34A",             # Vibrant Green
    "Biology": "#F97316",               # Warm Orange
    "Earth & Space Science": "#8B5CF6", # Purple
    "Earth Science": "#8B5CF6"
}

# ----------------------------
# Sidebar – Grade selector
# ----------------------------
st.sidebar.markdown("### Select Grade")
grade = st.sidebar.radio("Grade", ["7", "8"], horizontal=True)

data = DATA_BY_GRADE[grade]
concepts = data["concepts"]
activities = data["activities"]

# ----------------------------
# Session state
# ----------------------------
if "selected_concept" not in st.session_state:
    st.session_state.selected_concept = None

if "learned_concepts" not in st.session_state:
    st.session_state.learned_concepts = {"7": set(), "8": set()}

# ----------------------------
# Helpers
# ----------------------------
concept_by_name = {c["concept_name"]: c for c in concepts}
activities_by_parent = {}

for a in activities:
    parent = a.get("parent_concept")
    if parent:
        activities_by_parent.setdefault(parent, []).append(a)

# ----------------------------
# Build graph nodes & edges
# ----------------------------
nodes = []
edges = []
node_ids = set()

def add_node(node):
    if node.id not in node_ids:
        nodes.append(node)
        node_ids.add(node.id)

# ---- Domain & Strand aggregation
domains = {}
strands = {}

for c in concepts:
    domains.setdefault(c["domain"], set()).add(c["strand"])
    strands.setdefault((c["domain"], c["strand"]), []).append(c)

# ---- Domain nodes (HEXAGON – LARGE)
for domain in domains:
    add_node(Node(
        id=f"domain::{domain}",
        label=domain,
        shape="hexagon",
        size=55,
        color=DOMAIN_COLORS.get(domain, "#6B7280"),
        font={"size": 18, "color": "white"}
    ))

# ---- Strand nodes (ELLIPSE – MEDIUM)
for domain, strand in domains.items():
    for s in strand:
        add_node(Node(
            id=f"strand::{domain}::{s}",
            label=s,
            shape="ellipse",
            size=38,
            color=DOMAIN_COLORS.get(domain, "#6B7280"),
            font={"size": 14, "color": "white"}
        ))

        edges.append(Edge(
            source=f"domain::{domain}",
            target=f"strand::{domain}::{s}",
            color="#CBD5E1"
        ))

# ---- Concept nodes (DOT – SMALL)
for c in concepts:
    has_activity = c["concept_name"] in activities_by_parent

    add_node(Node(
        id=f"concept::{c['concept_name']}",
        label=c["concept_name"],
        shape="dot",
        size=20,
        color=DOMAIN_COLORS.get(c["domain"], "#2563EB"),
        borderWidth=3 if has_activity else 1,
        borderColor="#111827" if has_activity else "#D1D5DB",
        font={"size": 12}
    ))

    edges.append(Edge(
        source=f"strand::{c['domain']}::{c['strand']}",
        target=f"concept::{c['concept_name']}",
        color="#FCA5A5"
    ))

# ---- Concept ↔ Concept interconnections
concept_names = set(concept_by_name.keys())

for c in concepts:
    for linked in c.get("interconnections", []):
        if linked in concept_names:
            edges.append(Edge(
                source=f"concept::{c['concept_name']}",
                target=f"concept::{linked}",
                color="#E5E7EB",
                dashes=True
            ))

# ----------------------------
# Graph config
# ----------------------------
config = Config(
    width="100%",
    height=700,
    directed=False,
    physics=True,
    hierarchical=False,
    nodeHighlightBehavior=True,
    highlightColor="#000000"
)

# ----------------------------
# Render
# ----------------------------
st.markdown("## 📘 NCERT Knowledge Graph")
selected = agraph(nodes=nodes, edges=edges, config=config)

# ----------------------------
# Selection handling
# ----------------------------
if selected and selected.startswith("concept::"):
    concept_name = selected.replace("concept::", "")
    st.session_state.selected_concept = concept_name

# ----------------------------
# Sidebar – Concept details
# ----------------------------
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Concept Details")

selected_concept = st.session_state.selected_concept

if not selected_concept:
    st.sidebar.info("Click a concept node to view details.")
else:
    c = concept_by_name[selected_concept]

    st.sidebar.markdown(f"### {selected_concept}")
    st.sidebar.write(c["brief_explanation"])

    st.sidebar.markdown("**Chapters**")
    for ch in c.get("chapter_references", []):
        st.sidebar.write(f"- {ch}")

    st.sidebar.markdown("**Concept Type**")
    st.sidebar.write(c.get("concept_type", "—"))

    st.sidebar.markdown("**Cognitive Level**")
    st.sidebar.write(c.get("cognitive_level", "—"))

    # ---- Activities
    related_acts = activities_by_parent.get(selected_concept, [])

    if related_acts:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🧪 Learning Activities")

        for a in related_acts:
            st.sidebar.markdown(f"**{a['activity_name']}**")
            st.sidebar.write(f"Type: {a['activity_type']}")
            st.sidebar.write(a["learning_goal"])

    # ---- Mark as learned
    st.sidebar.markdown("---")
    learned = selected_concept in st.session_state.learned_concepts[grade]

    if st.sidebar.checkbox("Mark concept as learned", value=learned):
        st.session_state.learned_concepts[grade].add(selected_concept)
    else:
        st.session_state.learned_concepts[grade].discard(selected_concept)
