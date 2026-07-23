import streamlit as st
from shared import render_grid_card, render_result_detail, apply_custom_css
from pipeline.storage import get_saved_resources_for_user

apply_custom_css()

st.markdown('<p class="main-title">📚 Library</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Resources you\'ve saved.</p>', unsafe_allow_html=True)

username = st.session_state.get("username")
all_saved = get_saved_resources_for_user(username)

if "selected_resource_url" not in st.session_state:
    st.session_state["selected_resource_url"] = None

selected_url = st.session_state["selected_resource_url"]

if selected_url:
    selected = next((r for r in all_saved if r.url == selected_url), None)
    if selected:
        render_result_detail(selected)
    else:
        st.session_state["selected_resource_url"] = None
        st.rerun()
else:
    search_query = st.text_input("Search saved resources...", placeholder="Search by title")

    type_counts = {}
    for r in all_saved:
        type_counts[r.resource_type] = type_counts.get(r.resource_type, 0) + 1

    tab_labels = [f"All ({len(all_saved)})"] + [f"{t} ({c})" for t, c in type_counts.items()]
    tabs = st.tabs(tab_labels)

    filtered = all_saved
    if search_query.strip():
        filtered = [r for r in filtered if search_query.strip().lower() in r.title.lower()]

    with tabs[0]:
        if not filtered:
            st.info("No saved resources yet." if not all_saved else "No matches found.")
        else:
            for r in filtered:
                render_grid_card(r, context="all")

    for idx, (rtype, count) in enumerate(type_counts.items(), start=1):
        with tabs[idx]:
            type_filtered = [r for r in filtered if r.resource_type == rtype]
            if not type_filtered:
                st.info("No matches found.")
            else:
                for r in type_filtered:
                    render_grid_card(r, context=rtype)