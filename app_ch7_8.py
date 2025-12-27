import json
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="NCERT Knowledge Graph (Grades 7–8)",
    layout="wide"
)

st.title("📘 NCERT Knowledge Graph (Grades 7 & 8)")

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
with open("data/grade7_knowledge_base.json", "r", encoding="utf-8") as f:
    grade7 = json.load(f)

with open("data/grade8_knowledge_base.json", "r", encoding="utf-8") as f:
    grade8 = json.load(f)

# -------------------------------------------------
# SIDEBAR — GRADE SELECT
# -------------------------------------------------
grade = st.sidebar.radio("Select Grade", ["7", "8"], horizontal=True)

data = grade7 if grade == "7" else grade8
concepts = data["concepts"]
activities = data["activities"]

# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
if "selected_concept" not in st.session_state:
    st.session_state.selected_concept = None

if "learned_concepts" not in st.session_state:
    st.session_state.learned_concepts = {"7": set(), "8": set()}

# -------------------------------------------------
# COLOR MAP (DOMAIN → COLOR)
# -------------------------------------------------
DOMAIN_COLORS = {
    "Physics": "#1E3A8A",
    "Chemistry": "#15803D",
    "Biology": "#EA580C",
    "Earth & Space Science": "#7C4A03",
    "Earth Science": "#7C4A03",
    "Scientific Inquiry & Investigative Process": "#374151"
}

# -------------------------------------------------
# HELPERS
# -------------------------------------------------
concept_map = {c["concept_name"]: c for c in concepts}
concept_names = set(concept_map.keys())

concepts_with_activities = {
    a["parent_concept"]
    for a in activities
    if a.get("parent_concept") in concept_names
}

# -------------------------------------------------
# BUILD NODES
# -------------------------------------------------
nodes = []

# ---- Domains (Tier 1) ----
domains = sorted({c["domain"] for c in concepts})
for d in domains:
    nodes.append(
        Node(
            id=f"domain::{d}",
            label=d,
            shape="hexagon",
            size=60,
            color=DOMAIN_COLORS.get(d, "#374151")
        )
    )

# ---- Strands (Tier 2) ----
strands = sorted({c["strand"] for c in concepts})
for s in strands:
    nodes.append(
        Node(
            id=f"strand::{s}",
            label=s,
            shape="ellipse",
            size=38,
            color="#6B7280"
        )
    )

# ---- Concepts (Tier 3) ----
for c in concepts:
    name = c["concept_name"]
    domain = c["domain"]
    has_activity = name in concepts_with_activities

    nodes.append(
        Node(
            id=f"concept::{name}",
            label=name,
            shape="dot",
            size=22,
            color=DOMAIN_COLORS.get(domain, "#2563EB"),
            borderWidth=3 if has_activity else 1,
            borderColor="#111827" if has_activity else "#D1D5DB"
        )
    )

# -------------------------------------------------
# BUILD EDGES
# -------------------------------------------------
edges = []

# Domain → Strand
for c in concepts:
    edges.append(
        Edge(
            source=f"domain::{c['domain']}",
            target=f"strand::{c['strand']}",
            color="#9CA3AF"
        )
    )

# Strand → Concept
for c in concepts:
    edges.append(
        Edge(
            source=f"strand::{c['strand']}",
            target=f"concept::{c['concept_name']}",
            color="#CBD5E1"
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
                    color="#F97316"
                )
            )

# -------------------------------------------------
# RENDER GRAPH
# -------------------------------------------------
config = Config(
    width=1000,
    height=700,
    directed=False,
    physics=True,
    hierarchical=False
)

clicked = agraph(nodes=nodes, edges=edges, config=config)

if clicked and clicked.startswith("concept::"):
    st.session_state.selected_concept = clicked.replace("concept::", "")

# -------------------------------------------------
# SIDEBAR — DETAILS
# -------------------------------------------------
st.sidebar.divider()
st.sidebar.subheader("🔍 Concept Details")

if st.session_state.selected_concept:
    c = concept_map[st.session_state.selected_concept]

    st.sidebar.markdown(f"### {c['concept_name']}")
    st.sidebar.write(c["brief_explanation"])

    st.sidebar.markdown("**Chapter References**")
    for ch in c["chapter_references"]:
        st.sidebar.write(f"• {ch}")

    st.sidebar.markdown("**Concept Type**")
    st.sidebar.write(c["concept_type"])

    st.sidebar.markdown("**Cognitive Level**")
    st.sidebar.write(c["cognitive_level"])

    linked_acts = [
        a for a in activities
        if a.get("parent_concept") == c["concept_name"]
    ]

    if linked_acts:
        st.sidebar.divider()
        st.sidebar.markdown("### 🧪 Learning Activities")

        for a in linked_acts:
            st.sidebar.markdown(f"**{a['activity_name']}**")
            st.sidebar.write(f"Type: {a['activity_type']}")
            st.sidebar.write(a["learning_goal"])
            st.sidebar.markdown("---")

    # Mark as learned (checkbox only)
    learned = c["concept_name"] in st.session_state.learned_concepts[grade]
    checked = st.sidebar.checkbox("✔ Mark concept as learned", value=learned)

    if checked:
        st.session_state.learned_concepts[grade].add(c["concept_name"])
    else:
        st.session_state.learned_concepts[grade].discard(c["concept_name"])

else:
    st.sidebar.info("Click a concept node to view details.")

# -------------------------------------------------
# LEGEND
# -------------------------------------------------
with st.sidebar.expander("🎨 Legend"):
    st.markdown("⬢ **Hexagon** → Domain")
    st.markdown("⬭ **Ellipse** → Strand")
    st.markdown("● **Dot** → Concept")
    st.markdown("⬛ **Dark border** → Has learning activity")

