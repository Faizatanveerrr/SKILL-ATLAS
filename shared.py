import streamlit as st
from pipeline.graph import build_graph
from pipeline.storage import init_db, save_resource_for_user, is_saved


@st.cache_resource
def get_graph():
    init_db()
    return build_graph()


def init_session_state():
    if "results" not in st.session_state:
        st.session_state["results"] = None
    if "fallback_results" not in st.session_state:
        st.session_state["fallback_results"] = None
    if "last_topic" not in st.session_state:
        st.session_state["last_topic"] = ""


def apply_custom_css():
    st.markdown("""
    <style>
        .stApp { background-color: #0e1117; }
        .main-title { font-size: 2.2rem; font-weight: 800; color: #ffffff; margin-bottom: 0; }
        .subtitle { color: #9ca3af; font-size: 1rem; margin-bottom: 1.5rem; }
        .resource-card {
            background-color: #1a1d24; border: 1px solid #2d313a;
            border-radius: 12px; padding: 1.3rem 1.5rem; margin-bottom: 1rem;
        }
        .resource-title { font-size: 1.25rem; font-weight: 700; color: #ffffff; margin-bottom: 0.4rem; }
        .badge {
            display: inline-block; padding: 3px 10px; border-radius: 20px;
            font-size: 0.78rem; font-weight: 600; margin-right: 6px;
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


def render_result(r, topic=None, show_save_button=True):
    prereq_html = f'<div class="meta-text">📋 Prerequisites: {", ".join(r.prerequisites)}</div>' if r.prerequisites else ""
    skills_html = f'<div class="meta-text">🧠 Skills Taught: {", ".join(r.skills_taught)}</div>' if r.skills_taught else ""
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

    if show_save_button:
        username = st.session_state.get("username")
        already_saved = is_saved(username, r.url)
        if already_saved:
            st.caption("✅ Saved to Library")
        else:
            if st.button(f"💾 Save", key=f"save_{r.url}"):
                save_resource_for_user(username, r.url, topic or st.session_state.get("last_topic", ""))
                st.rerun()