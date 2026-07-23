import streamlit as st
import yaml

st.markdown('<p class="main-title">⚙️ Settings</p>', unsafe_allow_html=True)

authenticator = st.session_state["authenticator"]
config = st.session_state["config"]

st.subheader("Change Password")

try:
    if authenticator.reset_password(st.session_state["username"]):
        with open("config.yaml", "w") as f:
            yaml.dump(config, f, default_flow_style=False)
        st.success("Password changed successfully.")
except Exception as e:
    st.error(e)