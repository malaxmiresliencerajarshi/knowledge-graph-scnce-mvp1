import json
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(layout="wide")

# -------------------------------------------------
# Load data
# -------------------------------------------------
with open("grade7_knowledge_base.json", "r", encoding="utf-8") as f:
    g7 = json.load(f)

with open("grade8_knowledge_base.json", "r", encoding="utf-8") as f:
    g8 = json.load(f)

DATA = {"7": g7, "8": g8}

# -------------------------------------------------
# Domain colours (LOCKED)
# -------------------------------------------------
DOMAIN_COLORS = {
    "Physics (The Physical World)": "#2563EB",
    "Chemistry (The World of Matter)": "#16A34A",
    "Biology (The Living World)": "#EA580C",
    "Earth & Space Science": "#7C3AED",
    "Scientific Inquiry & Investigative Process": "#6B7280",
}

# -------------------------------------------------
# Sidebar: grade selector
# -------------------------------------------------
st.sidebar.header("Select Grade")
grade = st.sidebar.radio("Grade", ["7", "8"], horizontal=True)

concepts = DATA[grade]["concepts"]
activities = DATA[grade]["activities"]

# -------------------------------------------------
# Session state
# -------------------------------------------------
if "selected_concept" not in st.session_state:
    st.session_state.selected_concept = None

if "learned" not in st.session_state:
    st.session_state.learned = set()

# -------------------------------------------------
# Index activities by concept
# -------------------------------------------------
activity_map = {}
for a in activities:
    pc = a.get("parent_concept")
    if pc:
        activity_map.setdefault(pc, []).append(a)

# -------------------------------------------------
# Build node containers
# -------------------------------------------------
nodes = []
edges = []

domains = sorted(set(c["domain"] for c in concepts))
strands = sorted(set(c["strand"] for c in concepts))

# -------------------------------------------------
# Domain nodes (visual anchors only)
# -------------------------------------------------
for d in domains:
    nodes.append(Node(
        id=f"domain::{d}",
        label=d.replace(" (", "\n("),
        shape="box",
        size=60,
        color=DOMAIN_COLORS.get(d, "#64748B"),
        font={"size": 18, "color": "white"},
        selectable=False,
        physics=False
    ))

# -------------------------------------------------
# Strand nodes (visual only, inherit domain colour)
# -------------------------------------------------
for s in strands:
    domain = next(c["domain"] for c in concepts if c["strand"] == s)
    nodes.append(Node(
        id=f"strand::{s}",
        label=s,
        shape="ellipse",
        size=32,
        color=DOMAIN_COLORS.get(domain, "#64748B"),
        font={"size": 14, "color": "white"},
        selectable=False,
        physics=False
    ))
    edges.append(Edge(
        source=f"domain::{domain}",
        target=f"strand::{s}",
        color="#CBD5E1"
    ))

# -------------------------------------------------
# Concept nodes (ONLY clickable nodes)
# -------------------------------------------------
for c in concepts:
    cname = c["concept_name"]
    domain = c["domain"]
    strand = c["strand"]

    has_activity = cname in activity_map

    nodes.append(Node(
        id=f"concept::{cname}",
        label=cname,
        shape="dot",
        size=22,
        color=DOMAIN_COLORS.get(domain, "#64748B"),
        borderWidth=3 if has_activity else 1,
        borderColor="#111827",
        selectable=True
    ))

    edges.append(Edge(
        source=f"strand::{strand}",
        target=f"concept::{cname}",
        color="#E5E7EB"
    ))

    for linked in c.get("interconnections", []):
        edges.append(Edge(
            source=f"concept::{cname}",
            target=f"concept::{linked}",
            color="#FCA5A5",
            dashes=True
        ))

# -------------------------------------------------
# Graph config (STABLE)
# -------------------------------------------------
config = Config(
    height=700,
    width=1400,
    directed=False,
    physics=True,
    hierarchical=False
)

# -------------------------------------------------
# Render graph
# -------------------------------------------------
st.title("📘 NCERT Knowledge Graph")

result = agraph(nodes=nodes, edges=edges, config=config)

if result and isinstance(result, dict):
    clicked = result.get("nodes", [])
    if clicked:
        node_id = clicked[0].get("id", "")
        if node_id.startswith("concept::"):
            st.session_state.selected_concept = node_id.replace("concept::", "")

# -------------------------------------------------
# Sidebar: Concept details
# -------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("Concept Details")

if st.session_state.selected_concept:
    cname = st.session_state.selected_concept
    c = next(c for c in concepts if c["concept_name"] == cname)

    st.sidebar.subheader(cname)
    st.sidebar.write(c["brief_explanation"])

    st.sidebar.markdown("**Chapter(s):**")
    for ch in c["chapter_references"]:
        st.sidebar.write(f"- {ch}")

    st.sidebar.markdown(f"**Concept type:** {c['concept_type']}")
    st.sidebar.markdown(f"**Cognitive level:** {c['cognitive_level']}")

    st.sidebar.markdown("---")

    if cname in activity_map:
        with st.sidebar.expander("Learning Activities"):
            for a in activity_map[cname]:
                st.markdown(f"**{a['activity_name']}**")
                st.write(f"- Type: {a['activity_type']}")
                st.write(f"- Goal: {a['learning_goal']}")

    learned = st.sidebar.checkbox(
        "Mark concept as learned",
        value=cname in st.session_state.learned
    )

    if learned:
        st.session_state.learned.add(cname)
    else:
        st.session_state.learned.discard(cname)

else:
    st.sidebar.info("Click a concept node to view details.")
