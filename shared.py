import streamlit as st
from pipeline.graph import build_graph
from pipeline.storage import init_db, save_resource_for_user, is_saved
from pipeline.image_generator import get_or_generate_resource_thumbnail
import html

@st.cache_resource
def get_graph():
    init_db()
    return build_graph()


def init_session_state():
    init_db()
    if "results" not in st.session_state:
        st.session_state["results"] = None
    if "fallback_results" not in st.session_state:
        st.session_state["fallback_results"] = None
    if "last_topic" not in st.session_state:
        st.session_state["last_topic"] = ""
    if "theme" not in st.session_state:
        st.session_state["theme"] = "dark"


# ---------------------------------------------------------------------------
# Theme palettes. Every color the CSS below uses is pulled from one of these
# two dicts, keyed the same way, so apply_custom_css() below never has a
# hardcoded color literal in it — everything routes through THEMES[mode].
# ---------------------------------------------------------------------------
THEMES = {
    "dark": {
        "app_bg": "linear-gradient(180deg, #0b0f1a 0%, #0e1117 100%)",
        "text_primary": "#f8fafc",
        "text_secondary": "#9ca3af",
        "title_gradient": "linear-gradient(90deg, #ffffff, #93c5fd)",
        "card_bg": "linear-gradient(145deg, #171b26, #14171f)",
        "card_border": "#262b38",
        "card_border_hover": "#334063",
        "card_shadow": "rgba(0,0,0,0.25)",
        "card_shadow_hover": "rgba(59,130,246,0.15)",
        "summary_text": "#b8c0cf",
        "meta_text": "#7c8798",
        "badge_score_bg": "rgba(52,211,153,0.14)", "badge_score_text": "#4ade80", "badge_score_border": "rgba(74,222,128,0.25)",
        "badge_relevance_bg": "rgba(96,165,250,0.14)", "badge_relevance_text": "#60a5fa", "badge_relevance_border": "rgba(96,165,250,0.25)",
        "badge_free_bg": "rgba(52,211,153,0.14)", "badge_free_text": "#4ade80", "badge_free_border": "rgba(74,222,128,0.25)",
        "badge_paid_bg": "rgba(251,191,36,0.14)", "badge_paid_text": "#fbbf24", "badge_paid_border": "rgba(251,191,36,0.25)",
        "badge_level_bg": "rgba(167,139,250,0.14)", "badge_level_text": "#a78bfa", "badge_level_border": "rgba(167,139,250,0.25)",
        "type_course": "rgba(52,211,153,0.14)", "type_course_text": "#4ade80",
        "type_doc": "rgba(96,165,250,0.14)", "type_doc_text": "#60a5fa",
        "type_video": "rgba(244,114,182,0.14)", "type_video_text": "#f472b6",
        "type_article": "rgba(167,139,250,0.14)", "type_article_text": "#a78bfa",
        "type_repo": "rgba(251,191,36,0.14)", "type_repo_text": "#fbbf24",
        "button_bg": "linear-gradient(180deg, #1a1f2e, #151925)",
        "button_bg_hover": "linear-gradient(180deg, #1e2536, #171c29)",
        "button_border": "#2d3348",
        "button_text": "#e2e8f0",
        "button_text_hover": "#ffffff",
        "input_bg": "#141824",
        "input_border": "#2a3040",
        "input_text": "#f1f5f9",
        "sidebar_bg": "linear-gradient(180deg, #0d1119, #0a0d14)",
        "sidebar_border": "#1c2130",
        "tab_text": "#94a3b8",
        "tab_text_selected": "#60a5fa",
        "alert_border": "rgba(255,255,255,0.08)",
        "divider": "#1c2130",
        "accent": "#3b82f6",
    },
    "light": {
        "app_bg": "linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%)",
        "text_primary": "#0f172a",
        "text_secondary": "#64748b",
        "title_gradient": "linear-gradient(90deg, #0f172a, #2563eb)",
        "card_bg": "linear-gradient(145deg, #ffffff, #f8fafc)",
        "card_border": "#e2e8f0",
        "card_border_hover": "#93c5fd",
        "card_shadow": "rgba(15,23,42,0.06)",
        "card_shadow_hover": "rgba(37,99,235,0.12)",
        "summary_text": "#334155",
        "meta_text": "#64748b",
        "badge_score_bg": "rgba(22,163,74,0.10)", "badge_score_text": "#15803d", "badge_score_border": "rgba(21,128,61,0.25)",
        "badge_relevance_bg": "rgba(37,99,235,0.10)", "badge_relevance_text": "#1d4ed8", "badge_relevance_border": "rgba(29,78,216,0.25)",
        "badge_free_bg": "rgba(22,163,74,0.10)", "badge_free_text": "#15803d", "badge_free_border": "rgba(21,128,61,0.25)",
        "badge_paid_bg": "rgba(217,119,6,0.10)", "badge_paid_text": "#b45309", "badge_paid_border": "rgba(180,83,9,0.25)",
        "badge_level_bg": "rgba(124,58,237,0.10)", "badge_level_text": "#6d28d9", "badge_level_border": "rgba(109,40,217,0.25)",
        "type_course": "rgba(22,163,74,0.10)", "type_course_text": "#15803d",
        "type_doc": "rgba(37,99,235,0.10)", "type_doc_text": "#1d4ed8",
        "type_video": "rgba(219,39,119,0.10)", "type_video_text": "#be185d",
        "type_article": "rgba(124,58,237,0.10)", "type_article_text": "#6d28d9",
        "type_repo": "rgba(217,119,6,0.10)", "type_repo_text": "#b45309",
        "button_bg": "linear-gradient(180deg, #ffffff, #f8fafc)",
        "button_bg_hover": "linear-gradient(180deg, #f8fafc, #f1f5f9)",
        "button_border": "#e2e8f0",
        "button_text": "#0f172a",
        "button_text_hover": "#0f172a",
        "input_bg": "#ffffff",
        "input_border": "#e2e8f0",
        "input_text": "#0f172a",
        "sidebar_bg": "linear-gradient(180deg, #f8fafc, #f1f5f9)",
        "sidebar_border": "#e2e8f0",
        "tab_text": "#64748b",
        "tab_text_selected": "#2563eb",
        "alert_border": "rgba(15,23,42,0.08)",
        "divider": "#e2e8f0",
        "accent": "#2563eb",
    },
}


