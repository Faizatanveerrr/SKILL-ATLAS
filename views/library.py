import streamlit as st
from shared import render_result, apply_custom_css
from pipeline.storage import get_saved_resources_for_user

apply_custom_css()

st.markdown('<p class="main-title">📚 Library</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Resources you\'ve saved.</p>', unsafe_allow_html=True)

username = st.session_state.get("username")
saved = get_saved_resources_for_user(username)

if not saved:
    st.info("You haven't saved any resources yet. Find something useful on the Discover page and click Save.")
else:
    for r in saved:
        render_result(r, show_save_button=False)