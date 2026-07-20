import streamlit as st
from pipeline.storage import get_search_history_for_user

st.markdown('<p class="main-title">🕐 History</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Your recent searches.</p>', unsafe_allow_html=True)

username = st.session_state.get("username")
history = get_search_history_for_user(username)

if not history:
    st.info("No searches yet.")
else:
    for entry in history:
        st.write(f"🔍 **{entry['topic']}** — {entry['result_count']} results — {entry['time']}")
        st.divider()