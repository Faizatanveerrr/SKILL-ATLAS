import streamlit as st
from pipeline.graph import build_graph
from pipeline.storage import init_db, save_resource_for_user, is_saved
from pipeline.youtube import is_youtube_url, get_youtube_thumbnail
import html
import logging

logger = logging.getLogger(__name__)


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


def apply_custom_css():
    st.markdown("""
    <style>
        /* ---------- BASE ---------- */
        .stApp {
            background: linear-gradient(180deg, #0b0f1a 0%, #0e1117 100%);
        }
        html, body, [class*="css"] {
            font-family: 'Segoe UI', 'Calibri', sans-serif;
        }

        /* ---------- TYPOGRAPHY ---------- */
        .main-title {
            font-size: 2.4rem;
            font-weight: 800;
            background: linear-gradient(90deg, #ffffff, #93c5fd);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.1rem;
            letter-spacing: -0.5px;
        }
        .subtitle {
            color: #9ca3af;
            font-size: 1.02rem;
            margin-bottom: 1.7rem;
        }

        /* ---------- CARDS ---------- */
        .resource-card, .grid-card {
            background: linear-gradient(145deg, #171b26, #14171f);
            border: 1px solid #262b38;
            border-radius: 16px;
            padding: 1.4rem 1.6rem;
            margin-bottom: 1.1rem;
            box-shadow: 0 4px 18px rgba(0,0,0,0.25);
            transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
        }
        .resource-card:hover, .grid-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 28px rgba(59,130,246,0.15);
            border-color: #334063;
        }

        /* Native bordered containers (st.container(border=True)) */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: linear-gradient(145deg, #171b26, #14171f);
            border-radius: 16px !important;
            border: 1px solid #262b38 !important;
            box-shadow: 0 4px 18px rgba(0,0,0,0.25);
            transition: box-shadow 0.18s ease, border-color 0.18s ease;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color: #334063 !important;
            box-shadow: 0 8px 28px rgba(59,130,246,0.12);
        }

        .resource-title, .grid-title {
            font-size: 1.28rem;
            font-weight: 700;
            color: #f8fafc;
            margin-bottom: 0.5rem;
            letter-spacing: -0.2px;
        }
        .summary-text, .grid-desc {
            color: #b8c0cf;
            line-height: 1.6;
            margin: 0.8rem 0;
        }
        .meta-text {
            color: #7c8798;
            font-size: 0.85rem;
            margin-top: 0.45rem;
        }

        /* ---------- BADGES ---------- */
        .badge, .type-pill {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 999px;
            font-size: 0.76rem;
            font-weight: 600;
            margin-right: 6px;
            margin-bottom: 4px;
            letter-spacing: 0.2px;
        }
        .badge-score { background: rgba(52,211,153,0.14); color: #4ade80; border: 1px solid rgba(74,222,128,0.25); }
        .badge-relevance { background: rgba(96,165,250,0.14); color: #60a5fa; border: 1px solid rgba(96,165,250,0.25); }
        .badge-free { background: rgba(52,211,153,0.14); color: #4ade80; border: 1px solid rgba(74,222,128,0.25); }
        .badge-paid { background: rgba(251,191,36,0.14); color: #fbbf24; border: 1px solid rgba(251,191,36,0.25); }
        .badge-level { background: rgba(167,139,250,0.14); color: #a78bfa; border: 1px solid rgba(167,139,250,0.25); }
        .type-Course { background: rgba(52,211,153,0.14); color: #4ade80; }
        .type-Documentation { background: rgba(96,165,250,0.14); color: #60a5fa; }
        .type-Video { background: rgba(244,114,182,0.14); color: #f472b6; }
        .type-Article { background: rgba(167,139,250,0.14); color: #a78bfa; }
        .type-Repository { background: rgba(251,191,36,0.14); color: #fbbf24; }

        /* ---------- BUTTONS ---------- */
        .stButton > button, .stLinkButton > a {
            border-radius: 10px !important;
            border: 1px solid #2d3348 !important;
            background: linear-gradient(180deg, #1a1f2e, #151925) !important;
            color: #e2e8f0 !important;
            font-weight: 600 !important;
            transition: all 0.15s ease !important;
        }
        .stButton > button:hover, .stLinkButton > a:hover {
            border-color: #3b82f6 !important;
            background: linear-gradient(180deg, #1e2536, #171c29) !important;
            color: #ffffff !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(59,130,246,0.2);
        }
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
            border: none !important;
            color: #ffffff !important;
        }
        .stButton > button[kind="primary"]:hover {
            box-shadow: 0 6px 18px rgba(59,130,246,0.35);
        }

        /* ---------- INPUTS ---------- */
        .stTextInput input, .stTextArea textarea, .stSelectbox > div > div {
            background-color: #141824 !important;
            border: 1px solid #2a3040 !important;
            border-radius: 10px !important;
            color: #f1f5f9 !important;
            transition: border-color 0.15s ease;
        }
        .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 0 3px rgba(59,130,246,0.15) !important;
        }

        /* ---------- SIDEBAR ---------- */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0d1119, #0a0d14);
            border-right: 1px solid #1c2130;
        }

        /* ---------- TABS ---------- */
        .stTabs [data-baseweb="tab"] {
            color: #94a3b8;
            font-weight: 600;
        }
        .stTabs [aria-selected="true"] {
            color: #60a5fa !important;
        }

        /* ---------- ALERTS ---------- */
        div[data-testid="stAlert"] {
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.08);
        }

        /* ---------- DIVIDERS ---------- */
        hr {
            border-color: #1c2130 !important;
            margin: 1.6rem 0 !important;
        }

        /* ---------- SUBTLE FADE-IN ---------- */
        div[data-testid="stVerticalBlockBorderWrapper"], .resource-card, .grid-card {
            animation: fadeIn 0.35s ease;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }
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


def _resolve_thumbnail(r):
    """
    Resolves a thumbnail for a resource card:
    1. Use r.thumbnail_url if already set.
    2. If it's a YouTube link, use the real YouTube thumbnail (fast, free).
    Returns None if nothing is available, so the caller falls back to an
    emoji icon.

    NOTE: AI-generated thumbnails (Stable Diffusion) have been removed --
    they weren't producing relevant images. Real image search (e.g.
    Unsplash) is planned as a replacement; until then, resources without
    a thumbnail_url or YouTube link just show their type icon.
    """
    if r.thumbnail_url:
        return r.thumbnail_url

    if is_youtube_url(r.url):
        try:
            yt_thumb = get_youtube_thumbnail(r.url)
        except Exception:
            logger.exception(f"YouTube thumbnail lookup failed for {r.url}")
            yt_thumb = None
        if yt_thumb:
            return yt_thumb

    return None


def render_result_compact_shell(r):
    """
    Renders the text/badges/buttons for one result card immediately,
    leaving an empty placeholder where the thumbnail will go.
    Returns the placeholder so it can be filled in later, after every
    card's text has already been shown.
    """
    container = st.container(border=True)
    with container:
        price_class = "badge-free" if r.price_type == "Free" else "badge-paid"
        st.markdown(f"""
            <div class="resource-title">{html.escape(r.title)}</div>
            <span class="badge badge-score">⭐ {r.score}/10</span>
            <span class="badge {price_class}">💰 {r.price_type}</span>
            <span class="badge badge-level">🎯 {r.difficulty_level}</span>
        """, unsafe_allow_html=True)

        thumb_placeholder = st.empty()

        st.write("")
        bcol1, bcol2 = st.columns(2, gap="small")
        with bcol1:
            if st.button("ℹ️ About", key=f"about_{r.url}", use_container_width=True):
                st.session_state["selected_resource_url"] = r.url
                st.rerun()
        with bcol2:
            st.link_button("🔗 Visit Site", r.url, use_container_width=True)

    return thumb_placeholder


def fill_thumbnail(placeholder, r, max_width=None):
    """
    Resolves and fills in the thumbnail for a card previously created by
    render_result_compact_shell or render_result_detail.

    max_width: if set, the image is shown at a fixed pixel width instead
    of stretching to fill its container. Use this for the detail page,
    where the container is the full page width and stretching a small
    generated image (512x512) that wide makes it blurry and oversized.
    Card thumbnails should keep max_width=None so they still fill their
    (small) card width via use_container_width.
    """
    thumbnail = _resolve_thumbnail(r)
    if thumbnail:
        if max_width:
            placeholder.image(thumbnail, width=max_width)
        else:
            # Fixed-height, cropped thumbnail strip for cards -- prevents
            # wide YouTube thumbnails (16:9) from stretching the card tall
            # when scaled to full container width via st.image.
            placeholder.markdown(
                f'''<div style="width:100%; height:160px; border-radius:10px;
                    overflow:hidden; margin-bottom:0.4rem; background:#0d1117;
                    display:flex; align-items:center; justify-content:center;">
                    <img src="{thumbnail}" style="width:100%; height:100%;
                        object-fit:contain; display:block;" />
                </div>''',
                unsafe_allow_html=True
            )
    else:
        icon = TYPE_ICONS.get(r.resource_type, "📚")
        placeholder.markdown(
            f'<div style="font-size:2.5rem; text-align:center; padding-top:0.6rem;">{icon}</div>',
            unsafe_allow_html=True
        )


def render_result_compact(r):
    """Kept for backward compatibility: renders text then resolves the thumbnail immediately (blocking)."""
    placeholder = render_result_compact_shell(r)
    fill_thumbnail(placeholder, r)


def render_results_list(results):
    """
    Renders a full list of results in two passes:
    1. All text/badges/buttons render first (fast, no blocking).
    2. Thumbnails are resolved and filled in afterward, one by one.
    """
    placeholders = [(r, render_result_compact_shell(r)) for r in results]

    for r, placeholder in placeholders:
        fill_thumbnail(placeholder, r)


def render_result_detail(r, topic=None):
    import html
    from pipeline.analyse import generate_quiz

    if st.button("← Back to results"):
        st.session_state["selected_resource_url"] = None
        st.rerun()

    prereq_html = f'<div class="meta-text">📋 Prerequisites: {html.escape(", ".join(r.prerequisites))}</div>' if r.prerequisites else ""
    skills_html = f'<div class="meta-text">🧠 Skills Taught: {html.escape(", ".join(r.skills_taught))}</div>' if r.skills_taught else ""
    price_class = "badge-free" if r.price_type == "Free" else "badge-paid"

    # ---- Text content renders first, immediately ----
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

    # ---- Placeholder reserves the thumbnail's spot without blocking anything below ----
    thumb_placeholder = st.empty()

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

    # ---- Thumbnail resolves and fills in last, after the whole page is already usable ----
    # Fixed width here (not full page width) -- the generated image is
    # 512x512 natively, and stretching it across the entire page looks
    # blurry/oversized. 512 keeps it crisp; adjust if your layout is wider.
    fill_thumbnail(thumb_placeholder, r, max_width=512)


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