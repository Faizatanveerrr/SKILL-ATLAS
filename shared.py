import streamlit as st
from pipeline.graph import build_graph
from pipeline.storage import init_db, save_resource_for_user, is_saved
import html

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
                .resource-card {
            background-color: #1a1d24; border: 1px solid #2d313a;
            border-radius: 12px; padding: 1.2rem 1.5rem; margin-bottom: 1.2rem;
        }
        .resource-card img { border-radius: 8px; }
                div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #1a1d24;
            border-radius: 12px;
            margin-bottom: 1rem;
        }
                div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #1a1d24;
            border-radius: 12px;
            margin-bottom: 1rem;
        }
        .grid-card {
            background-color: #1a1d24; border: 1px solid #2d313a;
            border-radius: 14px; padding: 1.1rem; margin-bottom: 1rem; height: 100%;
        }
        .icon-box {
            width: 48px; height: 48px; border-radius: 10px; background-color: #2d313a;
            display: flex; align-items: center; justify-content: center;
            font-size: 1.4rem; margin-bottom: 0.7rem;
        }
        .type-pill {
            display: inline-block; padding: 2px 10px; border-radius: 20px;
            font-size: 0.72rem; font-weight: 600; margin-bottom: 0.5rem;
        }
        .type-Course { background-color: #1e3a2f; color: #4ade80; }
        .type-Documentation { background-color: #1e2a4a; color: #60a5fa; }
        .type-Video { background-color: #4a1e3a; color: #f472b6; }
        .type-Article { background-color: #2a1e4a; color: #a78bfa; }
        .type-Repository { background-color: #4a3a1e; color: #fbbf24; }
        .grid-title { font-size: 1.05rem; font-weight: 700; color: #ffffff; margin-bottom: 0.4rem; line-height: 1.3; }
        .grid-desc { color: #9ca3af; font-size: 0.85rem; line-height: 1.4; margin-bottom: 0.6rem; }
    </style>
    """, unsafe_allow_html=True)
TYPE_ICONS = {"Course": "🎓", "Documentation": "📄", "Video": "🎬", "Article": "📰", "Repository": "💻"}

def render_grid_card(r, saved_label=None, context="default"):
    icon = TYPE_ICONS.get(r.resource_type, "📚")
    type_class = f"type-{r.resource_type}" if r.resource_type in TYPE_ICONS else "type-Course"

    st.markdown(f"""
    <div class="grid-card">
        <div class="icon-box">{icon}</div>
        <span class="type-pill {type_class}">{html.escape(r.resource_type)}</span>
        <div class="grid-title">{html.escape(r.title)}</div>
        <div class="grid-desc">{html.escape(r.ai_summary[:120])}{'...' if len(r.ai_summary) > 120 else ''}</div>
        <span class="badge badge-score">⭐ {r.score}/10</span>
        <span class="badge {"badge-free" if r.price_type == "Free" else "badge-paid"}">💰 {r.price_type}</span>
    </div>
    """, unsafe_allow_html=True)

    if saved_label:
        st.caption(saved_label)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("ℹ️ About", key=f"grid_about_{context}_{r.url}", use_container_width=True):
            st.session_state["selected_resource_url"] = r.url
            st.rerun()
    with col2:
        st.link_button("🔗 Visit", r.url, use_container_width=True, key=f"grid_visit_{context}_{r.url}")
       
def render_result_compact(r):
    with st.container(border=True):
        col_img, col_content = st.columns([1, 4], gap="medium")

        with col_img:
            if r.thumbnail_url:
                st.image(r.thumbnail_url, use_container_width=True)
            else:
                icon = {"Video": "🎬", "Course": "🎓", "Documentation": "📄", "Article": "📰", "Repository": "💻"}.get(r.resource_type, "📚")
                st.markdown(f'<div style="font-size:2.5rem; text-align:center; padding-top:0.6rem;">{icon}</div>', unsafe_allow_html=True)

        with col_content:
            price_class = "badge-free" if r.price_type == "Free" else "badge-paid"
            st.markdown(f"""
                <div class="resource-title">{html.escape(r.title)}</div>
                <span class="badge badge-score">⭐ {r.score}/10</span>
                <span class="badge {price_class}">💰 {r.price_type}</span>
                <span class="badge badge-level">🎯 {r.difficulty_level}</span>
            """, unsafe_allow_html=True)

        st.write("")
        bcol1, bcol2 = st.columns(2, gap="small")
        with bcol1:
            if st.button("ℹ️ About", key=f"about_{r.url}", use_container_width=True):
                st.session_state["selected_resource_url"] = r.url
                st.rerun()
        with bcol2:
            st.link_button("🔗 Visit Site", r.url, use_container_width=True)


def render_result_detail(r, topic=None):
    import html
    from pipeline.analyse import generate_quiz

    if st.button("← Back to results"):
        st.session_state["selected_resource_url"] = None
        st.rerun()

    prereq_html = f'<div class="meta-text">📋 Prerequisites: {html.escape(", ".join(r.prerequisites))}</div>' if r.prerequisites else ""
    skills_html = f'<div class="meta-text">🧠 Skills Taught: {html.escape(", ".join(r.skills_taught))}</div>' if r.skills_taught else ""
    price_class = "badge-free" if r.price_type == "Free" else "badge-paid"

    st.markdown(f"""
    <div class="resource-card">
        <div class="resource-title">{html.escape(r.title)}</div>
        <span class="badge badge-score">⭐ {r.score}/10 Quality</span>
        <span class="badge badge-relevance">🎯 {r.relevance_score}/10 Relevance</span>
        <span class="badge {price_class}">💰 {r.price_type}</span>
        <span class="badge badge-level">🎯 {r.difficulty_level}</span>
        <div class="summary-text">{html.escape(r.ai_summary)}</div>
        <div class="meta-text">📂 Type: {r.resource_type}</div>
        {prereq_html}
        {skills_html}
        <div class="meta-text">💭 {html.escape(r.reasoning)}</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.link_button("🔗 Visit Site", r.url, use_container_width=True)
    with col2:
        username = st.session_state.get("username")
        already_saved = is_saved(username, r.url)
        if already_saved:
            st.caption("✅ Saved to Library")
        else:
            if st.button("💾 Save", key=f"save_detail_{r.url}", use_container_width=True):
                save_resource_for_user(username, r.url, topic or st.session_state.get("last_topic", ""))
                st.rerun()

    st.write("")
    if st.button("📝 Generate Quiz", key=f"quiz_btn_{r.url}"):
        with st.spinner("Generating quiz..."):
            quiz = generate_quiz(r.title, r.ai_summary, r.topics_covered)
            st.session_state[f"quiz_{r.url}"] = quiz

    quiz_data = st.session_state.get(f"quiz_{r.url}")
    if quiz_data:
        st.subheader("Quiz")
        for i, q in enumerate(quiz_data["questions"]):
            st.write(f"**Q{i+1}. {q['question']}**")
            answer = st.radio(
                "Choose an answer:",
                q["options"],
                key=f"quiz_{r.url}_q{i}",
                label_visibility="collapsed"
            )
            if st.button(f"Check Answer {i+1}", key=f"check_{r.url}_q{i}"):
                correct = q["options"][q["correct_answer_index"]]
                if answer == correct:
                    st.success("Correct! ✅")
                else:
                    st.error(f"Not quite. The correct answer is: {correct}")
    from pipeline.analyse import generate_project_ideas

    st.write("")
    if st.button("🛠️ Suggest Projects", key=f"projects_btn_{r.url}"):
        with st.spinner("Generating project ideas..."):
            projects = generate_project_ideas(r.title, r.ai_summary, r.skills_taught, r.difficulty_level)
            st.session_state[f"projects_{r.url}"] = projects

    project_data = st.session_state.get(f"projects_{r.url}")
    if project_data:
        st.subheader("Project Ideas")
        for p in project_data["projects"]:
            st.markdown(f"""
            <div class="resource-card">
                <div class="resource-title">{p['title']}</div>
                <div class="summary-text">{p['description']}</div>
                <span class="badge badge-level">⏱️ ~{p['estimated_hours']}h</span>
            </div>
            """, unsafe_allow_html=True)
    from pipeline.analyse import analyze_skill_gap

    st.write("")
    with st.expander("🎯 Check Skill Gap"):
        user_skills = st.text_input("What skills do you already have?", key=f"skills_input_{r.url}")
        if st.button("Analyze Fit", key=f"gap_btn_{r.url}") and user_skills.strip():
            with st.spinner("Analyzing..."):
                gap = analyze_skill_gap(user_skills, r.title, r.skills_taught, r.difficulty_level)
                st.session_state[f"gap_{r.url}"] = gap

        gap_data = st.session_state.get(f"gap_{r.url}")
        if gap_data:
            st.write(f"**Fit Score:** {gap_data['fit_score']}/10")
            st.write(f"**Already Known:** {', '.join(gap_data['already_known']) if gap_data['already_known'] else 'None'}")
            st.write(f"**New Skills:** {', '.join(gap_data['new_skills'])}")
            st.write(gap_data['gap_summary'])
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
