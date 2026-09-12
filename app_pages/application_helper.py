"""pages/application_helper.py — Coaches students through application questions
without fabricating experiences on their behalf."""

import streamlit as st

from services.opportunity_service import load_opportunities, get_opportunity_by_id
from services.claude_service import application_helper_respond, ClaudeServiceError


def render() -> None:
    st.markdown("## \u270D\uFE0F Application Helper")
    st.caption(
        "Paste an application question or essay prompt. Claude will help you understand what's "
        "being asked and think through your own real experiences — it will not invent achievements "
        "or write a generic answer for you."
    )

    opportunities = load_opportunities()
    options = ["None / general application question"] + [
        f"{o['title']} \u2014 {o['organization']}" for o in opportunities
    ]
    choice = st.selectbox("Link to an opportunity? (optional)", options)
    linked_opp = None
    if choice != options[0]:
        idx = options.index(choice) - 1
        linked_opp = opportunities[idx]

    st.info(
        "\U0001F4A1 This is a coach, not a generator. Be ready to share your own experiences — "
        "Claude will ask what's relevant rather than assuming.",
        icon="\U0001F4A1",
    )

    history = st.session_state.application_helper_chat

    for msg in history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if not history:
        placeholder = "Paste the application question, essay prompt, or instructions here..."
    else:
        placeholder = "Continue the conversation..."

    user_input = st.chat_input(placeholder)
    if user_input:
        history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    reply = application_helper_respond(history, opportunity=linked_opp)
                    st.write(reply)
                    history.append({"role": "assistant", "content": reply})
                except ClaudeServiceError as e:
                    st.error(str(e))
                    history.pop()

    if history and st.button("Start a new application"):
        st.session_state.application_helper_chat = []
        st.rerun()
