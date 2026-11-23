"""
app.py

Entry point for the Student Opportunity Assistant.
"""

import os
import streamlit as st

# Load local .env values. Streamlit Cloud uses st.secrets instead.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from utils.ui_components import inject_custom_css, init_session_state
from utils.modern_theme import inject_modern_theme
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
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_custom_css()
inject_modern_theme()
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
    "Home": "🏠",
    "Discover Opportunities": "🔎",
    "Analyze an Opportunity": "🧠",
    "My Recommendations": "🎯",
    "Opportunity Assistant": "💬",
    "Application Helper": "✍️",
    "Saved Opportunities": "🔖",
    "About": "ⓘ",
    "My Profile": "👤",
}

if "nav_page" not in st.session_state:
    st.session_state.nav_page = "Home"

with st.sidebar:
    st.markdown("### 🎓 Student Opportunity Assistant")
    st.caption("Discover → Understand → Match → Prepare → Apply")
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
    st.caption(f"🔖 {saved_count} saved opportunit{'y' if saved_count == 1 else 'ies'}")

    _has_claude_key = False
    try:
        _has_claude_key = bool(st.secrets.get("ANTHROPIC_API_KEY"))
    except Exception:
        _has_claude_key = bool(os.environ.get("ANTHROPIC_API_KEY"))

    if not _has_claude_key:
        st.caption("Claude is optional. Gemini is the default chat provider.")

PAGES[st.session_state.nav_page].render()
