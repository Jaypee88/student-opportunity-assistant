"""pages/assistant.py — Multi-turn conversation about a single selected opportunity.

Uses the Claude Messages API's native multi-turn support: we keep the growing
message list in session_state and resend it (plus the opportunity's data,
injected into the system prompt) on every turn, exactly as the Messages API
expects for conversational context.
"""

import streamlit as st

from services.opportunity_service import load_opportunities, get_opportunity_by_id
from services.claude_service import ask_about_opportunity, ClaudeServiceError
from utils.ui_components import render_opportunity_detail


def render() -> None:
    st.markdown("## \U0001F4AC Opportunity Assistant")
    st.caption("Ask follow-up questions about a specific opportunity. Answers are grounded in its verified record.")

    opportunities = load_opportunities()
    if not opportunities:
        st.info("No opportunities in the database yet.")
        return

    id_to_title = {o["id"]: f"{o['title']} \u2014 {o['organization']}" for o in opportunities}
    default_id = st.session_state.get("assistant_selected_id") or opportunities[0]["id"]
    ids = list(id_to_title.keys())

    selected_id = st.selectbox(
        "Which opportunity?",
        options=ids,
        format_func=lambda i: id_to_title[i],
        index=ids.index(default_id) if default_id in ids else 0,
    )
    st.session_state.assistant_selected_id = selected_id
    opp = get_opportunity_by_id(selected_id, opportunities)

    with st.expander("Opportunity details", expanded=False):
        render_opportunity_detail(opp)

    st.divider()

    chats = st.session_state.opportunity_chats
    history = chats.setdefault(selected_id, [])

    for msg in history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    suggestions = [
        "Am I eligible based on my profile?",
        "What documents do I need to prepare?",
        "What project could strengthen my application?",
        "Help me build a preparation plan.",
    ]
    st.caption("Try asking: " + " \u2022 ".join(f'"{s}"' for s in suggestions))

    user_input = st.chat_input("Ask a question about this opportunity...")
    if user_input:
        history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    reply = ask_about_opportunity(
                        opportunity=opp,
                        conversation_history=history,
                        student_profile=st.session_state.student_profile or None,
                    )
                    st.write(reply)
                    history.append({"role": "assistant", "content": reply})
                except ClaudeServiceError as e:
                    st.error(str(e))
                    history.pop()  # remove the user turn we couldn't answer, so retry is clean

    if history and st.button("Clear this conversation"):
        chats[selected_id] = []
        st.rerun()
