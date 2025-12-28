import json
import os
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config
import google.generativeai as genai

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(
    page_title="NCERT Knowledge Graph (Grades 7–8)",
    layout="wide"
)

# ==================================================
# GEMINI SETUP (CORRECT)
# ==================================================
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

MODEL_NAME = "gemini-2.0-flash-lite"
model = genai.GenerativeModel(MODEL_NAME)

def safe_generate(prompt: str) -> str:
    try:
        resp = model.generate_content(prompt)
        if hasattr(resp, "text") and resp.text:
            return resp.text.strip()
        return "⚠️ Gemini returned an empty response."
    except Exception as e:
        return f"❌ Gemini error: {e}"

# ==================================================
# DATA LOAD
# ==================================================
@st.cache_data
def load_data():
    with open("data/grade7_knowledge_base.json", encoding="utf-8") as f:
        g7 = json.load(f)
    with open("data/grade8_knowledge_base.json", encoding="utf-8") as f:
        g8 = json.load(f)
    return {"7": g7, "8": g8}

DATA = load_data()

# ==================================================
# CONSTANTS
# ==================================================
DOMAIN_COLORS = {
    "Physics (The Physical World)": "#1f77b4",
    "Chemistry (The World of Matter)": "#2ca02c",
    "Biology (The Living World)": "#ff7f0e",
    "Earth & Space Science": "#9467bd",
    "Scientific Inquiry & Investigative Process": "#7f7f7f"
}

LEARNED_FILE = "learned_concepts.json"