def render_theme_toggle():
    """Small sidebar control to flip between light and dark mode. Stored in
    session_state, so it persists across page navigation within a session."""
    with st.sidebar:
        current = st.session_state.get("theme", "dark")
        label = "☀️ Light mode" if current == "dark" else "🌙 Dark mode"
        if st.button(label, key="theme_toggle_btn", use_container_width=True):
            st.session_state["theme"] = "light" if current == "dark" else "dark"
            st.rerun()


def render_footer():
    """Fixed-position footer shown on every page. Rendered automatically by
    apply_custom_css() so no view file needs to call this directly."""
    t = THEMES[st.session_state.get("theme", "dark")]
    st.markdown(f"""
    <style>
        .app-footer {{
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            padding: 0.5rem 1.5rem;
            background: {t["sidebar_bg"]};
            border-top: 1px solid {t["divider"]};
            font-size: 0.78rem;
            color: {t["meta_text"]};
            z-index: 999;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .app-footer a {{
            color: {t["meta_text"]};
            text-decoration: none;
            margin-left: 1rem;
        }}
        .app-footer a:hover {{
            color: {t["accent"]};
        }}
        /* keep page content from being hidden behind the fixed footer */
        .block-container {{
            padding-bottom: 3.5rem !important;
        }}
    </style>
    <div class="app-footer">
        <span>📚 Skill Atlas &nbsp;·&nbsp; AI-Powered Learning Discovery &nbsp;·&nbsp; v1.0</span>
        <span>
            <a href="https://github.com/" target="_blank">GitHub</a>
            <a href="mailto:contact@skillatlas.app">Contact</a>
        </span>
    </div>
    """, unsafe_allow_html=True)


