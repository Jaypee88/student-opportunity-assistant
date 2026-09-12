"""
app.py

Entry point for the Student Opportunity Assistant.

Responsibilities of this file, and ONLY this file:
- Page config and global CSS
- Session state initialization
- Sidebar navigation
- Routing to the right page module

Every page's actual content lives in pages/*.py as a `render()` function.
Data access, Claude calls, and scoring logic live in services/ and are
never duplicated here -- this file is intentionally thin.
"""

import os
import streamlit as st

# Load .env for local development. In deployment (Streamlit Community Cloud),
# secrets come from st.secrets instead, so a missing .env there is expected
# and harmless.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from utils.ui_components import inject_custom_css, init_session_state
from app_pages import (
    home,
    discover,
    analyze,
    recommendations,
    assistant,
    application_helper,
    saved,
    about,
    profile,
)

st.set_page_config(
    page_title="Student Opportunity Assistant",
    page_icon="\U0001F393",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_custom_css()
init_session_state()

PAGES = {
    "Home": home,
    "Discover Opportunities": discover,
    "Analyze an Opportunity": analyze,
    "My Profile": profile,
    "My Recommendations": recommendations,
    "Opportunity Assistant": assistant,
    "Application Helper": application_helper,
    "Saved Opportunities": saved,
    "About": about,
}
ICONS = {
    "Home": "\U0001F3E0",
    "Discover Opportunities": "\U0001F50D",
    "Analyze an Opportunity": "\U0001F9E0",
    "My Recommendations": "\U0001F3AF",
    "Opportunity Assistant": "\U0001F4AC",
    "Application Helper": "\u270D\uFE0F",
    "Saved Opportunities": "\U0001F516",
    "About": "\u2139\uFE0F",
    "My Profile": "👤",
}

if "nav_page" not in st.session_state:
    st.session_state.nav_page = "Home"

with st.sidebar:
    st.markdown("### \U0001F393 Student Opportunity Assistant")
    st.caption("Discover \u2192 Understand \u2192 Match \u2192 Prepare \u2192 Apply")
    st.divider()

    selection = st.radio(
        "Navigate",
        options=list(PAGES.keys()),
        format_func=lambda name: f"{ICONS[name]}  {name}",
        index=list(PAGES.keys()).index(st.session_state.nav_page),
        label_visibility="collapsed",
    )
    if selection != st.session_state.nav_page:
        st.session_state.nav_page = selection
        st.rerun()

    st.divider()
    saved_count = len(st.session_state.get("saved_opportunity_ids", []))
    st.caption(f"\U0001F516 {saved_count} saved opportunit{'y' if saved_count == 1 else 'ies'}")
    _has_secret_key = False
    try:
        _has_secret_key = "ANTHROPIC_API_KEY" in st.secrets
    except Exception:
        _has_secret_key = False
    if not os.environ.get("ANTHROPIC_API_KEY") and not _has_secret_key:
        st.warning(
            "Claude is not configured. Claude-powered features will be unavailable.",
            icon="⚠️",
        )
# Route to the selected page module.
PAGES[st.session_state.nav_page].render()
