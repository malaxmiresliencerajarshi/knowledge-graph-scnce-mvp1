import json
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

st.set_page_config(
    page_title="NCERT Grade 7 Knowledge Graph",
    layout="wide"
)

st.title("📘 NCERT Grade 7 – Knowledge Graph")

# ---------- Load data ----------
@st.cache_data
def load_data():
    with open("data/grade7_knowledge_base.json", "r", encoding="utf-8") as f:
        return json.load(f)

data = load_data()

concepts = data["concepts"]
activities = data["activities"]

# ---------- Sidebar ----------
st.sidebar.header("🔍 Concept Details")
selected_concept = st.session_state.get("selected_concept")

if selected_concept:
    concept = next(
        (c for c in concepts if c["concept_name"] == selected_concept),
        None
    )

    if concept:
        st.sidebar.subheader(selected_concept)
        st.sidebar.write(concept.get("brief_explanation", ""))

        st.sidebar.markdown("**Domain**")
        st.sidebar.write(concept["domain"])

        st.sidebar.markdown("**Strand**")
        st.sidebar.write(concept["strand"])

        st.sidebar.markdown("**Chapters**")
        for ch in concept.get("chapter_references", []):
            st.sidebar.write(f"- {ch}")

        st.sidebar.markdown("**Cognitive Level**")
        st.sidebar.write(concept.get("cognitive_level", ""))

        st.sidebar.markdown("**Activities**")
        related_activities = [
            a for a in activities if a["parent_concept"] == selected_concept
        ]

        if related_activities:
            for a in related_activities:
                st.sidebar.write(f"• {a['activity_name']}")
        else:
            st.sidebar.write("No activities linked.")

else:
    st.sidebar.info("Click a concept node to view details.")

# ---------- Build graph ----------
nodes = []
edges = []

for c in concepts:
    nodes.append(
        Node(
            id=c["concept_name"],
            label=c["concept_name"],
            size=18,
            color="#1f77b4"
        )
    )

    for linked in c.get("interconnections", []):
        edges.append(
            Edge(
                source=c["concept_name"],
                target=linked
            )
        )

config = Config(
    width=1200,
    height=650,
    directed=False,
    physics=True,
    hierarchical=False,
    nodeHighlightBehavior=True,
    highlightColor="#F7A7A6"
)

# ---------- Render graph ----------
selected = agraph(
    nodes=nodes,
    edges=edges,
    config=config
)

if selected:
    st.session_state["selected_concept"] = selected
