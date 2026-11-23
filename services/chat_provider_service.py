"""Provider routing for the multi-turn Opportunity Assistant."""

import json
import os
from typing import Optional

import streamlit as st
from google import genai

from services.claude_service import ask_about_opportunity, ClaudeServiceError


class ChatProviderError(Exception):
    """Friendly error raised when a selected chat provider is unavailable."""


def _gemini_api_key() -> Optional[str]:
    """Read Gemini credentials from Streamlit Secrets or local environment."""
    try:
        key = st.secrets.get("GEMINI_API_KEY")
        if key:
            return str(key).strip()
    except Exception:
        pass
    return os.getenv("GEMINI_API_KEY")


def _claude_is_configured() -> bool:
    try:
        if st.secrets.get("ANTHROPIC_API_KEY"):
            return True
    except Exception:
        pass
    return bool(os.getenv("ANTHROPIC_API_KEY"))


def provider_is_configured(provider: str) -> bool:
    if provider == "Gemini":
        return bool(_gemini_api_key())
    if provider == "Claude":
        return _claude_is_configured()
    return False


def ask_with_provider(
    provider: str,
    opportunity: dict,
    conversation_history: list[dict[str, str]],
    student_profile: Optional[dict] = None,
) -> str:
    """Send the same grounded conversation to the provider selected by the user."""
    if provider == "Claude":
        if not _claude_is_configured():
            raise ChatProviderError(
                "Claude is not configured for this deployment. Add ANTHROPIC_API_KEY "
                "to Streamlit Secrets to enable it, or switch to Gemini."
            )
        try:
            return ask_about_opportunity(
                opportunity=opportunity,
                conversation_history=conversation_history,
                student_profile=student_profile,
            )
        except ClaudeServiceError as exc:
            raise ChatProviderError(str(exc)) from exc

    if provider != "Gemini":
        raise ChatProviderError("Please select Gemini or Claude.")

    api_key = _gemini_api_key()
    if not api_key:
        raise ChatProviderError(
            "Gemini is not configured. Add GEMINI_API_KEY to Streamlit Secrets "
            "for deployment or to your local .env file."
        )

    opportunity_context = json.dumps(
        opportunity, indent=2, ensure_ascii=False
    )
    profile_context = json.dumps(
        student_profile or {}, indent=2, ensure_ascii=False
    )
    transcript = []
    for message in conversation_history:
        role = "Student" if message["role"] == "user" else "Assistant"
        transcript.append(f"{role}: {message['content']}")

    prompt = f"""You are the Student Opportunity Assistant, helping a student
understand one selected opportunity. Be clear, warm, concise, and practical.

GROUNDING RULES:
- Treat the opportunity record below as the source of truth.
- Do not invent eligibility rules, deadlines, requirements, benefits, or links.
- If information is missing, say it is not specified and recommend checking
  the official source.
- Use the student profile only to personalize advice. Never invent profile facts.
- Keep continuity with the conversation transcript.
- Do not claim to have submitted an application or contacted an organization.

VERIFIED OPPORTUNITY RECORD:
{opportunity_context}

STUDENT PROFILE:
{profile_context}

CONVERSATION:
{chr(10).join(transcript)}

Write the next assistant reply only."""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
            config={"temperature": 0.35},
        )
        if not response.text:
            raise ChatProviderError("Gemini returned an empty response. Please try again.")
        return response.text.strip()
    except ChatProviderError:
        raise
    except Exception as exc:
        message = str(exc)
        if "API_KEY_INVALID" in message or "API key not valid" in message:
            raise ChatProviderError(
                "Google rejected the Gemini API key. Check that the replacement key "
                "is active and correctly saved in Streamlit Secrets."
            ) from exc
        raise ChatProviderError(
            f"Gemini could not complete the request: {message}"
        ) from exc