# ==================================================
# LEARNED STATE
# ==================================================
def load_learned():
    if os.path.exists(LEARNED_FILE):
        with open(LEARNED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_learned(data):
    with open(LEARNED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

learned_store = load_learned()

# ==================================================
# SIDEBAR — GRADE
# ==================================================
st.sidebar.title("📘 Curriculum")
grade = st.sidebar.radio("Select Grade", ["7", "8"], horizontal=True)

concepts = DATA[grade]["concepts"]
activities = DATA[grade]["activities"]

concept_map = {c["concept_name"]: c for c in concepts}
concept_names = set(concept_map.keys())

learned_store.setdefault(grade, {})

# ==================================================
# SESSION STATE
# ==================================================
if "selected_concept" not in st.session_state:
    st.session_state.selected_concept = None

# ==================================================
# BUILD HIERARCHY
# ==================================================
domains = {}
strands = {}

for c in concepts:
    domains.setdefault(c["domain"], set()).add(c["strand"])
    strands.setdefault((c["domain"], c["strand"]), []).append(c["concept_name"])

concepts_with_activities = {
    a["parent_concept"] for a in activities if a.get("parent_concept")
}

# ==================================================
# BUILD NODES
# ==================================================
nodes = []

for domain in domains:
    nodes.append(Node(
        id=f"domain::{domain}",
        label=domain,
        shape="box",
        size=45,
        color=DOMAIN_COLORS.get(domain),
        font={"size": 18, "bold": True, "color": "white"}
    ))

for (domain, strand) in strands:
    nodes.append(Node(
        id=f"strand::{strand}",
        label=strand,
        shape="ellipse",
        size=28,
        color=DOMAIN_COLORS.get(domain),
        font={"size": 14}
    ))

for c in concepts:
    name = c["concept_name"]
    has_activity = name in concepts_with_activities
    nodes.append(Node(
        id=f"concept::{name}",
        label=name,
        size=18,
        shape="dot",
        color=DOMAIN_COLORS.get(c["domain"]),
        borderWidth=4 if has_activity else 1,
        borderColor="#000000" if has_activity else "#cccccc"
    ))

# ==================================================
# BUILD EDGES
# ==================================================
edges = []

for domain, strand_set in domains.items():
    for strand in strand_set:
        edges.append(Edge(
            source=f"domain::{domain}",
            target=f"strand::{strand}",
            color="#cccccc"
        ))

for (domain, strand), clist in strands.items():
    for cname in clist:
        edges.append(Edge(
            source=f"strand::{strand}",
            target=f"concept::{cname}",
            color="#dddddd"
        ))

for c in concepts:
    for linked in c.get("interconnections", []):
        if linked in concept_names:
            edges.append(Edge(
                source=f"concept::{c['concept_name']}",
                target=f"concept::{linked}",
                color="#ff9999"
            ))

# ==================================================
# GRAPH CONFIG
# ==================================================
config = Config(
    width="100%",
    height=800,
    directed=False,
    physics=True,
    nodeHighlightBehavior=True,
    highlightColor="#FFD700",
    physics_config={
        "forceAtlas2Based": {
            "gravitationalConstant": -150,
            "springLength": 180,
            "avoidOverlap": 2.0
        },
        "stabilization": {"enabled": True, "iterations": 120}
    }
)

# ==================================================
# RENDER GRAPH
# ==================================================
st.title(f"📘 NCERT Knowledge Graph — Grade {grade}")
selected = agraph(nodes=nodes, edges=edges, config=config)

clicked = None
if isinstance(selected, dict) and selected.get("nodes"):
    clicked = selected["nodes"][0]

if isinstance(clicked, str) and clicked.startswith("concept::"):
    st.session_state.selected_concept = clicked.replace("concept::", "")

# ==================================================
# SIDEBAR — CONCEPT DETAILS
# ==================================================
st.sidebar.header("🔍 Concept Details")

if st.session_state.selected_concept:
    concept = concept_map[st.session_state.selected_concept]

    st.sidebar.subheader(concept["concept_name"])
    st.sidebar.write(concept["brief_explanation"])
    st.sidebar.caption(f"Type: {concept['concept_type']} | Level: {concept['cognitive_level']}")

    st.sidebar.markdown("**Chapters**")
    for ch in concept["chapter_references"]:
        st.sidebar.write(f"• {ch}")

    linked_acts = [a for a in activities if a["parent_concept"] == concept["concept_name"]]

    with st.sidebar.expander(f"🧪 Activities ({len(linked_acts)})"):
        if linked_acts:
            for a in linked_acts:
                st.markdown(f"**{a['activity_name']}**")
                st.write(a["learning_goal"])
        else:
            st.write("No activities linked.")

    learned_store[grade].setdefault(concept["domain"], [])
    is_learned = concept["concept_name"] in learned_store[grade][concept["domain"]]

    if st.sidebar.checkbox("✅ Mark concept as learned", value=is_learned):
        if not is_learned:
            learned_store[grade][concept["domain"]].append(concept["concept_name"])
            save_learned(learned_store)
    else:
        if is_learned:
            learned_store[grade][concept["domain"]].remove(concept["concept_name"])
            save_learned(learned_store)

# ==================================================
# GEMINI AI ASSISTANT (WORKING)
# ==================================================
st.sidebar.divider()
st.sidebar.subheader("🤖 AI Learning Assistant")

if st.session_state.selected_concept:
    mode = st.sidebar.radio("Choose action", ["Explain", "Connect concepts", "Quiz me"])

    if st.sidebar.button("Ask Gemini"):
        with st.sidebar.spinner("Thinking..."):
            ctx = f"""
Grade {grade}
Concept: {concept['concept_name']}
Explanation: {concept['brief_explanation']}
Activities: {[a['activity_name'] for a in linked_acts]}
"""
            if mode == "Explain":
                prompt = ctx + "\nExplain this concept simply with a real-life example."
            elif mode == "Connect concepts":
                prompt = ctx + "\nExplain connections to other subjects and real life."
            else:
                prompt = ctx + "\nCreate 3 quiz questions (easy, medium, hard)."

            answer = safe_generate(prompt)

        st.sidebar.markdown("### Gemini says")
        st.sidebar.write(answer)
else:
    st.sidebar.info("Select a concept to use AI assistance.")
