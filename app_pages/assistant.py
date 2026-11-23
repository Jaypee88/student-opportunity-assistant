"""Opportunity Assistant — provider-selectable, grounded multi-turn chat."""

import streamlit as st

from services.opportunity_service import load_opportunities, get_opportunity_by_id
from services.chat_provider_service import (
    ask_with_provider,
    provider_is_configured,
    ChatProviderError,
)
from utils.ui_components import render_opportunity_detail


def render() -> None:
    st.markdown(
        """
        <div style="padding:.35rem 0 .7rem">
          <div style="font-size:.78rem;font-weight:750;letter-spacing:.12em;text-transform:uppercase;color:#635bdb">
            STUDENT SUPPORT · AI ASSISTANT
          </div>
          <h1 style="margin:.25rem 0 .35rem">Opportunity Assistant</h1>
          <p style="max-width:720px;font-size:1.02rem">
            Get clear answers about eligibility, requirements and how to prepare.
            Responses stay grounded in the opportunity you select.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    opportunities = load_opportunities()
    if not opportunities:
        st.info("No opportunities are available in the database yet.")
        return

    id_to_title = {
        item["id"]: f'{item["title"]} — {item["organization"]}'
        for item in opportunities
    }
    default_id = st.session_state.get("assistant_selected_id") or opportunities[0]["id"]
    ids = list(id_to_title)

    top_left, top_right = st.columns([2.2, 1])
    with top_left:
        selected_id = st.selectbox(
            "Choose an opportunity",
            options=ids,
            format_func=lambda item_id: id_to_title[item_id],
            index=ids.index(default_id) if default_id in ids else 0,
        )
    with top_right:
        provider = st.selectbox(
            "AI model",
            options=["Gemini", "Claude"],
            index=0,
            help="Gemini is the default. Claude requires an Anthropic API key.",
            key="assistant_provider",
        )

    st.session_state.assistant_selected_id = selected_id
    opp = get_opportunity_by_id(selected_id, opportunities)

    configured = provider_is_configured(provider)
    if configured:
        st.caption(f"● {provider} is configured · You can switch providers at any time.")
    elif provider == "Gemini":
        st.warning(
            "Gemini needs to be configured by the app owner before chat can run. "
            "Add GEMINI_API_KEY to Streamlit Secrets."
        )
    else:
        st.info(
            "Claude is optional and requires an Anthropic API key. "
            "Switch to Gemini or configure ANTHROPIC_API_KEY to use Claude."
        )

    with st.expander("View opportunity details", expanded=False):
        render_opportunity_detail(opp)

    st.divider()
    chats = st.session_state.opportunity_chats
    history = chats.setdefault(selected_id, [])

    if not history:
        st.markdown("#### What would you like to understand?")
        suggestions = [
            "Am I eligible based on my profile?",
            "What documents should I prepare?",
            "What skills or experience would strengthen my application?",
            "Help me create a preparation checklist.",
        ]
        cols = st.columns(2)
        for index, suggestion in enumerate(suggestions):
            with cols[index % 2]:
                if st.button(
                    suggestion,
                    key=f"assistant_suggestion_{selected_id}_{index}",
                    use_container_width=True,
                ):
                    st.session_state["_assistant_pending_prompt"] = suggestion
                    st.rerun()

    for message in history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    pending_prompt = st.session_state.pop("_assistant_pending_prompt", None)
    user_input = st.chat_input("Ask a question about this opportunity...")
    prompt = user_input or pending_prompt

    if prompt:
        history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner(f"{provider} is thinking..."):
                try:
                    reply = ask_with_provider(
                        provider=provider,
                        opportunity=opp,
                        conversation_history=history,
                        student_profile=st.session_state.student_profile or None,
                    )
                    st.markdown(reply)
                    history.append({"role": "assistant", "content": reply})
                except ChatProviderError as exc:
                    st.error(str(exc))
                    history.pop()

    if history:
        if st.button("Clear conversation", type="secondary"):
            chats[selected_id] = []
            st.rerun()
