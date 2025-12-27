import json
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

# --------------------------------------------------
# Page config
# --------------------------------------------------
st.set_page_config(
    page_title="NCERT Knowledge Graph",
    layout="wide"
)

# --------------------------------------------------
# Domain colors (LOCKED)
# --------------------------------------------------
DOMAIN_COLORS = {
    "Physics (The Physical World)": "#2563EB",          # Deep Blue
    "Chemistry (The World of Matter)": "#16A34A",       # Vibrant Green
    "Biology (The Living World)": "#F97316",            # Warm Orange
    "Earth & Space Science": "#8B5CF6",                 # Purple
    "Scientific Inquiry & Investigative Process": "#6B7280"  # Slate Grey
}


# --------------------------------------------------
# Load data (Grade 7 + Grade 8)
# --------------------------------------------------
with open("data/grade7_knowledge_base.json", "r", encoding="utf-8") as f:
    grade7_data = json.load(f)

with open("data/grade8_knowledge_base.json", "r", encoding="utf-8") as f:
    grade8_data = json.load(f)

# --------------------------------------------------
# Sidebar: Grade selector
# --------------------------------------------------
st.sidebar.markdown("## Select Grade")
grade = st.sidebar.radio("Grade", ["7", "8"], horizontal=True)

data = grade7_data if grade == "7" else grade8_data
concepts = data["concepts"]
activities = data["activities"]

# --------------------------------------------------
# Session state
# --------------------------------------------------
if "selected_concept" not in st.session_state:
    st.session_state.selected_concept = None

if "learned_concepts" not in st.session_state:
    st.session_state.learned_concepts = {"7": set(), "8": set()}

# --------------------------------------------------
# Helper mappings
# --------------------------------------------------
concept_lookup = {c["concept_name"]: c for c in concepts}

activity_map = {}
for a in activities:
    parent = a.get("parent_concept")
    if parent:
        activity_map.setdefault(parent, []).append(a)

# --------------------------------------------------
# Build graph nodes
# --------------------------------------------------
nodes = []
edges = []

domains = {}
strands = {}

# ---- Domain + Strand discovery
for c in concepts:
    domains.setdefault(c["domain"], set()).add(c["strand"])

# ---- Domain nodes (HEXAGON)
for domain in domains:
    nodes.append(Node(
        id=f"domain::{domain}",
        label=domain,
        shape="hexagon",
        size=55,
        color=DOMAIN_COLORS[domain],
        font={"size": 18, "color": "white"}
    ))

# ---- Strand nodes (ELLIPSE)
for domain, strand_set in domains.items():
    for strand in strand_set:
        strand_id = f"strand::{domain}::{strand}"
        nodes.append(Node(
            id=strand_id,
            label=strand,
            shape="ellipse",
            size=38,
            color=DOMAIN_COLORS[domain],
            font={"size": 14, "color": "white"}
        ))
        edges.append(Edge(
            source=f"domain::{domain}",
            target=strand_id,
            color=DOMAIN_COLORS[domain],
            width=2
        ))
        strands[strand_id] = domain

# ---- Concept nodes (DOT)
for c in concepts:
    domain = c["domain"]
    strand_id = f"strand::{domain}::{c['strand']}"
    concept_id = f"concept::{c['concept_name']}"

    has_activity = c["concept_name"] in activity_map
    is_selected = st.session_state.selected_concept == c["concept_name"]

    nodes.append(Node(
        id=concept_id,
        label=c["concept_name"],
        shape="dot",
        size=20,
        color=DOMAIN_COLORS[domain],
        borderWidth=3 if has_activity else 1,
        borderColor="#111827" if has_activity else "#D1D5DB",
        opacity=1.0 if (not st.session_state.selected_concept or is_selected) else 0.25,
        font={"size": 12}
    ))

    edges.append(Edge(
        source=strand_id,
        target=concept_id,
        color=DOMAIN_COLORS[domain],
        width=1
    ))

# ---- Concept interconnections
concept_names = set(concept_lookup.keys())

for c in concepts:
    for linked in c.get("interconnections", []):
        if linked in concept_names:
            edges.append(Edge(
                source=f"concept::{c['concept_name']}",
                target=f"concept::{linked}",
                color="#CBD5E1",
                width=1,
                dashes=True
            ))

# --------------------------------------------------
# Graph config
# --------------------------------------------------
config = Config(
    width="100%",
    height=700,
    directed=False,
    physics=True,
    hierarchical=False,
    nodeHighlightBehavior=False,
    highlightColor="#FACC15",
    linkHighlightBehavior=False
)

# --------------------------------------------------
# Render graph
# --------------------------------------------------
st.markdown("## 📘 NCERT Knowledge Graph")

result = agraph(
    nodes=nodes,
    edges=edges,
    config=config
)

# --------------------------------------------------
# Handle node click
# --------------------------------------------------
if result and isinstance(result, dict):
    clicked = result.get("node")
    if clicked and clicked.startswith("concept::"):
        st.session_state.selected_concept = clicked.replace("concept::", "")

# --------------------------------------------------
# Sidebar: Concept details
# --------------------------------------------------
st.sidebar.markdown("## 🔍 Concept Details")

selected = st.session_state.selected_concept

if not selected:
    st.sidebar.info("Click a concept node to view details.")
else:
    c = concept_lookup[selected]

    st.sidebar.markdown(f"### {selected}")
    st.sidebar.write(c["brief_explanation"])

    st.sidebar.markdown("**Chapters**")
    for ch in c["chapter_references"]:
        st.sidebar.write(f"- {ch}")

    st.sidebar.markdown(f"**Concept Type:** {c['concept_type']}")
    st.sidebar.markdown(f"**Cognitive Level:** {c['cognitive_level']}")

    # ---- Activities
    if selected in activity_map:
        st.sidebar.markdown("### 🧪 Activities")
        for a in activity_map[selected]:
            st.sidebar.markdown(f"**{a['activity_name']}**")
            st.sidebar.write(f"- Type: {a['activity_type']}")
            st.sidebar.write(f"- Goal: {a['learning_goal']}")

    # ---- Mark as learned
    learned = selected in st.session_state.learned_concepts[grade]
    if st.sidebar.checkbox("Mark concept as learned", value=learned):
        st.session_state.learned_concepts[grade].add(selected)
    else:
        st.session_state.learned_concepts[grade].discard(selected)


