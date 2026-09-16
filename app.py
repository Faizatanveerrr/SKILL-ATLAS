import subprocess
import sys
import logging
logging.basicConfig(level=logging.INFO)
from pathlib import Path
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from shared import init_session_state
import os
from dotenv import load_dotenv


@st.cache_resource
def ensure_playwright_browser():
    result = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        st.error(f"Playwright install failed: {result.stderr}")
    return result.returncode == 0

ensure_playwright_browser()
import time
_t0 = time.time()
print(f"[T] script start")


# Workaround for intermittent Windows import race (OSError WinError 6714)
# that can hit pyarrow when it's first imported from Streamlit's background
# ScriptRunner thread (happens inside streamlit_authenticator's cookie
# manager component). Pre-importing here, with retries, forces it into
# sys.modules early so the later lazy import just reuses the cached module.
_t_pa = time.time()
for _attempt in range(5):
    try:
        import pyarrow  # noqa: F401
        break
    except OSError:
        time.sleep(0.2)
print(f"[T] pyarrow pre-import: {time.time()-_t_pa:.2f}s")

print(f"[T] imports done: {time.time()-_t0:.2f}s")

st.set_page_config(page_title="Skill Atlas", page_icon="📚", layout="wide")

# ---------------------------------------------------------------------------
# THEME-AWARE COLORS
# Streamlit does NOT expose global --background-color / --text-color CSS
# variables on the main page (those only exist inside custom-component
# iframes). And st.get_option("theme.base") only reflects config.toml, not
# whatever the user picks live from the ⋮ menu -> Settings -> theme toggle.
#
# So instead we define our OWN CSS variables (--sa-*) with dark-theme
# fallbacks for first paint, and a small JS snippet (below, in the
# components.v1.html block) reads the colors Streamlit is ACTUALLY
# rendering on already-themed native elements (sidebar, links, etc.) and
# writes them into these variables live, on a polling interval. That keeps
# our custom CSS in sync with whatever theme is really active, without
# guessing variable names Streamlit doesn't actually expose here.
# ---------------------------------------------------------------------------
bg            = "var(--sa-bg, #0d1117)"
card_bg       = "var(--sa-card-bg, #161b22)"
input_bg      = "var(--sa-bg, #0d1117)"
text          = "var(--sa-text, #f0f6fc)"
muted         = "var(--sa-text, #8b949e)"     # dimmed via opacity below
border        = "color-mix(in srgb, var(--sa-text, #30363d) 25%, transparent)"
accent        = "var(--sa-accent, #58a6ff)"
button_bg     = "var(--sa-card-bg, #161b22)"
button_hover  = "color-mix(in srgb, var(--sa-card-bg, #161b22) 80%, var(--sa-text, white) 20%)"
notif_bg      = "var(--sa-card-bg, #1f242c)"
notif_text    = "var(--sa-text, #c9d1d9)"