def apply_custom_css():
    if "theme" not in st.session_state:
        st.session_state["theme"] = "dark"

    render_theme_toggle()
    t = THEMES[st.session_state["theme"]]

    st.markdown(f"""
    <style>
        /* ---------- BASE ---------- */
        .stApp {{
            background: {t["app_bg"]};
        }}
        html, body, [class*="css"] {{
            font-family: 'Segoe UI', 'Calibri', sans-serif;
        }}

        /* ---------- TYPOGRAPHY ---------- */
        .main-title {{
            font-size: 2.4rem;
            font-weight: 800;
            background: {t["title_gradient"]};
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.1rem;
            letter-spacing: -0.5px;
        }}
        .subtitle {{
            color: {t["text_secondary"]};
            font-size: 1.02rem;
            margin-bottom: 1.7rem;
        }}

        /* ---------- CARDS ---------- */
        .resource-card, .grid-card {{
            background: {t["card_bg"]};
            border: 1px solid {t["card_border"]};
            border-radius: 16px;
            padding: 1.4rem 1.6rem;
            margin-bottom: 1.1rem;
            box-shadow: 0 4px 18px {t["card_shadow"]};
            transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
        }}
        .resource-card:hover, .grid-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 28px {t["card_shadow_hover"]};
            border-color: {t["card_border_hover"]};
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: {t["card_bg"]};
            border-radius: 16px !important;
            border: 1px solid {t["card_border"]} !important;
            box-shadow: 0 4px 18px {t["card_shadow"]};
            transition: box-shadow 0.18s ease, border-color 0.18s ease;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
            border-color: {t["card_border_hover"]} !important;
            box-shadow: 0 8px 28px {t["card_shadow_hover"]};
        }}

        .resource-title, .grid-title {{
            font-size: 1.28rem;
            font-weight: 700;
            color: {t["text_primary"]};
            margin-bottom: 0.5rem;
            letter-spacing: -0.2px;
        }}
        .summary-text, .grid-desc {{
            color: {t["summary_text"]};
            line-height: 1.6;
            margin: 0.8rem 0;
        }}
        .meta-text {{
            color: {t["meta_text"]};
            font-size: 0.85rem;
            margin-top: 0.45rem;
        }}
        .meta-text a {{ color: {t["accent"]}; }}

        /* ---------- BADGES ---------- */
        .badge, .type-pill {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 999px;
            font-size: 0.76rem;
            font-weight: 600;
            margin-right: 6px;
            margin-bottom: 4px;
            letter-spacing: 0.2px;
        }}
        .badge-score {{ background: {t["badge_score_bg"]}; color: {t["badge_score_text"]}; border: 1px solid {t["badge_score_border"]}; }}
        .badge-relevance {{ background: {t["badge_relevance_bg"]}; color: {t["badge_relevance_text"]}; border: 1px solid {t["badge_relevance_border"]}; }}
        .badge-free {{ background: {t["badge_free_bg"]}; color: {t["badge_free_text"]}; border: 1px solid {t["badge_free_border"]}; }}
        .badge-paid {{ background: {t["badge_paid_bg"]}; color: {t["badge_paid_text"]}; border: 1px solid {t["badge_paid_border"]}; }}
        .badge-level {{ background: {t["badge_level_bg"]}; color: {t["badge_level_text"]}; border: 1px solid {t["badge_level_border"]}; }}
        .type-Course {{ background: {t["type_course"]}; color: {t["type_course_text"]}; }}
        .type-Documentation {{ background: {t["type_doc"]}; color: {t["type_doc_text"]}; }}
        .type-Video {{ background: {t["type_video"]}; color: {t["type_video_text"]}; }}
        .type-Article {{ background: {t["type_article"]}; color: {t["type_article_text"]}; }}
        .type-Repository {{ background: {t["type_repo"]}; color: {t["type_repo_text"]}; }}

        /* ---------- BUTTONS ---------- */
        .stButton > button, .stLinkButton > a {{
            border-radius: 10px !important;
            border: 1px solid {t["button_border"]} !important;
            background: {t["button_bg"]} !important;
            color: {t["button_text"]} !important;
            font-weight: 600 !important;
            transition: all 0.15s ease !important;
        }}
        .stButton > button:hover, .stLinkButton > a:hover {{
            border-color: {t["accent"]} !important;
            background: {t["button_bg_hover"]} !important;
            color: {t["button_text_hover"]} !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px {t["card_shadow_hover"]};
        }}
        .stButton > button[kind="primary"] {{
            background: linear-gradient(135deg, {t["accent"]}, {t["accent"]}) !important;
            border: none !important;
            color: #ffffff !important;
        }}
        .stButton > button[kind="primary"]:hover {{
            box-shadow: 0 6px 18px {t["card_shadow_hover"]};
        }}

        /* ---------- INPUTS ---------- */
        .stTextInput input, .stTextArea textarea, .stSelectbox > div > div {{
            background-color: {t["input_bg"]} !important;
            border: 1px solid {t["input_border"]} !important;
            border-radius: 10px !important;
            color: {t["input_text"]} !important;
            transition: border-color 0.15s ease;
        }}
        .stTextInput input:focus, .stTextArea textarea:focus {{
            border-color: {t["accent"]} !important;
            box-shadow: 0 0 0 3px {t["card_shadow_hover"]} !important;
        }}

        /* ---------- SIDEBAR ---------- */
        section[data-testid="stSidebar"] {{
            background: {t["sidebar_bg"]};
            border-right: 1px solid {t["sidebar_border"]};
        }}

        /* ---------- TABS ---------- */
        .stTabs [data-baseweb="tab"] {{
            color: {t["tab_text"]};
            font-weight: 600;
        }}
        .stTabs [aria-selected="true"] {{
            color: {t["tab_text_selected"]} !important;
        }}

        /* ---------- ALERTS ---------- */
        div[data-testid="stAlert"] {{
            border-radius: 12px;
            border: 1px solid {t["alert_border"]};
        }}

        /* ---------- DIVIDERS ---------- */
        hr {{
            border-color: {t["divider"]} !important;
            margin: 1.6rem 0 !important;
        }}

        /* ---------- SUBTLE FADE-IN ---------- */
        div[data-testid="stVerticalBlockBorderWrapper"], .resource-card, .grid-card {{
            animation: fadeIn 0.35s ease;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(6px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
    </style>
    """, unsafe_allow_html=True)

    render_footer()


TYPE_ICONS = {"Course": "🎓", "Documentation": "📄", "Video": "🎬", "Article": "📰", "Repository": "💻"}


def _resolve_thumbnail(r) -> str:
    if r.thumbnail_url:
        return r.thumbnail_url
    return get_or_generate_resource_thumbnail(r.title, r.url)


def render_grid_card(r, saved_label=None, context="default"):
    type_class = f"type-{r.resource_type}" if r.resource_type in TYPE_ICONS else "type-Course"
    thumbnail = _resolve_thumbnail(r)

    st.image(thumbnail, use_container_width=True)
    st.markdown(f"""
    <div class="grid-card" style="margin-top:-0.4rem; border-top-left-radius:0; border-top-right-radius:0;">
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
            st.image(_resolve_thumbnail(r), use_container_width=True)

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

    st.image(_resolve_thumbnail(r), use_container_width=True)
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