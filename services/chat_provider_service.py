"""Provider routing for conversational and research-enabled student assistance."""
import json
import os
import time
from typing import Optional

import streamlit as st
from google import genai

from services.claude_service import ask_about_opportunity, ClaudeServiceError


class ChatProviderError(Exception):
    """Friendly error raised when a selected chat provider is unavailable."""


def _gemini_api_key() -> Optional[str]:
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
    return bool(_gemini_api_key()) if provider == "Gemini" else (
        _claude_is_configured() if provider == "Claude" else False
    )


def _build_prompt(opportunity, profile, research_context, history):
    transcript = []
    for message in history[-12:]:
        role = "Student" if message.get("role") == "user" else "Assistant"
        transcript.append(f"{role}: {message.get('content', '')}")

    return f"""You are Student Opportunity Assistant, a warm, capable conversational guide for university students.

HOW TO BEHAVE:
- This is a real conversation, not a form-filling document analyser. Respond naturally to greetings and ordinary questions.
- Help with opportunity discovery, scholarships, internships, fellowships, grants, competitions, application preparation, and eligibility.
- If live research results are supplied, synthesize them into a useful answer. Identify the opportunity, organization, who it targets, deadline/status, requirements, benefits, and official application/source link when the evidence contains those facts.
- Explicitly distinguish facts stated by an official source, claims from third-party sources, and details that could not be verified. Never describe a listing as currently open unless current evidence from an official source supports that.
- If search results are weak or absent, say so and suggest a narrower search. Never invent search results, URLs, dates, eligibility, CGPA thresholds, funding, or requirements.
- Personalize against the student profile. Separate confirmed matches from unknown details. Ask only the most useful follow-up question when a missing profile detail blocks a confident assessment.
- When an opportunity is a likely match, explain why and what still needs checking. Never guarantee eligibility or selection.
- If a specific opportunity record is supplied, use it as context but do not assume its old verification date proves current availability.
- Keep the answer conversational, useful, and appropriately concise. Use headings/bullets when they improve scanning.
- Do not repeat a generic empty analysis template. Do not say the student must paste opportunity text when they are asking you to find opportunities.
- Do not claim to have applied, contacted an organization, or verified a page you did not access.
- Current date: {__import__('datetime').date.today().isoformat()}.

STUDENT PROFILE:
{json.dumps(profile or {}, ensure_ascii=False, indent=2)}

SELECTED OPPORTUNITY (may be null):
{json.dumps(opportunity, ensure_ascii=False, indent=2) if opportunity else "None — this is a general assistant conversation."}

LIVE WEB RESEARCH RESULTS:
{json.dumps(research_context or [], ensure_ascii=False, indent=2) if research_context else "No live web search was run for this turn."}

RECENT CONVERSATION:
{chr(10).join(transcript)}

Reply to the student's latest message. Include useful source URLs from the research results where relevant."""


def ask_with_provider(
    provider: str,
    opportunity: Optional[dict],
    conversation_history: list[dict[str, str]],
    student_profile: Optional[dict] = None,
    research_context: Optional[list[dict]] = None,
) -> str:
    """Use the selected provider with the same conversation, profile and research context."""
    if provider not in ("Gemini", "Claude"):
        raise ChatProviderError("Please select Gemini or Claude.")

    if provider == "Claude":
        if not _claude_is_configured():
            raise ChatProviderError(
                "Claude is not configured for this deployment. Add ANTHROPIC_API_KEY "
                "to Streamlit Secrets to enable it, or switch to Gemini."
            )
        try:
            return ask_about_opportunity(
                opportunity=opportunity or {},
                conversation_history=conversation_history,
                student_profile=student_profile,
                research_context=research_context,
            )
        except ClaudeServiceError as exc:
            raise ChatProviderError(str(exc)) from exc

    api_key = _gemini_api_key()
    if not api_key:
        raise ChatProviderError(
            "Gemini is not configured. Add GEMINI_API_KEY to Streamlit Secrets "
            "for deployment or to your local .env file."
        )

    prompt = _build_prompt(opportunity, student_profile, research_context, conversation_history)
    client = genai.Client(api_key=api_key)
    models_to_try = ["gemini-3.8-flash", "gemini-3.5-flash-lite"]
    last_error = None

    for model_index, model_name in enumerate(models_to_try):
        attempts = 2 if model_index == 0 else 1
        for attempt in range(attempts):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config={"temperature": 0.35},
                )
                if not response.text:
                    raise ChatProviderError("Gemini returned an empty response. Please try again.")
                return response.text.strip()
            except ChatProviderError:
                raise
            except Exception as exc:
                last_error = exc
                message = str(exc)
                if "API_KEY_INVALID" in message or "API key not valid" in message:
                    raise ChatProviderError(
                        "Google rejected the Gemini API key. Check that the active key "
                        "is correctly saved in Streamlit Secrets."
                    ) from exc
                temporary = any(
                    marker in message.upper()
                    for marker in ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED",
                                   "500", "502", "504", "INTERNAL", "DEADLINE_EXCEEDED")
                )
                if not temporary:
                    raise ChatProviderError(f"Gemini could not complete the request: {message}") from exc
                if attempt < attempts - 1:
                    time.sleep(2 ** (attempt + 1))

    raise ChatProviderError(
        "Gemini is temporarily unavailable. The app retried the primary model and "
        "tried its lightweight fallback. Please try again shortly."
    ) from last_error
