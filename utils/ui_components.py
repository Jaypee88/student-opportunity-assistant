"""
ui_components.py

Shared Streamlit UI building blocks used across multiple pages, so the
opportunity card, detail view, and session-state shape stay identical
whether you're looking at Discover, Recommendations, or Saved.

This keeps app.py and each page focused on page-specific logic instead of
re-implementing card rendering five times.
"""

from __future__ import annotations
import streamlit as st

from utils.helpers import compute_status, format_deadline, status_badge_markdown, safe_join, truncate

CUSTOM_CSS = """
<style>
    /* ---- Typography & base ---- */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Roboto, sans-serif;
    }
    h1, h2, h3 { letter-spacing: -0.01em; }

    /* ---- Opportunity card ---- */
    .opp-card {
        border: 1px solid #e3e3e8;
        border-radius: 14px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 1rem;
        background: #ffffff;
        transition: box-shadow 0.15s ease;
    }
    .opp-card:hover {
        box-shadow: 0 3px 14px rgba(0,0,0,0.06);
    }
    .opp-title {
        font-size: 1.08rem;
        font-weight: 700;
        margin-bottom: 0.1rem;
        color: #1a1a2e;
    }
    .opp-org {
        color: #5b5b6b;
        font-size: 0.92rem;
        margin-bottom: 0.5rem;
    }
    .opp-meta {
        font-size: 0.85rem;
        color: #4b4b58;
        margin: 0.15rem 0;
    }
    .opp-tag {
        display: inline-block;
        background: #f1f1f6;
        color: #444;
        border-radius: 8px;
        padding: 1px 9px;
        font-size: 0.76rem;
        margin: 2px 4px 2px 0;
    }
    .section-label {
        font-weight: 700;
        color: #1a1a2e;
        margin-top: 0.9rem;
        margin-bottom: 0.2rem;
        font-size: 0.95rem;
    }
    .muted { color: #6b6b78; }
    .verify-banner {
        background: #f0ecfb;
        border-left: 4px solid #5b3fa0;
        padding: 0.55rem 0.9rem;
        border-radius: 6px;
        font-size: 0.85rem;
        margin: 0.6rem 0;
    }
</style>
"""


