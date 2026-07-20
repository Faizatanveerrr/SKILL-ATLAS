import streamlit as st
from pipeline.graph import build_graph
from pipeline.rank import rank_resources
@st.cache_resource
def get_graph():
    return build_graph()
st.set_page_config(page_title="Skill Atlas", page_icon="📚", layout="wide")

# ---------- CUSTOM CSS ----------
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 0;
    }
    .subtitle {
        color: #9ca3af;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
    .resource-card {
        background-color: #1a1d24;
        border: 1px solid #2d313a;
        border-radius: 12px;
        padding: 1.3rem 1.5rem;
        margin-bottom: 1rem;
    }
    .resource-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 0.4rem;
    }
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-right: 6px;
    }
    .badge-score { background-color: #1e3a2f; color: #4ade80; }
    .badge-relevance { background-color: #1e2a4a; color: #60a5fa; }
    .badge-free { background-color: #1e3a2f; color: #4ade80; }
    .badge-paid { background-color: #4a2f1e; color: #fbbf24; }
    .badge-level { background-color: #2a1e4a; color: #a78bfa; }
    .summary-text { color: #d1d5db; margin: 0.8rem 0; line-height: 1.5; }
    .meta-text { color: #9ca3af; font-size: 0.85rem; margin-top: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown('<p class="main-title">📚 Skill Atlas</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Discover the best learning resources — not just the popular ones.</p>', unsafe_allow_html=True)

# ---------- SEARCH + FILTERS ----------
topic = st.text_input("What do you want to learn?", placeholder="e.g. LangGraph, Docker, System Design")

col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
with col1:
    resource_type = st.selectbox("Type", [None, "Course", "Documentation", "Video", "Article", "Repository"])
with col2:
    price_type = st.selectbox("Price", [None, "Free", "Paid"])
with col3:
    difficulty_level = st.selectbox("Level", [None, "Beginner", "Intermediate", "Advanced"])
with col4:
    st.write("")
    st.write("")
    search_clicked = st.button("🔍 Search", use_container_width=True)


def render_result(r):
    prereq_html = ""
    if r.prerequisites:
        prereq_html = f'<div class="meta-text">📋 Prerequisites: {", ".join(r.prerequisites)}</div>'

    skills_html = ""
    if r.skills_taught:
        skills_html = f'<div class="meta-text">🧠 Skills Taught: {", ".join(r.skills_taught)}</div>'

    price_class = "badge-free" if r.price_type == "Free" else "badge-paid"

    st.markdown(f"""
    <div class="resource-card">
        <div class="resource-title">{r.title}</div>
        <span class="badge badge-score">⭐ {r.score}/10 Quality</span>
        <span class="badge badge-relevance">🎯 {r.relevance_score}/10 Relevance</span>
        <span class="badge {price_class}">💰 {r.price_type}</span>
        <span class="badge badge-level">🎯 {r.difficulty_level}</span>
        <div class="summary-text">{r.ai_summary}</div>
        <div class="meta-text">🔗 <a href="{r.url}" target="_blank">{r.url}</a></div>
        {prereq_html}
        {skills_html}
    </div>
    """, unsafe_allow_html=True)

if st.button("Search") and topic.strip():
    with st.spinner("Searching the web, analyzing resources..."):
        app = get_graph()
        initial_state = {
            "topic": topic,
            "resource_type": resource_type,
            "price_type": price_type,
            "difficulty_level": difficulty_level,
            "candidates": [],
            "analyzed_results": [],
            "ranked_results": []
        }
        final_state = app.invoke(initial_state)
        st.session_state["results"] = final_state["ranked_results"]
        st.session_state["fallback_results"] = final_state["analyzed_results"]
        st.session_state["last_topic"] = topic

if "results" in st.session_state:
    results = st.session_state["results"]
    if results:
        st.success(f"Found {len(results)} resources for '{st.session_state['last_topic']}'")
        for r in results:
            render_result(r)
    else:
        fallback = rank_resources(st.session_state["fallback_results"])
        if fallback:
            st.warning("No exact match for your filters — here are other resources on this topic:")
            for r in fallback:
                render_result(r)
        else:
            st.error("No resources found at all for this topic. Try a different search term.")

# ---------- SEARCH EXECUTION ----------
if search_clicked and topic.strip():
    with st.spinner("Searching the web, analyzing resources..."):
        app = get_graph()
        initial_state = {
            "topic": topic,
            "resource_type": resource_type,
            "price_type": price_type,
            "difficulty_level": difficulty_level,
            "candidates": [],
            "analyzed_results": [],
            "ranked_results": []
        }
        final_state = app.invoke(initial_state)
        results = final_state["ranked_results"]

    if results:
        st.success(f"Found {len(results)} resources for '{topic}'")
        for r in results:
            render_result(r)
    else:
        fallback = rank_resources(final_state["analyzed_results"])
        if fallback:
            st.warning("No exact match for your filters — here are other resources on this topic:")
            for r in fallback:
                render_result(r)
        else:
            st.error("No resources found at all for this topic. Try a different search term.")