"""pages/analyze.py — Paste opportunity text, get a structured AI analysis."""

import streamlit as st

from services.claude_service import (
    analyze_opportunity as analyze_with_claude,
    ClaudeServiceError,
)
from services.gemini_service import (
    analyze_opportunity as analyze_with_gemini,
    GeminiServiceError,
)
from utils.validators import clean_text_input


def render() -> None:
    st.markdown("## 🧠 Analyze an Opportunity")
    st.caption(
        "Paste the text of an opportunity — a listing, eligibility page, or application "
        "instructions — and an AI model will break it down. If something isn't stated, "
        "it will say so rather than guess."
    )

    prefill = st.session_state.pop("_prefill_analyze_text", "")

    pasted_text = st.text_area(
        "Opportunity text",
        value=prefill,
        height=260,
        placeholder="Paste the opportunity description, eligibility criteria, and/or application instructions here...",
        label_visibility="collapsed",
    )

    use_profile = st.checkbox(
        "Use my profile for personalized eligibility and fit analysis",
        value=bool(st.session_state.student_profile),
        help=(
            "Your saved profile is managed from the My Profile page. "
            "It is used only to personalize the fit assessment."
        ),
    )

    # AI provider selection
    provider = st.radio(
        "AI Provider",
        options=["Claude", "Gemini"],
        horizontal=True,
    )

    analyze_clicked = st.button(
        f"Analyze with {provider}",
        type="primary",
    )

    if analyze_clicked:
        cleaned = clean_text_input(pasted_text)

        if not cleaned:
            st.warning("Paste some opportunity text first.")
        else:
            profile = (
                st.session_state.student_profile
                if use_profile
                else None
            )

            with st.spinner(f"Analyzing with {provider}..."):
                try:
                    if provider == "Gemini":
                        result = analyze_with_gemini(
                            cleaned,
                            profile,
                        )
                    else:
                        result = analyze_with_claude(
                            cleaned,
                            profile,
                        )

                    st.session_state.last_analysis = result
                    st.session_state.last_analysis_source_text = cleaned
                    st.session_state.last_analysis_provider = provider

                except (ClaudeServiceError, GeminiServiceError) as e:
                    st.error(str(e))
                    st.session_state.last_analysis = None

    result = st.session_state.get("last_analysis")

    if not result:
        return

    st.divider()

    provider_used = st.session_state.get(
        "last_analysis_provider",
        "AI",
    )

    st.caption(f"Analysis provided by {provider_used}")

    if "_raw_fallback" in result:
        st.warning(
            f"{provider_used}'s response could not be parsed into structured sections. "
            "Showing raw output:"
        )
        st.write(result["_raw_fallback"])
        return

    st.markdown("### Overview")
    st.write(
        result.get(
            "overview",
            "Not specified in the provided information.",
        )
    )

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### Eligibility")

        eligibility = result.get("eligibility")

        if isinstance(eligibility, dict):
            status = eligibility.get("status", "")
            reason = eligibility.get("reason", "")

            if status:
                st.write(status)

            if reason:
                st.write(reason)
        else:
            st.write(
                eligibility
                or "Not specified in the provided information."
            )

    with c2:
        st.markdown("### Deadline")
        st.write(
            result.get(
                "deadline",
                "Not specified in the provided information.",
            )
        )

    st.markdown("### Requirements")
    _render_list(result.get("requirements"))

    st.markdown("### Documents needed")
    _render_list(result.get("documents_needed"))

    st.markdown("### What they appear to be looking for")

    st.write(
        result.get(
            "what_they_look_for",
            "Not specified in the provided information.",
        )
    )

    st.markdown("### Important details")
    _render_list(result.get("important_details"))

    st.markdown("### Potential concerns")

    concerns = result.get("potential_concerns")

    if concerns:
        for c in concerns:
            st.warning(c, icon="⚠️")
    else:
        st.caption("None flagged.")

    st.markdown("### Fit for me")

    st.write(
        result.get(
            "fit_for_me",
            "No student profile provided.",
        )
    )

    st.markdown("### Action checklist")

    checklist = result.get("action_checklist", [])

    if checklist:
        for i, item in enumerate(checklist):
            st.checkbox(
                item,
                key=f"checklist_{i}_{hash(item) % 10000}",
            )
    else:
        st.caption("No checklist items generated.")

    st.divider()

    if st.button("💬 Ask follow-up questions about this"):
        st.session_state["_prefill_assistant_context"] = (
            st.session_state.last_analysis_source_text
        )

        st.session_state.nav_page = "Opportunity Assistant"
        st.rerun()


def _render_list(items) -> None:
    if not items:
        st.caption("Not specified in the provided information.")
        return

    for item in items:
        st.markdown(f"- {item}")
