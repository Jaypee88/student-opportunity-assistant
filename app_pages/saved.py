"""pages/saved.py — Saved opportunities and an upcoming-deadlines view."""

import streamlit as st

from services.opportunity_service import load_opportunities, sort_opportunities
from utils.ui_components import render_opportunity_card, render_opportunity_detail
from utils.helpers import compute_status, format_deadline


def render() -> None:
    st.markdown("## \U0001F516 Saved Opportunities")

    all_opps = load_opportunities()
    saved_ids = st.session_state.saved_opportunity_ids

    if st.session_state.selected_opportunity_id and st.session_state.selected_opportunity_id in saved_ids:
        opp = next((o for o in all_opps if o["id"] == st.session_state.selected_opportunity_id), None)
        if opp:
            if st.button("\u2190 Back to saved list"):
                st.session_state.selected_opportunity_id = None
                st.rerun()
            render_opportunity_detail(opp)
            return

    saved_opps = [o for o in all_opps if o["id"] in saved_ids]

    if not saved_opps:
        st.info(
            "You haven't saved any opportunities yet. Browse **Discover Opportunities** or "
            "**My Recommendations** and click \u2606 Save on anything interesting."
        )
        return

    open_soonish = [o for o in saved_opps if compute_status(o) in ("Open", "Closing Soon")]
    open_soonish = sort_opportunities(open_soonish, sort_by="deadline_asc")

    if open_soonish:
        st.markdown("### \u23F0 Upcoming deadlines")
        for opp in open_soonish[:5]:
            badge = "\U0001F7E1" if compute_status(opp) == "Closing Soon" else "\U0001F7E2"
            st.markdown(f"{badge} **{opp['title']}** \u2014 {format_deadline(opp)}")
        st.divider()

    st.markdown(f"### All saved ({len(saved_opps)})")
    saved_opps = sort_opportunities(saved_opps, sort_by="deadline_asc")
    for opp in saved_opps:
        render_opportunity_card(opp, key_prefix="saved")
