import json
import os
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

import google.generativeai as genai

# -----------------------------------
# Gemini Setup
# -----------------------------------
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

gemini_model = genai.GenerativeModel(
    model_name="gemini-2.5-flash-lite"
)

# -----------------------------------
# Temp Debug
# -----------------------------------
st.sidebar.markdown("### 🔍 Gemini Debug")

if "GEMINI_API_KEY" in os.environ:
    st.sidebar.success("API key loaded")
else:
    st.sidebar.error("API key NOT found")


# -----------------------------------
# Gemini helpers (CLEAN & SAFE)
# -----------------------------------

def safe_generate(prompt):
    try:
        response = gemini_model.generate_content(prompt)

        if not response:
            return "⚠️ Gemini returned no response."

        if hasattr(response, "text") and response.text:
            return response.text[:1200]

        return "⚠️ Gemini responded, but no text was generated."

    except Exception as e:
        return f"❌ Gemini error: {e}"



def build_gemini_context(concept, activities, grade):
    context = f"""
You are an expert teacher following the NCERT curriculum.

Grade: {grade}
Concept: {concept['concept_name']}

Explanation:
{concept['brief_explanation']}

Concept Type: {concept['concept_type']}
Cognitive Level: {concept['cognitive_level']}

Chapters:
{", ".join(concept['chapter_references'])}
"""

    if activities:
        context += "\nLearning Activities:\n"
        for a in activities:
            context += f"- {a['activity_name']}: {a['learning_goal']}\n"

    return context.strip()


def gemini_explain(context):
    prompt = f"""
{context}

Task:
Explain this concept to a student in simple language.
Use one real-life example.
Keep it under 150 words.
"""
    return safe_generate(prompt)


def gemini_connect(context):
    prompt = f"""
{context}

Task:
Explain how this concept connects to:
- other subjects (maths, language, social science)
- real-life situations

Keep the explanation short and clear.
"""
    return safe_generate(prompt)


def gemini_quiz(context):
    prompt = f"""
{context}

Task:
Create 3 questions to check understanding:
1. Easy (recall)
2. Medium (understanding)
3. Challenging (application)

Do not provide answers.
"""
    return safe_generate(prompt)

# ==================================================
# Page config
# ==================================================
st.set_page_config(
    page_title="NCERT Knowledge Graph (Grades 7–8)",
    layout="wide"
)

