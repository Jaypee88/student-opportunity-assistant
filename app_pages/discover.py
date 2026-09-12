"""pages/discover.py — Search, filter, and browse the opportunity database."""

import streamlit as st

from services.opportunity_service import (
    load_opportunities,
    search_opportunities,
    sort_opportunities,
    get_all_categories,
    get_all_fields,
)
from services.claude_service import interpret_search_query, ClaudeServiceError
from utils.ui_components import render_opportunity_card, render_opportunity_detail
from utils.helpers import compute_status


def render() -> None:
    st.markdown("## \U0001F50D Discover Opportunities")
    st.caption("Search naturally, or use the filters. Results come only from our verified database.")

    all_opps = load_opportunities()

    # If a card's "View details" was clicked, show the detail view and stop.
    if st.session_state.selected_opportunity_id:
        opp = next((o for o in all_opps if o["id"] == st.session_state.selected_opportunity_id), None)
        if opp:
            if st.button("\u2190 Back to results"):
                st.session_state.selected_opportunity_id = None
                st.rerun()
            render_opportunity_detail(opp)
            return
        else:
            st.session_state.selected_opportunity_id = None

    with st.form("search_form"):
        query = st.text_input(
            "Search",
            placeholder='e.g. "AI internships for undergraduates" or "scholarships for African students"',
            label_visibility="collapsed",
        )
        col_a, col_b = st.columns([1, 3])
        with col_a:
            smart_search = st.checkbox("Use AI to interpret my search", value=True)
        submitted = col_b.form_submit_button("Search", use_container_width=False)

    with st.expander("Filters", expanded=False):
        f1, f2, f3 = st.columns(3)
        category = f1.selectbox("Category", ["Any"] + get_all_categories(all_opps))
        field = f2.selectbox("Field", ["Any"] + get_all_fields(all_opps))
        edu_level = f3.selectbox("Academic level", ["Any", "Undergraduate", "Graduate"])

        f4, f5, f6 = st.columns(3)
        remote = f4.selectbox("Remote / on-site", ["Any", "Remote", "On-site", "Hybrid"])
        status_options = ["Open", "Closing Soon", "Closed", "Date Uncertain", "Verification Needed"]
        status_filter = f5.multiselect("Status", status_options, default=["Open", "Closing Soon"])
        sort_by = f6.selectbox(
            "Sort by", ["deadline_asc", "deadline_desc", "recently_added", "title_az"],
            format_func=lambda x: {
                "deadline_asc": "Deadline (soonest first)",
                "deadline_desc": "Deadline (latest first)",
                "recently_added": "Recently added",
                "title_az": "Title (A-Z)",
            }[x],
        )

    keywords = []
    search_note = None

    if submitted and query.strip():
        st.session_state.search_query = query
        if smart_search:
            try:
                interpretation = interpret_search_query(query)
                keywords = interpretation.get("keywords", [])
                if interpretation.get("explanation"):
                    search_note = interpretation["explanation"]
                if interpretation.get("categories") and category == "Any":
                    # Only auto-apply an AI-suggested category if the student hasn't set one manually.
                    ai_categories = interpretation["categories"]
                    if len(ai_categories) == 1:
                        category = ai_categories[0]
            except ClaudeServiceError as e:
                st.info(f"Smart search unavailable ({e}) — using plain keyword search instead.")
                keywords = query.split()
        else:
            keywords = query.split()
    elif st.session_state.search_query and not submitted:
        keywords = st.session_state.search_query.split()

    results = search_opportunities(
        keywords=keywords or None,
        category=None if category == "Any" else category,
        field=None if field == "Any" else field,
        remote_status=None if remote == "Any" else remote,
        education_level=None if edu_level == "Any" else edu_level,
        status_filter=status_filter or None,
        opportunities=all_opps,
    )
    results = sort_opportunities(results, sort_by=sort_by)

    if search_note:
        st.caption(f"\U0001F9E0 {search_note}")

    st.markdown(f"**{len(results)} opportunit{'y' if len(results) == 1 else 'ies'} found**")

    if not results:
        st.info(
            "No opportunities match your search yet. Try broadening your filters, or clearing the "
            "status filter to include Closed / Date Uncertain listings."
        )
        return

    for opp in results:
        render_opportunity_card(opp, key_prefix="discover")
