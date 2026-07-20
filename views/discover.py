import streamlit as st
from shared import get_graph, render_result, apply_custom_css
from pipeline.rank import rank_resources
from pipeline.storage import log_search

apply_custom_css()

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

if search_clicked and topic.strip():
    clean_topic = topic.strip()
    username = st.session_state.get("username")

    with st.spinner("Searching the web, analyzing resources..."):
        app = get_graph()
        initial_state = {
            "topic": clean_topic,
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
        st.session_state["last_topic"] = clean_topic

        log_search(username, clean_topic, len(final_state["ranked_results"]))

if st.session_state["results"] is not None:
    results = st.session_state["results"]
    topic_used = st.session_state["last_topic"]
    if results:
        st.success(f"Found {len(results)} resources for '{topic_used}'")
        for r in results:
            render_result(r, topic=topic_used)
    else:
        fallback = rank_resources(st.session_state["fallback_results"])
        if fallback:
            st.warning("No exact match for your filters — here are other resources on this topic:")
            for r in fallback:
                render_result(r, topic=topic_used)
        else:
            st.error("No resources found at all for this topic. Try a different search term.")