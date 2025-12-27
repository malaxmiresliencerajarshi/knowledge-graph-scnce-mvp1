import json
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(layout="wide", page_title="NCERT Knowledge Graph")

# -----------------------------
# Load data (both grades in code)
# -----------------------------
with open("data/grade7_knowledge_base.json", "r", encoding="utf-8") as f:
    grade7 = json.load(f)

with open("data/grade8_knowledge_base.json", "r", encoding="utf-8") as f:
    grade8 = json.load(f)

DATA_BY_GRADE = {
    7: grade7,
    8: grade8
}

# -----------------------------
# Domain color theme (single color flows down)
# -----------------------------
DOMAIN_COLORS = {
    "Physics (The Physical World)": "#2563eb",       # Deep Blue
    "Chemistry (The World of Matter)": "#16a34a",    # Green
    "Biology (The Living World)": "#ea580c",         # Orange
    "Earth & Space Science": "#7c3aed",              # Purple
    "Scientific Inquiry & Investigative Process": "#6b7280"  # Grey
}

# -----------------------------
# Sidebar – Grade selector
# -----------------------------
st.sidebar.header("Select Grade")
grade = st.sidebar.radio("Grade", [7, 8], horizontal=True)

data = DATA_BY_GRADE[grade]
concepts = data["concepts"]
activities = data.get("activities", [])

# -----------------------------
# Session state
# -----------------------------
if "selected_concept" not in st.session_state:
    st.session_state.selected_concept = None

if "learned" not in st.session_state:
    st.session_state.learned = set()

# -----------------------------
# Helper maps
# -----------------------------
concept_map = {c["concept_name"]: c for c in concepts}

activities_by_concept = {}
for a in activities:
    parent = a.get("parent_concept")
    if parent:
        activities_by_concept.setdefault(parent, []).append(a)

# -----------------------------
# Build graph
# -----------------------------
nodes = []
edges = []

# ---- Domains (RECTANGLE, BIG, behind)
domains = sorted(set(c["domain"] for c in concepts))

for d in domains:
    color = DOMAIN_COLORS.get(d, "#64748b")
    nodes.append(Node(
        id=f"domain::{d}",
        label=d.replace(" (", "\n("),
        shape="box",
        size=90,
        level=0,
        color=color,
        font={"size": 18, "color": "white"}
    ))

# ---- Strands (ELLIPSE, medium)
strands = sorted(set((c["domain"], c["strand"]) for c in concepts))

for domain, strand in strands:
    nodes.append(Node(
        id=f"strand::{domain}::{strand}",
        label=strand,
        shape="ellipse",
        size=45,
        level=1,
        color=DOMAIN_COLORS.get(domain, "#64748b"),
        font={"size": 14, "color": "white"}
    ))

    edges.append(Edge(
        source=f"domain::{domain}",
        target=f"strand::{domain}::{strand}",
        color="#cbd5f5"
    ))

# ---- Concepts (DOTS, small, clickable)
for c in concepts:
    name = c["concept_name"]
    domain = c["domain"]
    strand = c["strand"]

    has_activity = name in activities_by_concept
    border = "#111827" if has_activity else DOMAIN_COLORS.get(domain)

    nodes.append(Node(
        id=f"concept::{name}",
        label=name,
        shape="dot",
        size=22,
        level=2,
        color=DOMAIN_COLORS.get(domain),
        borderWidth=3 if has_activity else 1,
        borderColor=border
    ))

    edges.append(Edge(
        source=f"strand::{domain}::{strand}",
        target=f"concept::{name}",
        color="#94a3b8"
    ))

    # Concept ↔ Concept links
    for linked in c.get("interconnections", []):
        if linked in concept_map:
            edges.append(Edge(
                source=f"concept::{name}",
                target=f"concept::{linked}",
                color="#fca5a5"
            ))

# -----------------------------
# Graph config (CLICK SAFE)
# -----------------------------
config = Config(
    width=1200,
    height=750,
    directed=False,
    physics=True,
    hierarchical=False,
    interaction={
        "hover": True,
        "selectable": True,
        "multiselect": False
    }
)

# -----------------------------
# Render graph
# -----------------------------
st.title("📘 NCERT Knowledge Graph")

result = agraph(
    nodes=nodes,
    edges=edges,
    config=config
)

# ---- Handle node click (agraph v0.0.45 compatible) ----
if result and isinstance(result, dict):
    clicked_nodes = result.get("nodes", [])
    if clicked_nodes:
        node_id = clicked_nodes[0].get("id", "")

        if node_id.startswith("concept::"):
            st.session_state.selected_concept = node_id.replace("concept::", "")

    # ---- Activities dropdown
    acts = activities_by_concept.get(selected, [])
    if acts:
        with st.sidebar.expander("📌 Learning Activities"):
            for a in acts:
                st.markdown(f"**{a['activity_name']}**")
                st.write(f"Type: {a.get('activity_type','-')}")
                st.write(f"Goal: {a.get('learning_goal','-')}")
                st.divider()

else:
    st.sidebar.info("Click a concept node to view details.")

