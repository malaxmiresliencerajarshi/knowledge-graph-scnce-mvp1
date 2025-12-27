import json
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

# -----------------------------------
# PAGE CONFIG
# -----------------------------------
st.set_page_config(
    page_title="NCERT Knowledge Graph (Grades 7–8)",
    layout="wide"
)

st.title("📘 NCERT Knowledge Graph (Grades 7 & 8)")

# -----------------------------------
# LOAD DATA
# -----------------------------------
with open("grade7_knowledge_base.json", "r", encoding="utf-8") as f:
    grade7 = json.load(f)

with open("grade8_knowledge_base.json", "r", encoding="utf-8") as f:
    grade8 = json.load(f)

# -----------------------------------
# SIDEBAR — GRADE SELECT
# -----------------------------------
grade = st.sidebar.radio("Select Grade", ["7", "8"], horizontal=True)

data = grade7 if grade == "7" else grade8
concepts = data["concepts"]
activities = data["activities"]

# -----------------------------------
# SESSION STATE
# -----------------------------------
if "selected_concept" not in st.session_state:
    st.session_state.selected_concept = None

if "learned_concepts" not in st.session_state:
    st.session_state.learned_concepts = {"7": set(), "8": set()}

learned_set = st.session_state.learned_concepts[grade]

# -----------------------------------
# HELPERS
# -----------------------------------
concept_map = {c["concept_name"]: c for c in concepts}
concept_names = set(concept_map.keys())

concepts_with_activities = {
    a["parent_concept"]
    for a in activities
    if a.get("parent_concept") in concept_names
}

# -----------------------------------
# BUILD NODES
# -----------------------------------
nodes = []

# --- Tier 1 (Domains) ---
domains = sorted({c["domain"] for c in concepts})
for d in domains:
    nodes.append(Node(
        id=f"domain::{d}",
        label=d,
        size=55,
        color="#4A148C",
        shape="box"
    ))

# --- Tier 2 (Strands) ---
strands = sorted({c["strand"] for c in concepts})
for s in strands:
    nodes.append(Node(
        id=f"strand::{s}",
        label=s,
        size=40,
        color="#6A1B9A",
        shape="ellipse"
    ))

# --- Tier 3 (Concepts) ---
for c in concepts:
    name = c["concept_name"]
    selected = (st.session_state.selected_concept == name)
    learned = name in learned_set
    has_activity = name in concepts_with_activities

    # Color logic
    if selected:
        color = "#FF9800"
    elif learned:
        color = "#BDBDBD"
    else:
        color = "#1f77b4"

    nodes.append(Node(
        id=f"concept::{name}",
        label=name,
        size=42 if selected else 26,
        color=color,
        opacity=1.0 if (not st.session_state.selected_concept or selected) else 0.35,
        borderWidth=3 if has_activity else 1,
        borderColor="#2ECC71" if has_activity else "#CCCCCC"
    ))

# -----------------------------------
# BUILD EDGES
# -----------------------------------
edges = []

# Domain → Strand
for c in concepts:
    edges.append(Edge(
        source=f"domain::{c['domain']}",
        target=f"strand::{c['strand']}",
        color="#9C27B0"
    ))

# Strand → Concept
for c in concepts:
    edges.append(Edge(
        source=f"strand::{c['strand']}",
        target=f"concept::{c['concept_name']}",
        color="#90CAF9"
    ))

# Concept ↔ Concept (interconnections)
for c in concepts:
    for linked in c.get("interconnections", []):
        if linked in concept_names:
            edges.append(Edge(
                source=f"concept::{c['concept_name']}",
                target=f"concept::{linked}",
                color="#FF6F61"
            ))

# -----------------------------------
# RENDER GRAPH
# -----------------------------------
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

# -----------------------------------
# SIDEBAR — DETAILS
# -----------------------------------
st.sidebar.divider()
st.sidebar.subheader("🔍 Concept Details")

if st.session_state.selected_concept:
    c = concept_map[st.session_state.selected_concept]

    st.sidebar.markdown(f"### {c['concept_name']}")
    st.sidebar.write(c["brief_explanation"])

    st.sidebar.markdown("**Chapters**")
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
        with st.sidebar.expander(f"🧪 Activities ({len(linked_acts)})"):
            for a in linked_acts:
                st.markdown(f"**{a['activity_name']}**")
                st.write(f"Type: {a['activity_type']}")
                st.write(a["learning_goal"])
                st.markdown("---")

    learned = c["concept_name"] in learned_set
    checked = st.sidebar.checkbox("✔ Mark as learned", value=learned)

    if checked:
        learned_set.add(c["concept_name"])
    else:
        learned_set.discard(c["concept_name"])

else:
    st.sidebar.info("Click a concept node to view details.")

# -----------------------------------
# LEGEND
# -----------------------------------
with st.sidebar.expander("🎨 Legend"):
    st.markdown("🟠 Selected concept")
    st.markdown("🟢 Green border → Has activities")
    st.markdown("⚪ Grey → Learned")
