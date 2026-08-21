import streamlit as st
from shared import get_graph, render_result, render_result_compact, apply_custom_css
from pipeline.rank import rank_resources
from pipeline.storage import init_db, log_search
from pipeline.graph import run_pipeline_streaming

apply_custom_css()
init_db()

st.markdown('<p class="main-title">📚 Skill Atlas</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Discover the best learning resources — not just the popular ones.</p>', unsafe_allow_html=True)

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

if "selected_resource_url" not in st.session_state:
    st.session_state["selected_resource_url"] = None

if search_clicked and topic.strip():
    clean_topic = topic.strip()
    username = st.session_state.get("username")

    st.session_state["selected_resource_url"] = None

    status = st.empty()
    live_container = st.container()
    found = []  # plain list instead of a counter var, so the closure below can mutate it

    def on_result(resource):
        found.append(resource)
        status.info(f"🔎 Found {len(found)} resource(s) so far — still searching...")
        with live_container:
            render_result_compact(resource)

    status.info("🔎 Searching the web...")
    final_state = run_pipeline_streaming(
        clean_topic,
        resource_type=resource_type,
        price_type=price_type,
        difficulty_level=difficulty_level,
        on_result=on_result,
    )
    status.empty()

    st.session_state["results"] = final_state["ranked_results"]
    st.session_state["fallback_results"] = final_state["analyzed_results"]
    st.session_state["last_topic"] = clean_topic

    log_search(username, clean_topic, len(final_state["ranked_results"]))

    # Re-run once so the page settles into the normal, ranked/deduped display
    # below instead of leaving the raw arrival-order list on screen.
    st.rerun()

if "results" not in st.session_state:
    st.session_state["results"] = None
if "fallback_results" not in st.session_state:
    st.session_state["fallback_results"] = None
if "last_topic" not in st.session_state:
    st.session_state["last_topic"] = ""

if st.session_state["results"] is not None:
    results = st.session_state["results"]
    topic_used = st.session_state["last_topic"]
    all_available = results if results else rank_resources(st.session_state["fallback_results"])

    selected_url = st.session_state["selected_resource_url"]

    if selected_url:
        selected = next((r for r in all_available if r.url == selected_url), None)
        if selected:
            from shared import render_result_detail
            render_result_detail(selected, topic=topic_used)
        else:
            st.session_state["selected_resource_url"] = None
            st.rerun()
    else:
        if results:
            st.success(f"Found {len(results)} resources for '{topic_used}'")
            for r in results:
                render_result_compact(r)
        else:
            fallback = rank_resources(st.session_state["fallback_results"])
            if fallback:
                st.warning("No exact match for your filters — here are other resources on this topic:")
                for r in fallback:
                    render_result_compact(r)
            else:
                st.error("No resources found at all for this topic. Try a different search term.")