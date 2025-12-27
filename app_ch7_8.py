import json
import os
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
#persistence helper block
# ----------------------------
LEARNED_FILE = "learned_concepts.json"

def load_learned_concepts():
    if os.path.exists(LEARNED_FILE):
        with open(LEARNED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_learned_concepts(data):
    with open(LEARNED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

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

# ----------------------------
# Sidebar — Grade selection
# ----------------------------
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

st.sidebar.markdown("## 📊 Learning Progress")

progress = compute_domain_progress(concepts, learned_store, selected_grade)

for domain, percent in progress.items():
    st.sidebar.markdown(f"**{domain}**")
    st.sidebar.progress(percent / 100)
    st.sidebar.caption(f"{percent}% completed")

# -----------------------------
# learn store
# -----------------------------
learned_store = load_learned_concepts()

if selected_grade not in learned_store:
    learned_store[selected_grade] = {}


# -----------------------------
# Concepts that have activities
# -----------------------------
concepts_with_activities = {
    a["parent_concept"]
    for a in activities
    if a.get("parent_concept")
}

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
# Domain colors
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

# Domain nodes
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

# Strand nodes
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

# Concept nodes
for c in concepts:
    concept_name = c["concept_name"]
    domain = c["domain"]
    domain_color = DOMAIN_COLORS.get(domain, "#999999")

    has_activity = concept_name in concepts_with_activities

    nodes.append(
        Node(
            id=f"concept::{concept_name}",
            label=concept_name,
            shape="dot",
            size=18,
            color=domain_color,                       # ✅ correct
            borderColor="#111827" if has_activity else domain_color,
            borderWidth=3 if has_activity else 1,
            font={"size": 12}
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
# Main graph
# ----------------------------
st.markdown(f"## 📘 NCERT Grade {grade} – Knowledge Graph")

selected = agraph(nodes=nodes, edges=edges, config=config)

# ----------------------------
# Normalize click result (DO NOT TOUCH)
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

    # -------- Concept details dropdown (CLOSED by default) --------
    with st.sidebar.expander("📘 Concept Details", expanded=False):
        st.markdown("**Brief Explanation**")
        st.write(concept.get("brief_explanation", "—"))

        st.markdown("**Chapter References**")
        for ch in concept.get("chapter_references", []):
            st.write(f"• {ch}")

        st.markdown("**Concept Type**")
        st.write(concept.get("concept_type", "—"))

        st.markdown("**Cognitive Level**")
        st.write(concept.get("cognitive_level", "—"))

    # -------- Activity details dropdown --------
    linked_activities = [
        a for a in activities
        if a.get("parent_concept") == selected_concept
    ]

    with st.sidebar.expander(f"🧪 Activity Details ({len(linked_activities)})"):
        if linked_activities:
            for a in linked_activities:
                st.markdown(f"**{a.get('activity_name', '—')}**")
                st.write(f"• Activity Type: {a.get('activity_type', '—')}")
                st.write(f"• Learning Goal: {a.get('learning_goal', '—')}")
                st.markdown("---")
        else:
            st.write("No activities linked to this concept.")

    # -------- Mark as learned checkbox (safe)
    if selected_concept:
    concept_domain = selected_concept_data["domain"]

    if concept_domain not in learned_store[selected_grade]:
        learned_store[selected_grade][concept_domain] = []

    already_learned = selected_concept in learned_store[selected_grade][concept_domain]

    mark_learned = st.checkbox(
        "Mark concept as learned",
        value=already_learned,
        key=f"learned_{selected_grade}_{selected_concept}"
    )

    if mark_learned and not already_learned:
        learned_store[selected_grade][concept_domain].append(selected_concept)
        save_learned_concepts(learned_store)

    if not mark_learned and already_learned:
        learned_store[selected_grade][concept_domain].remove(selected_concept)
        save_learned_concepts(learned_store)


    
    # -------- Mark as learned (MOVED BELOW activities) --------
    learned = selected_concept in st.session_state.learned_concepts[grade]

    checked = st.sidebar.checkbox(
        "✅ Mark concept as learned",
        value=learned
    )

    if checked:
        st.session_state.learned_concepts[grade].add(selected_concept)
    else:
        st.session_state.learned_concepts[grade].discard(selected_concept)

else:
    st.sidebar.info("Click a concept node to view details.")

def compute_domain_progress(concepts, learned_store, grade):
    domain_totals = {}
    domain_learned = {}

    for c in concepts:
        domain = c["domain"]
        domain_totals[domain] = domain_totals.get(domain, 0) + 1

    for domain, learned_list in learned_store.get(grade, {}).items():
        domain_learned[domain] = len(set(learned_list))

    progress = {}
    for domain in domain_totals:
        learned = domain_learned.get(domain, 0)
        total = domain_totals[domain]
        progress[domain] = round((learned / total) * 100, 1)

    return progress








