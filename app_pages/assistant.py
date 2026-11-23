"""Conversational Student Opportunity Assistant with live opportunity discovery."""
import streamlit as st

from services.opportunity_service import load_opportunities, get_opportunity_by_id
from services.chat_provider_service import ask_with_provider, provider_is_configured, ChatProviderError
from services.research_service import search_opportunities, is_opportunity_discovery, is_simple_greeting
from utils.ui_components import render_opportunity_detail


def render() -> None:
    st.markdown(
        """
        <div style="padding:.4rem 0 1rem">
          <div style="font-size:.78rem;font-weight:750;letter-spacing:.12em;text-transform:uppercase;color:#635bdb">
            YOUR STUDENT SUPPORT PARTNER
          </div>
          <h1 style="margin:.25rem 0 .35rem">Opportunity Assistant</h1>
          <p style="max-width:760px;font-size:1.02rem;color:var(--text-color)">
            Ask naturally. Discover current opportunities, understand requirements,
            and see how they fit your student profile.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    opportunities = load_opportunities()
    options = ["General assistant"] + [item["id"] for item in opportunities]
    titles = {"General assistant": "General conversation · Search the web"}
    titles.update({
        item["id"]: f'{item["title"]} — {item["organization"]}'
        for item in opportunities
    })

    left, right = st.columns([2.2, 1])
    with left:
        selected = st.selectbox(
            "Conversation context",
            options=options,
            format_func=lambda key: titles[key],
            index=options.index(st.session_state.get("assistant_selected_id"))
            if st.session_state.get("assistant_selected_id") in options else 0,
        )
    with right:
        provider = st.selectbox(
            "AI provider",
            ["Gemini", "Claude"],
            index=0,
            key="assistant_provider",
            help="Gemini is the default. Claude is optional and requires its own API key.",
        )

    opportunity = None if selected == "General assistant" else get_opportunity_by_id(selected, opportunities)
    if provider_is_configured(provider):
        st.caption(f"● {provider} is configured")
    elif provider == "Gemini":
        st.warning("Gemini is not configured. Add GEMINI_API_KEY to Streamlit Secrets.")
    else:
        st.info("Claude is optional. Add ANTHROPIC_API_KEY to enable it.")

    if opportunity:
        with st.expander("View selected opportunity details", expanded=False):
            render_opportunity_detail(opportunity)

    chat_key = selected
    chats = st.session_state.setdefault("opportunity_chats", {})
    history = chats.setdefault(chat_key, [])

    if not history:
        st.markdown("#### Start wherever you are")
        suggestions = [
            "Hi! What can you help me with?",
            "Find scholarships currently open to Nigerian undergraduates.",
            "Are there internships for Computer Engineering students?",
            "Help me check whether I qualify for an opportunity.",
        ]
        cols = st.columns(2)
        for index, suggestion in enumerate(suggestions):
            with cols[index % 2]:
                if st.button(suggestion, key=f"assistant_start_{selected}_{index}", use_container_width=True):
                    st.session_state["_assistant_pending_prompt"] = suggestion
                    st.rerun()

    for message in history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_input = st.chat_input("Ask about scholarships, internships, eligibility, applications...")
    pending = st.session_state.pop("_assistant_pending_prompt", None)
    prompt = user_input or pending

    if prompt:
        history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        research_results = []
        should_research = is_opportunity_discovery(prompt)
        if should_research:
            with st.status("Searching current opportunity listings...", expanded=False) as status:
                try:
                    research_results = search_opportunities(
                        prompt,
                        profile=st.session_state.get("student_profile") or {},
                    )
                    status.update(
                        label=f"Found {len(research_results)} web results to review",
                        state="complete" if research_results else "error",
                    )
                except Exception as exc:
                    status.update(label="Live search is temporarily unavailable", state="error")
                    st.warning(f"Web research could not run: {exc}")

        with st.chat_message("assistant"):
            try:
                if is_simple_greeting(prompt):
                    reply = (
                        "Hi! 👋 I'm your Student Opportunity Assistant. I can help you "
                        "discover scholarships, internships, fellowships and other opportunities, "
                        "check eligibility against your profile, understand requirements, and "
                        "prepare stronger applications. What are you looking for today?"
                    )
                else:
                    with st.spinner(f"{provider} is preparing your answer..."):
                        reply = ask_with_provider(
                            provider=provider,
                            opportunity=opportunity,
                            conversation_history=history,
                            student_profile=st.session_state.get("student_profile") or None,
                            research_context=research_results,
                        )
                st.markdown(reply)
                history.append({"role": "assistant", "content": reply})
                if research_results:
                    with st.expander("Web sources reviewed", expanded=False):
                        for result in research_results:
                            st.markdown(f"**[{result['title']}]({result['url']})**")
                            st.caption(f"{result['domain']} · {result['source_type']}")
                            if result["snippet"]:
                                st.write(result["snippet"])
                            if result.get("page_excerpt"):
                                with st.expander("Page excerpt", expanded=False):
                                    st.write(result["page_excerpt"][:1800])
            except ChatProviderError as exc:
                st.error(str(exc))
                history.pop()

    if history and st.button("Clear conversation", type="secondary"):
        chats[chat_key] = []
        st.rerun()

    with st.expander("Improve your recommendations", expanded=not bool(st.session_state.get("student_profile"))):
        st.caption("A saved profile helps the assistant compare real eligibility requirements with your details.")
        if not st.session_state.get("student_profile"):
            st.info("Your profile is currently empty. Add your course, level, CGPA, location and interests under My Profile.")
            if st.button("Open My Profile", key="assistant_open_profile"):
                st.session_state.nav_page = "My Profile"
                st.rerun()
        else:
            profile = st.session_state.student_profile
            st.write(
                f"**{profile.get('field_of_study') or 'Course not set'}** · "
                f"{profile.get('academic_level') or 'Level not set'} level · "
                f"{profile.get('country') or 'Location not set'}"
            )
            if not profile.get("cgpa"):
                st.caption("Add your CGPA to improve scholarship eligibility checks.")
