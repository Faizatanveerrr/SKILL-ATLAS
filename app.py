import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from shared import init_session_state

st.set_page_config(page_title="Skill Atlas", page_icon="📚", layout="wide")

with open("config.yaml") as f:
    config = yaml.load(f, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
)
tab1, tab2 = st.tabs(["Login", "Sign Up"])

with tab1:
    authenticator.login(key="login_form_unique")

with tab2:
    try:
        email, username, name = authenticator.register_user(pre_authorized=None)
        if email:
            with open("config.yaml", "w") as f:
                yaml.dump(config, f, default_flow_style=False)
            st.success("Account created successfully! Please go to the Login tab.")
    except Exception as e:
        st.error(e)


if st.session_state.get("authentication_status") is False:
    st.error("Username or password is incorrect")
elif st.session_state.get("authentication_status") is None:
    st.warning("Please enter your username and password")
else:
    init_session_state()

    with st.sidebar:
        st.write(f"Welcome, **{st.session_state['name']}**")
        authenticator.logout("Logout", "sidebar")

    pg = st.navigation([
        st.Page("views/discover.py", title="Discover", icon="🏠", default=True),
        st.Page("views/library.py", title="Library", icon="📚"),
        st.Page("views/history.py", title="History", icon="🕐"),
        st.Page("views/profile.py", title="Profile", icon="👤"),
        st.Page("views/settings.py", title="Settings", icon="⚙️"),
    ])
    pg.run()