def inject_custom_css() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def init_session_state() -> None:
    """Set up every session_state key the app relies on, once per session."""
    defaults = {
        "student_profile": {},
        "saved_opportunity_ids": [],
        "selected_opportunity_id": None,
        "opportunity_chats": {},       # {opp_id: [ {role, content}, ... ]}
        "application_helper_chat": [],
        "last_analysis": None,
        "last_analysis_source_text": "",
        "search_results": [],
        "search_query": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_opportunity_card(opp: dict, key_prefix: str = "") -> None:
    """
    Renders one opportunity as a card with a status badge, key facts, and
    View / Save actions. Clicking "View details" sets session_state so the
    calling page can render the full detail view (see render_opportunity_detail).
    """
    status = compute_status(opp)
    deadline_str = format_deadline(opp)
    is_saved = opp["id"] in st.session_state.saved_opportunity_ids

    with st.container(border=False):
        st.markdown(
            f"""
            <div class="opp-card">
                <div class="opp-title">{opp['title']}</div>
                <div class="opp-org">{opp['organization']}</div>
                <div class="opp-meta">{status_badge_markdown(status)} &nbsp; \u2022 &nbsp; {opp['category']} &nbsp; \u2022 &nbsp; {opp['location']} ({opp['remote_status']})</div>
                <div class="opp-meta">\U0001F4C5 {deadline_str}</div>
                <div class="opp-meta muted">{truncate(opp.get('description', ''), 180)}</div>
                <div style="margin-top:0.5rem;">
                    {''.join(f'<span class="opp-tag">{s}</span>' for s in opp.get('skills', [])[:5])}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("View details", key=f"{key_prefix}_view_{opp['id']}", use_container_width=True):
                st.session_state.selected_opportunity_id = opp["id"]
                st.rerun()
        with col2:
            label = "\u2605 Saved" if is_saved else "\u2606 Save"
            if st.button(label, key=f"{key_prefix}_save_{opp['id']}", use_container_width=True):
                if is_saved:
                    st.session_state.saved_opportunity_ids.remove(opp["id"])
                else:
                    st.session_state.saved_opportunity_ids.append(opp["id"])
                st.rerun()
        with col3:
            st.link_button("Official page \u2197", opp["application_url"], use_container_width=True)


def render_opportunity_detail(opp: dict) -> None:
    """Full detail view for one opportunity, used on Discover/Recommendations/Saved
    when a card is expanded, and reused by Analyze/Assistant page headers."""
    status = compute_status(opp)
    st.markdown(f"## {opp['title']}")
    st.markdown(f"**{opp['organization']}**")
    st.markdown(status_badge_markdown(status), unsafe_allow_html=True)

    if opp.get("verification_status", "").lower().startswith("needs verification"):
        st.markdown(
            f'<div class="verify-banner">\u26A0\uFE0F {opp["verification_status"]}. '
            f'Please confirm current details on the official page before relying on this listing.</div>',
            unsafe_allow_html=True,
        )

    c1, c2, c3 = st.columns(3)
    c1.metric("Category", opp["category"])
    c2.metric("Location", opp.get("remote_status", "Not specified"))
    c3.metric("Deadline", format_deadline(opp))

    st.markdown('<div class="section-label">Description</div>', unsafe_allow_html=True)
    st.write(opp.get("description", "Not specified in the provided information."))

    st.markdown('<div class="section-label">Eligibility</div>', unsafe_allow_html=True)
    st.write(opp.get("eligibility", "Not specified in the provided information."))

    st.markdown('<div class="section-label">Fields</div>', unsafe_allow_html=True)
    st.write(safe_join(opp.get("fields")))

    st.markdown('<div class="section-label">Skills</div>', unsafe_allow_html=True)
    st.write(safe_join(opp.get("skills")))

    st.markdown('<div class="section-label">Education level</div>', unsafe_allow_html=True)
    st.write(safe_join(opp.get("education_level")))

    st.markdown('<div class="section-label">Country eligibility</div>', unsafe_allow_html=True)
    st.write(safe_join(opp.get("country_eligibility")))

    st.markdown('<div class="section-label">Funding</div>', unsafe_allow_html=True)
    st.write(opp.get("funding", "Not specified in the provided information."))

    if opp.get("deadline_note"):
        st.markdown('<div class="section-label">Deadline note</div>', unsafe_allow_html=True)
        st.caption(opp["deadline_note"])

    st.markdown('<div class="section-label">Source</div>', unsafe_allow_html=True)
    st.caption(
        f"Official source: {opp.get('official_source', 'Not specified')}  \n"
        f"Last verified: {opp.get('last_verified', 'Not specified')}"
    )

    is_saved = opp["id"] in st.session_state.saved_opportunity_ids
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        st.link_button("Official application page \u2197", opp["application_url"], use_container_width=True)
    with b2:
        if st.button("\u2605 Unsave" if is_saved else "\u2606 Save", use_container_width=True, key=f"detail_save_{opp['id']}"):
            if is_saved:
                st.session_state.saved_opportunity_ids.remove(opp["id"])
            else:
                st.session_state.saved_opportunity_ids.append(opp["id"])
            st.rerun()
    with b3:
        if st.button("Analyze opportunity", use_container_width=True, key=f"detail_analyze_{opp['id']}"):
            st.session_state["_prefill_analyze_text"] = (
                f"{opp['title']} \u2014 {opp['organization']}\n\n{opp['description']}\n\n"
                f"Eligibility: {opp['eligibility']}\nDeadline: {format_deadline(opp)}"
            )
            st.session_state["nav_page"] = "Analyze an Opportunity"
            st.rerun()
    with b4:
        if st.button("Ask AI assistant about this", use_container_width=True, key=f"detail_ask_{opp['id']}"):
            st.session_state["nav_page"] = "Opportunity Assistant"
            st.session_state["assistant_selected_id"] = opp["id"]
            st.rerun()