st.markdown(f"""
    <style>
    .stApp {{
        background-color: {bg};
    }}
    h1 {{
        color: {text} !important;
    }}
    p {{
        color: {muted} !important;
        opacity: 0.75;
    }}

    .react-aria-SelectionIndicator {{
        display: none !important;
        background-color: transparent !important;
        background: transparent !important;
        background-image: none !important;
        box-shadow: none !important;
        opacity: 0 !important;
        height: 0 !important;
        width: 0 !important;
    }}

    .stTabs [data-baseweb="tab-list"] {{
        gap: 24px;
        background-color: transparent;
        border-bottom: 2px solid {border} !important;
        padding-bottom: 8px;
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 45px;
        background-color: transparent;
        color: {muted} !important;
        font-weight: 600;
        font-size: 16px;
        transition: all 0.2s ease;
        border-bottom: none !important;
    }}
    .stTabs [aria-selected="true"] {{
        color: {accent} !important;
        border-bottom: 2px solid {accent} !important;
    }}

    div[data-testid="stForm"] {{
        border: 1px solid {border} !important;
        padding: 2.5rem !important;
        border-radius: 12px !important;
        background-color: {card_bg} !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3) !important;
    }}
    div[data-testid="stTextInputRootElement"] {{
        background-color: {input_bg} !important;
        border: 1px solid {border} !important;
        box-shadow: none !important;
        outline: none !important;
    }}
    div[data-testid="stTextInputRootElement"]:hover {{
        border: 1px solid {border} !important;
        box-shadow: none !important;
        outline: none !important;
    }}
    div[data-testid="stTextInputRootElement"]:focus-within {{
        border: 1px solid {accent} !important;
        box-shadow: 0 0 0 1px {accent} !important;
        outline: none !important;
    }}
    div[data-testid="stTextInputRootElement"] input {{
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }}

    .react-aria-TextField {{
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }}
    .react-aria-TextField[data-hovered],
    .react-aria-TextField[data-focused],
    .react-aria-TextField[data-focus-visible],
    .react-aria-TextField[data-invalid] {{
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }}
    .react-aria-TextField input {{
        background-color: {input_bg} !important;
        color: {text} !important;
        border: 1px solid {border} !important;
        box-shadow: none !important;
        outline: none !important;
    }}
    .react-aria-TextField input:hover,
    .react-aria-TextField input:invalid {{
        border: 1px solid {border} !important;
        box-shadow: none !important;
        outline: none !important;
    }}
    .react-aria-TextField input:focus {{
        border: 1px solid {accent} !important;
        box-shadow: 0 0 0 1px {accent} !important;
        outline: none !important;
    }}

    input {{
        background-color: {input_bg} !important;
        color: {text} !important;
        border: 1px solid {border} !important;
        background-image: none !important;
        outline: none !important;
        box-shadow: none !important;
        -webkit-appearance: none !important;
        appearance: none !important;
    }}
    input:hover,
    input:invalid,
    input:hover:invalid,
    input:focus:invalid {{
        border: 1px solid {border} !important;
        box-shadow: none !important;
        outline: none !important;
    }}
    input:focus {{
        border: 1px solid {accent} !important;
        box-shadow: 0 0 0 1px {accent} !important;
        outline: none !important;
    }}
    input:-webkit-autofill,
    input:-webkit-autofill:hover,
    input:-webkit-autofill:focus {{
        -webkit-text-fill-color: {text} !important;
        -webkit-box-shadow: 0 0 0px 1000px {input_bg} inset !important;
        box-shadow: 0 0 0px 1000px {input_bg} inset !important;
        transition: background-color 5000s ease-in-out 0s;
    }}
    button,
    [data-testid="baseButton-secondary"],
    [data-testid="stFormSubmitButton"] button,
    div[class*="st-emotion-cache"] button {{
        background-image: none !important;
        background: {button_bg} !important;
        background-color: {button_bg} !important;
        border: 1px solid {border} !important;
        color: {text} !important;
        outline: none !important;
        box-shadow: none !important;
        border-image: none !important;
    }}
    button:hover,
    [data-testid="baseButton-secondary"]:hover,
    [data-testid="stFormSubmitButton"] button:hover {{
        background-image: none !important;
        background: {button_hover} !important;
        background-color: {button_hover} !important;
        border: 1px solid {accent} !important;
        color: {accent} !important;
    }}
    div[data-testid="stNotification"] {{
        border-radius: 8px;
        border: 1px solid {border};
        background-color: {notif_bg};
        color: {notif_text};
    }}
    header, [data-testid="stHeader"] {{
        background-color: transparent !important;
    }}
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
BASE_DIR = Path(__file__).resolve().parent

import yaml
_t = time.time()
with open(BASE_DIR / "config.yaml", "r") as f:
    config = yaml.safe_load(f)

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
)
print(f"[T] stauth.Authenticate init: {time.time()-_t:.2f}s")

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
    _t = time.time()
    init_session_state()
    print(f"[T] init_session_state: {time.time()-_t:.2f}s")

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
        st.Page("views/create_course.py", title="Micro Course", icon="🎬"),
    ])

    print(f"[T] total before pg.run: {time.time()-_t0:.2f}s")
    _t = time.time()
    pg.run()
    print(f"[T] pg.run (page render): {time.time()-_t:.2f}s")