# ==================================================
# Constants
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
# Persistence helpers
# ==================================================
def load_learned_concepts():
    if os.path.exists(LEARNED_FILE):
        with open(LEARNED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_learned_concepts(data):
    with open(LEARNED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def compute_domain_progress(concepts, learned_store, grade):
    domain_totals = {}
    domain_learned = {}

    for c in concepts:
        domain_totals[c["domain"]] = domain_totals.get(c["domain"], 0) + 1

    for domain, learned_list in learned_store.get(grade, {}).items():
        domain_learned[domain] = len(set(learned_list))

    progress = {}
    for domain, total in domain_totals.items():
        learned = domain_learned.get(domain, 0)
        progress[domain] = round((learned / total) * 100, 1)

    return progress

# ==================================================
# Load curriculum data
# ==================================================
@st.cache_data
def load_all_data():
    with open("data/grade7_knowledge_base.json", "r", encoding="utf-8") as f:
        g7 = json.load(f)
    with open("data/grade8_knowledge_base.json", "r", encoding="utf-8") as f:
        g8 = json.load(f)
    return {"7": g7, "8": g8}

ALL_DATA = load_all_data()

# ==================================================
# Sidebar — Grade selection
# ==================================================
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

# ==================================================
# Learned state init
# ==================================================
learned_store = load_learned_concepts()
learned_store.setdefault(grade, {})

# ==================================================
# Session state (click stability)
# ==================================================
if "selected_concept" not in st.session_state:
    st.session_state.selected_concept = None
elif st.session_state.selected_concept not in concept_names:
    st.session_state.selected_concept = None

# ==================================================
# Build hierarchy
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
# Nodes
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
    domain = c["domain"]
    has_activity = name in concepts_with_activities

    nodes.append(Node(
        id=f"concept::{name}",
        label=name,
        shape="dot",
        size=18,
        color=DOMAIN_COLORS.get(domain),
        borderColor="#111827" if has_activity else DOMAIN_COLORS.get(domain),
        borderWidth=3 if has_activity else 1,
        font={"size": 12}
    ))

# ==================================================
# Edges
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
    for c in clist:
        edges.append(Edge(
            source=f"strand::{strand}",
            target=f"concept::{c}",
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
# Graph config
# ==================================================
config = Config(
    width="100%",
    height=800,
    directed=False,
    physics=True,
    nodeHighlightBehavior=True,
    highlightColor="#F7A7A6",

    # 🔥 SPACING CONTROL
    physics_config={
        "forceAtlas2Based": {
            "gravitationalConstant": -150,
            "centralGravity": 0.01,
            "springLength": 180,
            "springConstant": 0.05,
            "avoidOverlap": 2.0
        },
        "maxVelocity": 30,
        "minVelocity": 0.1,
        "solver": "forceAtlas2Based",
        "stabilization": {
            "enabled": True,
            "iterations": 150
        }
    }
)


# ==================================================
# Render graph
# ==================================================
st.title(f"📘 NCERT Knowledge Graph — Grade {grade}")

selected = agraph(nodes=nodes, edges=edges, config=config)

# Normalize click
clicked = None
if isinstance(selected, dict) and selected.get("nodes"):
    clicked = selected["nodes"][0]
elif isinstance(selected, list) and selected:
    clicked = selected[0]
elif isinstance(selected, str):
    clicked = selected

if isinstance(clicked, str) and clicked.startswith("concept::"):
    st.session_state.selected_concept = clicked.replace("concept::", "")

# ==================================================
# Sidebar — Concept details
# ==================================================
st.sidebar.markdown("## 🔍 Concept Details")

selected_concept = st.session_state.selected_concept

if selected_concept:
    concept = concept_map[selected_concept]
    domain = concept["domain"]

    st.sidebar.markdown(f"### {selected_concept}")

    with st.sidebar.expander("📘 Concept Details", expanded=False):
        st.write("**Brief Explanation**")
        st.write(concept.get("brief_explanation", "—"))

        st.write("**Chapter References**")
        for ch in concept.get("chapter_references", []):
            st.write(f"• {ch}")

        st.write("**Concept Type**")
        st.write(concept.get("concept_type", "—"))

        st.write("**Cognitive Level**")
        st.write(concept.get("cognitive_level", "—"))

    linked_activities = [
        a for a in activities if a.get("parent_concept") == selected_concept
    ]

    with st.sidebar.expander(f"🧪 Activity Details ({len(linked_activities)})"):
        if linked_activities:
            for a in linked_activities:
                st.markdown(f"**{a.get('activity_name')}**")
                st.write(f"• Activity Type: {a.get('activity_type')}")
                st.write(f"• Learning Goal: {a.get('learning_goal')}")
                st.markdown("---")
        else:
            st.write("No activities linked.")

    learned_store[grade].setdefault(domain, [])
    already_learned = selected_concept in learned_store[grade][domain]

    mark_learned = st.sidebar.checkbox(
        "✅ Mark concept as learned",
        value=already_learned,
        key=f"learned_{grade}_{selected_concept}"
    )

    if mark_learned and not already_learned:
        learned_store[grade][domain].append(selected_concept)
        save_learned_concepts(learned_store)

    if not mark_learned and already_learned:
        learned_store[grade][domain].remove(selected_concept)
        save_learned_concepts(learned_store)

st.sidebar.markdown("### 🧪 Gemini Hard Test")

if st.sidebar.button("Test Gemini Now"):
    try:
        resp = gemini_model.generate_content(
            "Say hello and confirm you are working."
        )

        st.sidebar.success("Gemini call executed")

        if hasattr(resp, "text"):
            st.sidebar.write(resp.text)
        else:
            st.sidebar.write(str(resp))

    except Exception as e:
        st.sidebar.error(f"Gemini failed: {e}")


# ======================
# Sidebar — GEMINI UI 
# ======================
st.sidebar.divider()
st.sidebar.subheader("🤖 AI Learning Assistant")

if st.session_state.selected_concept:
    mode = st.sidebar.radio(
        "What would you like to do?",
        ["Explain", "Connect concepts", "Quiz me"]
    )

    if st.sidebar.button("Ask Gemini"):
        with st.sidebar.spinner("Thinking..."):
            concept = concept_map[st.session_state.selected_concept]

            linked_acts = [
                a for a in activities
                if a.get("parent_concept") == concept["concept_name"]
            ]

            context = build_gemini_context(
                concept,
                linked_acts,
                grade
            )

            if mode == "Explain":
                response = gemini_explain(context)
            elif mode == "Connect concepts":
                response = gemini_connect(context)
            else:
                response = gemini_quiz(context)

        st.sidebar.markdown("### Gemini says")
        st.sidebar.write(response)
else:
    st.sidebar.info("Select a concept to use AI assistance.")

# ==================================================
# Sidebar — Learning progress (DROPDOWN)
# ==================================================
with st.sidebar.expander("📊 Learning Progress", expanded=False):
    progress = compute_domain_progress(concepts, learned_store, grade)
    for domain, percent in progress.items():
        st.markdown(f"**{domain}**")
        st.progress(percent / 100)
        st.caption(f"{percent}% completed")







