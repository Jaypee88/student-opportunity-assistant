"""pages/recommendations.py — Personalized opportunity matching."""

import streamlit as st

from services.opportunity_service import load_opportunities
from services.recommendation_service import rank_opportunities
from services.claude_service import (
    explain_recommendation,
    ClaudeServiceError,
)
from utils.helpers import (
    format_deadline,
    status_badge_markdown,
    compute_status,
)


MATCH_COLORS = {
    "High": "🟢",
    "Medium": "🟡",
    "Low": "⚪",
}


REMOTE_OPTIONS = [
    "No preference",
    "Remote",
    "On-site",
    "Hybrid",
]

OPPORTUNITY_TYPES = [
    "Internship",
    "Scholarship",
    "Fellowship",
    "Hackathon",
    "Competition",
    "Grant",
    "Research",
    "Conference",
    "Volunteer",
    "AI/Tech Program",
]


def render() -> None:
    st.markdown("## 🎯 My Recommendations")
    st.caption(
        "Find opportunities that match your student profile or "
        "create a temporary custom search."
    )

    profile = st.session_state.student_profile

    # ---------------------------------------------------------
    # Recommendation mode
    # ---------------------------------------------------------

    if profile:
        mode = st.radio(
            "Recommendation mode",
            [
                "Use my profile",
                "Customize this search",
            ],
            horizontal=True,
        )
    else:
        st.info(
            "You do not have a saved profile yet. "
            "You can create one on the My Profile page or customize "
            "a search below."
        )

        mode = "Customize this search"

    # ---------------------------------------------------------
    # Determine which profile the scoring engine will use
    # ---------------------------------------------------------

    if mode == "Use my profile":
        recommendation_profile = profile

        st.success(
            "Using your saved profile for recommendations."
        )

    else:
        recommendation_profile = _render_custom_search()

        if not recommendation_profile:
            return

    # ---------------------------------------------------------
    # Load and rank opportunities
    # ---------------------------------------------------------

    opportunities = load_opportunities()

    if not opportunities:
        st.info("No opportunities in the database yet.")
        return

    ranked = rank_opportunities(
        recommendation_profile,
        opportunities,
    )

    if not ranked:
        st.info("No matching opportunities found.")
        return

    st.markdown(
        f"### Recommended opportunities ({len(ranked)})"
    )

    # ---------------------------------------------------------
    # Display recommendations
    # ---------------------------------------------------------

    for item in ranked:
        opp = item["opportunity"]
        score = item["score"]

        with st.container(border=True):
            top = st.columns([5, 1])

            with top[0]:
                st.markdown(f"**{opp['title']}**")
                st.caption(
                    f"{opp['organization']} • {opp['category']}"
                )

            with top[1]:
                st.markdown(
                    f"""
                    <div style='text-align:right; font-size:1.4rem;'>
                        {MATCH_COLORS[score['match_level']]}
                    </div>
                    <div style='text-align:right; font-weight:700;'>
                        {score['match_level']}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown(
                status_badge_markdown(
                    compute_status(opp)
                ),
                unsafe_allow_html=True,
            )

            st.caption(
                f"Score: {score['total_score']}/100 • "
                f"Deadline: {format_deadline(opp)}"
            )

            with st.expander(
                "Why this score? (transparent breakdown)"
            ):
                for key, comp in score["components"].items():
                    label = key.replace("_", " ").title()

                    st.progress(
                        (
                            min(
                                comp["score"] / comp["max"],
                                1.0,
                            )
                            if comp["max"]
                            else 0
                        ),
                        text=(
                            f"{label}: "
                            f"{comp['score']}/{comp['max']} — "
                            f"{comp['reason']}"
                        ),
                    )

            explain_key = f"explain_{opp['id']}"

            btn_cols = st.columns([1, 1, 2])

            with btn_cols[0]:
                if st.button(
                    "Explain in plain English",
                    key=f"explain_btn_{opp['id']}",
                ):
                    with st.spinner("Asking Claude..."):
                        try:
                            explanation = explain_recommendation(
                                opp,
                                recommendation_profile,
                                score,
                            )

                            st.session_state[
                                explain_key
                            ] = explanation

                        except ClaudeServiceError as e:
                            st.session_state[
                                explain_key
                            ] = f"(Explanation unavailable: {e})"

            with btn_cols[1]:
                if st.button(
                    "View details",
                    key=f"rec_view_{opp['id']}",
                ):
                    st.session_state.selected_opportunity_id = (
                        opp["id"]
                    )

                    st.session_state.nav_page = (
                        "Discover Opportunities"
                    )

                    st.rerun()

            with btn_cols[2]:
                st.link_button(
                    "Official page ↗",
                    opp["application_url"],
                )

            if explain_key in st.session_state:
                st.info(
                    st.session_state[explain_key]
                )


def _render_custom_search() -> dict | None:
    """
    Collect temporary recommendation preferences.

    Important:
    These values are NOT saved to student_profile.
    They are only used for this recommendation request.
    """

    st.markdown("### Customize this search")

    st.caption(
        "These preferences are temporary and will not change your saved profile."
    )


    with st.form("custom_recommendation_form"):
        c1, c2 = st.columns(2)

        with c1:
            field_of_study = st.text_input(
                "Field of study",
                placeholder="e.g. Computer Engineering",
            )

        with c2:
            academic_level = st.text_input(
                "Academic level",
                placeholder="e.g. 300",
            )

        country = st.text_input(
            "Country / location",
            placeholder="e.g. Nigeria",
        )

        remote_pref = st.selectbox(
            "Remote / on-site preference",
            REMOTE_OPTIONS,
        )

        interests = st.text_input(
            "Interests / fields",
            placeholder="AI/ML, software engineering",
        )

        skills = st.text_input(
            "Skills",
            placeholder="Python, Machine Learning",
        )

        preferred_categories = st.multiselect(
            "Opportunity types",
            OPPORTUNITY_TYPES,
        )

        submitted = st.form_submit_button(
            "Find opportunities",
            type="primary",
        )

    if not submitted:
        return None

    return {
        "field_of_study": field_of_study.strip(),
        "academic_level": academic_level.strip(),
        "country": country.strip(),
        "remote_preference": remote_pref,
        "fields_of_interest": [
            item.strip()
            for item in interests.split(",")
            if item.strip()
        ],
        "skills": [
            item.strip()
            for item in skills.split(",")
            if item.strip()
        ],
        "preferred_categories": preferred_categories,
    }