"""pages/home.py — Landing page: explains the platform and gives clear entry points."""

import streamlit as st
from services.opportunity_service import load_opportunities
from utils.helpers import compute_status


def render() -> None:
    st.markdown(
        """
        <div style="padding: 1.2rem 0 0.4rem 0;">
            <h1 style="font-size:2.3rem; margin-bottom:0.2rem;">Find opportunities that fit where you're going.</h1>
            <p style="font-size:1.15rem; color:#4b4b58; max-width:640px;">
                Discover scholarships, internships, competitions, fellowships and other
                opportunities, understand what they require, and use AI assistance to prepare
                for them — grounded in a verified opportunity database, not guesswork.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    opportunities = load_opportunities()
    open_count = sum(1 for o in opportunities if compute_status(o) in ("Open", "Closing Soon"))

    m1, m2, m3 = st.columns(3)
    m1.metric("Opportunities tracked", len(opportunities))
    m2.metric("Currently open or closing soon", open_count)
    m3.metric("Categories", len({o["category"] for o in opportunities}))

    st.write("")
    st.markdown("### What do you want to do?")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("**\U0001F50D Explore Opportunities**")
        st.caption("Search and filter the verified database.")
        if st.button("Explore Opportunities", use_container_width=True):
            st.session_state.nav_page = "Discover Opportunities"
            st.rerun()
    with c2:
        st.markdown("**\U0001F9E0 Analyze an Opportunity**")
        st.caption("Paste a listing and get a structured breakdown.")
        if st.button("Analyze an Opportunity", use_container_width=True):
            st.session_state.nav_page = "Analyze an Opportunity"
            st.rerun()
    with c3:
        st.markdown("**\U0001F3AF Get Recommendations**")
        st.caption("Tell us about yourself, get ranked matches.")
        if st.button("Get Recommendations", use_container_width=True):
            st.session_state.nav_page = "My Recommendations"
            st.rerun()
    with c4:
        st.markdown("**\u270D\uFE0F Application Helper**")
        st.caption("Coach yourself through an application question.")
        if st.button("Application Helper", use_container_width=True):
            st.session_state.nav_page = "Application Helper"
            st.rerun()

    st.divider()
    st.markdown("### How it works")
    steps = st.columns(5)
    labels = [
        ("1. Discover", "Search real, verified opportunities across categories."),
        ("2. Understand", "See eligibility, deadlines and requirements clearly."),
        ("3. Match", "Get transparent, explainable recommendations."),
        ("4. Prepare", "Analyze listings and plan with AI assistance."),
        ("5. Apply", "Head to the official application page, ready."),
    ]
    for col, (title, desc) in zip(steps, labels):
        with col:
            st.markdown(f"**{title}**")
            st.caption(desc)

    st.divider()
    st.markdown("### Recently added opportunities")
    recent = sorted(opportunities, key=lambda o: o.get("date_added", ""), reverse=True)[:3]
    if not recent:
        st.info("No opportunities in the database yet.")
    else:
        cols = st.columns(len(recent))
        for col, opp in zip(cols, recent):
            with col:
                st.markdown(f"**{opp['title']}**")
                st.caption(f"{opp['organization']} \u2022 {opp['category']}")
                if st.button("View", key=f"home_view_{opp['id']}", use_container_width=True):
                    st.session_state.selected_opportunity_id = opp["id"]
                    st.session_state.nav_page = "Discover Opportunities"
                    st.rerun()
