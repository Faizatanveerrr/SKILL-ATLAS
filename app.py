import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from shared import init_session_state
import os
from dotenv import load_dotenv

st.set_page_config(page_title="Skill Atlas", page_icon="📚", layout="wide")

with open("config.yaml") as f:
    config = yaml.load(f, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
)
st.session_state["authenticator"] = authenticator
st.session_state["config"] = config

# A user is "logged in" if EITHER the username/password authenticator
# succeeded, OR Streamlit's native OAuth (st.user) says they're logged in.
is_authenticated = (
    st.session_state.get("authentication_status") is True
    or st.user.is_logged_in
)

if not is_authenticated:
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        authenticator.login(key="login_form_unique")

        st.divider()

        # --- Google OAuth login ---
        # Requires a [auth] section in .streamlit/secrets.toml with:
        #   redirect_uri, cookie_secret, client_id, client_secret,
        #   server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
        #
        # If you instead configured a NAMED provider in secrets.toml
        # (e.g. a [auth.google] section), change the call below to:
        #   st.login("google")
        if st.button("Continue with Google", key="google_login_btn", use_container_width=True):
            st.login()

    with tab2:
        try:
            email, username, name = authenticator.register_user(pre_authorized=None)
            if email:
                with open("config.yaml", "w") as f:
                    yaml.dump(config, f, default_flow_style=False)
                st.success("Account created successfully! Please go to the Login tab.")
        except Exception as e:
            st.error(e)

if is_authenticated:
    init_session_state()

    if st.user.is_logged_in:
        display_name = st.user.name
        display_email = st.user.email
        # streamlit_authenticator sets session_state["username"] itself on
        # form login, but Google OAuth never does — set it explicitly here
        # so every page (e.g. discover.py's log_search call) can rely on
        # st.session_state["username"] always being populated.
        st.session_state["username"] = display_email
        st.session_state["name"] = display_name
    else:
        display_name = st.session_state.get("name")
        display_email = st.session_state.get("email")

    with st.sidebar:
        st.write(f"Welcome, **{display_name}**")
        # Route logout correctly depending on how the user signed in.
        if st.user.is_logged_in:
            if st.button("Logout", key="google_logout_btn"):
                st.logout()
        else:
            authenticator.logout("Logout", "sidebar")

    pg = st.navigation([
        st.Page("views/discover.py", title="Discover", icon="🏠", default=True),
        st.Page("views/library.py", title="Library", icon="📚"),
        st.Page("views/history.py", title="History", icon="🕐"),
        st.Page("views/profile.py", title="Profile", icon="👤"),
        st.Page("views/settings.py", title="Settings", icon="⚙️"),
        st.Page("views/playlists.py", title="Playlists", icon="🎵"),
        st.Page("views/roadmap.py", title="Roadmap", icon="🗺️"),
    ])
    pg.run()
    st.stop()  # prevent the login styling block below from rendering under the app




st.markdown("""
    <style>
    .stApp {
        background-color: #0d1117;
    }
    h1 {
        color: #f0f6fc !important;
    }
    p {
        color: #8b949e !important;
    }

    .react-aria-SelectionIndicator {
        display: none !important;
        background-color: transparent !important;
        background: transparent !important;
        background-image: none !important;
        box-shadow: none !important;
        opacity: 0 !important;
        height: 0 !important;
        width: 0 !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: transparent;
        border-bottom: 2px solid #21262d !important;
        padding-bottom: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: transparent;
        color: #8b949e !important;
        font-weight: 600;
        font-size: 16px;
        transition: all 0.2s ease;
        border-bottom: none !important;
    }
    .stTabs [aria-selected="true"] {
        color: #58a6ff !important;
        border-bottom: 2px solid #58a6ff !important;
    }

    div[data-testid="stForm"] {
        border: 1px solid #30363d !important;
        padding: 2.5rem !important;
        border-radius: 12px !important;
        background-color: #161b22 !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3) !important;
    }
    div[data-testid="stTextInputRootElement"] {
        background-color: #0d1117 !important;
        border: 1px solid #30363d !important;
        box-shadow: none !important;
        outline: none !important;
    }
    div[data-testid="stTextInputRootElement"]:hover {
        border: 1px solid #30363d !important;
        box-shadow: none !important;
        outline: none !important;
    }
    div[data-testid="stTextInputRootElement"]:focus-within {
        border: 1px solid #58a6ff !important;
        box-shadow: 0 0 0 1px #58a6ff !important;
        outline: none !important;
    }
    div[data-testid="stTextInputRootElement"] input {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }

    .react-aria-TextField {
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }
    .react-aria-TextField[data-hovered],
    .react-aria-TextField[data-focused],
    .react-aria-TextField[data-focus-visible],
    .react-aria-TextField[data-invalid] {
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }
    .react-aria-TextField input {
        background-color: #0d1117 !important;
        color: #ffffff !important;
        border: 1px solid #30363d !important;
        box-shadow: none !important;
        outline: none !important;
    }
    .react-aria-TextField input:hover,
    .react-aria-TextField input:invalid {
        border: 1px solid #30363d !important;
        box-shadow: none !important;
        outline: none !important;
    }
    .react-aria-TextField input:focus {
        border: 1px solid #58a6ff !important;
        box-shadow: 0 0 0 1px #58a6ff !important;
        outline: none !important;
    }

    input {
        background-color: #0d1117 !important;
        color: #ffffff !important;
        border: 1px solid #30363d !important;
        background-image: none !important;
        outline: none !important;
        box-shadow: none !important;
        -webkit-appearance: none !important;
        appearance: none !important;
    }
    input:hover,
    input:invalid,
    input:hover:invalid,
    input:focus:invalid {
        border: 1px solid #30363d !important;
        box-shadow: none !important;
        outline: none !important;
    }
    input:focus {
        border: 1px solid #58a6ff !important;
        box-shadow: 0 0 0 1px #58a6ff !important;
        outline: none !important;
    }
    input:-webkit-autofill,
    input:-webkit-autofill:hover,
    input:-webkit-autofill:focus {
        -webkit-text-fill-color: #ffffff !important;
        -webkit-box-shadow: 0 0 0px 1000px #0d1117 inset !important;
        box-shadow: 0 0 0px 1000px #0d1117 inset !important;
        transition: background-color 5000s ease-in-out 0s;
    }
    button, 
    [data-testid="baseButton-secondary"], 
    [data-testid="stFormSubmitButton"] button,
    div[class*="st-emotion-cache"] button {
        background-image: none !important;
        background: #161b22 !important;
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        color: #ffffff !important;
        outline: none !important;
        box-shadow: none !important;
        border-image: none !important;
    }
    button:hover, 
    [data-testid="baseButton-secondary"]:hover,
    [data-testid="stFormSubmitButton"] button:hover {
        background-image: none !important;
        background: #1f242c !important;
        background-color: #1f242c !important;
        border: 1px solid #58a6ff !important;
        color: #58a6ff !important;
    }
    div[data-testid="stNotification"] {
        border-radius: 8px;
        border: 1px solid #30363d;
        background-color: #1f242c;
        color: #c9d1d9;
    }
    header, [data-testid="stHeader"] {
        background-color: transparent !important;
    }
    </style>
""", unsafe_allow_html=True)

st.components.v1.html("""
<script>
function killTabHighlight() {
    const doc = window.parent.document;
    const els = doc.querySelectorAll('.react-aria-SelectionIndicator');
    els.forEach(el => {
        if (el.style.display !== 'none') {
            el.style.setProperty('display', 'none', 'important');
        }
    });
}
setInterval(killTabHighlight, 300);
</script>
""", height=0)