import json
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

# ----------------------------
# Page config
# ----------------------------
st.set_page_config(
    page_title="NCERT Grades 7–8 – Knowledge Graph",
    layout="wide"
)

# ----------------------------
# Load data
# ----------------------------
@st.cache_data
def load_all_data():
    with open("data/grade7_knowledge_base.json", "r", encoding="utf-8") as f:
        grade7 = json.load(f)

    with open("data/grade8_knowledge_base.json", "r", encoding="utf-8") as f:
        grade8 = json.load(f)

    return {
        "7": grade7,
        "8": grade8
    }

ALL_DATA = load_all_data()

st.sidebar.markdown("## 📘 Curriculum")

grade = st.sidebar.radio(
    "Select Grade",
    ["7", "8"],
    horizontal=True
)

data = ALL_DATA[grade]

concepts = data["concepts"]
activities = data["activities"]
concept_map = {c["concept_name"]: c for c in concepts}
concept_names = set(concept_map.keys())

# ----------------------------
# Session state
# ----------------------------

if "selected_concept" not in st.session_state:
    st.session_state.selected_concept = None
elif st.session_state.selected_concept not in concept_names:
    st.session_state.selected_concept = None

if "learned_concepts" not in st.session_state:
    st.session_state.learned_concepts = {"7": set(), "8": set()}

# ----------------------------
# Build Tier 1 & Tier 2 structure
# ----------------------------
domains = {}
strands = {}

for c in concepts:
    domains.setdefault(c["domain"], set()).add(c["strand"])
    strands.setdefault((c["domain"], c["strand"]), []).append(c["concept_name"])

# ----------------------------
# Colors (Domain-based)
# ----------------------------
DOMAIN_COLORS = {
    "Physics (The Physical World)": "#1f77b4",
    "Chemistry (The World of Matter)": "#2ca02c",
    "Biology (The Living World)": "#ff7f0e",
    "Earth & Space Science": "#9467bd",
    "Scientific Inquiry & Investigative Process": "#7f7f7f"
}

# ----------------------------
# Build nodes
# ----------------------------
nodes = []

# Tier 1 — Domain anchors
for domain in domains:
    nodes.append(
        Node(
            id=f"domain::{domain}",
            label=domain,
            size=45,
            color=DOMAIN_COLORS.get(domain, "#999999"),
            font={"size": 20, "bold": True},
            shape="box"
        )
    )

# Tier 2 — Strand anchors
for (domain, strand) in strands:
    nodes.append(
        Node(
            id=f"strand::{strand}",
            label=strand,
            size=30,
            color=DOMAIN_COLORS.get(domain, "#bbbbbb"),
            font={"size": 16},
            shape="ellipse"
        )
    )

# Tier 3 — Concept nodes
for c in concepts:
    nodes.append(
        Node(
            id=f"concept::{c['concept_name']}",
            label=c["concept_name"],
            size=18,
            color=DOMAIN_COLORS.get(c["domain"], "#cccccc"),
            shape="dot"
        )
    )

# ----------------------------
# Build edges
# ----------------------------
edges = []

# Domain → Strand
for domain, strand_list in domains.items():
    for strand in strand_list:
        edges.append(
            Edge(
    source=f"domain::{domain}",
    target=f"strand::{strand}",
    color="#cccccc"
)
        )

# Strand → Concept
for (domain, strand), concept_list in strands.items():
    for concept in concept_list:
        edges.append(
           Edge(
    source=f"strand::{strand}",
    target=f"concept::{concept}",
    color="#dddddd"
)
        )

# Concept ↔ Concept (interconnections)
for c in concepts:
    for linked in c.get("interconnections", []):
        if linked in concept_names:
            edges.append(
                Edge(
    source=f"concept::{c['concept_name']}",
    target=f"concept::{linked}",
    color="#ff9999"
)
            )

# ----------------------------
# Graph config
# ----------------------------
config = Config(
    width="100%",
    height=750,
    directed=False,
    physics=True,
    hierarchical=False,
    nodeHighlightBehavior=True,
    highlightColor="#F7A7A6"
)

# ----------------------------
# UI layout
# ----------------------------
st.markdown(f"## 📘 NCERT Grade {grade} – Knowledge Graph")

selected = agraph(nodes=nodes, edges=edges, config=config)

# ----------------------------
# Normalize click result
# ----------------------------
clicked = None

if isinstance(selected, dict):
    if selected.get("nodes"):
        clicked = selected["nodes"][0]
elif isinstance(selected, list) and selected:
    clicked = selected[0]
elif isinstance(selected, str):
    clicked = selected

if isinstance(clicked, str) and clicked.startswith("concept::"):
    st.session_state.selected_concept = clicked.replace("concept::", "")

# ----------------------------
# Sidebar — Concept Details
# ----------------------------
st.sidebar.markdown("## 🔍 Concept Details")

selected_concept = st.session_state.selected_concept

if selected_concept:
    concept = concept_map[selected_concept]

    st.sidebar.markdown(f"### {selected_concept}")
    st.sidebar.write(concept["brief_explanation"])

    st.sidebar.markdown("**Domain**")
    st.sidebar.write(concept["domain"])

    st.sidebar.markdown("**Strand**")
    st.sidebar.write(concept["strand"])

    st.sidebar.markdown("**Chapters**")
    for ch in concept.get("chapter_references", []):
        st.sidebar.write(f"• {ch}")

    st.sidebar.markdown("**Cognitive Level**")
    st.sidebar.write(concept.get("cognitive_level", "—"))

# ----------------------------
# Mark as learned (grade-scoped)
# ----------------------------
learned = selected_concept in st.session_state.learned_concepts[grade]

checked = st.sidebar.checkbox(
    "✅ Mark concept as learned",
    value=learned
)

if checked:
    st.session_state.learned_concepts[grade].add(selected_concept)
else:
    st.session_state.learned_concepts[grade].discard(selected_concept)

    # ----------------------------
    # Activities (lightweight)
    # ----------------------------
    linked_activities = [
        a for a in activities
        if a.get("parent_concept") == selected_concept
    ]

    with st.sidebar.expander(f"🧪 Learning Activities ({len(linked_activities)})"):
        if linked_activities:
            for a in linked_activities:
                st.write(f"• {a['activity_name']}")
        else:
            st.write("No activities linked to this concept.")

else:
    st.sidebar.info("Click a concept node to view details.")


