"""
claude_service.py

This is the ONLY module in the app that talks to the Anthropic API.
Every page that needs Claude (Analyze, Assistant, Recommendations,
Application Helper, Discover's smart search) calls a function here
rather than building its own client or prompt.

Why centralize this:
1. One place to handle missing API keys, rate limits, and malformed
   responses consistently.
2. One place to enforce the "don't invent information" rule via the
   system prompt, instead of hoping every page remembers to say it.
3. Prompt design lives here as data (see utils/claude_prompts.py), which
   makes it easy to review/tune without touching UI code.

Design choice: structured JSON output.
Several functions ask Claude to return JSON (wrapped in a strict system
instruction) so the app can reliably parse fields into UI components
instead of scraping free-form text. If parsing fails, we fall back to
showing the raw text with a warning rather than crashing.
"""

from __future__ import annotations
import json
import os
import re
from typing import Any, Optional

import anthropic
import streamlit as st

from utils.claude_prompts import (
    ANALYSIS_SYSTEM_PROMPT,
    ASSISTANT_SYSTEM_PROMPT,
    APPLICATION_HELPER_SYSTEM_PROMPT,
    RECOMMENDATION_EXPLAIN_SYSTEM_PROMPT,
    SEARCH_INTERPRETER_SYSTEM_PROMPT,
    build_analysis_user_prompt,
    build_recommendation_user_prompt,
    build_search_interpreter_user_prompt,
)

MODEL = "claude-sonnet-4-6"
MAX_TOKENS_ANALYSIS = 2000
MAX_TOKENS_CHAT = 1200
MAX_TOKENS_SHORT = 600


class ClaudeServiceError(Exception):
    """Raised for any Claude-related failure the UI should show a friendly message for."""


def _get_api_key() -> Optional[str]:
    """
    Look for the API key in Streamlit secrets first (for Streamlit Cloud),
    then fall back to environment variables (for local dev with .env via
    python-dotenv, loaded in app.py).
    """
    try:
        if "ANTHROPIC_API_KEY" in st.secrets:
            return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass
    return os.environ.get("ANTHROPIC_API_KEY")


def get_client() -> anthropic.Anthropic:
    api_key = _get_api_key()
    if not api_key:
        raise ClaudeServiceError(
            "No Anthropic API key found. Add ANTHROPIC_API_KEY to your .env file "
            "(local) or to Streamlit secrets (deployed)."
        )
    return anthropic.Anthropic(api_key=api_key)


def _call_claude(
    system_prompt: str,
    messages: list[dict[str, str]],
    max_tokens: int = MAX_TOKENS_CHAT,
) -> str:
    """
    Low-level wrapper around client.messages.create with consistent error
    handling. Returns the concatenated text of the response.
    """
    client = get_client()

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
        )
    except anthropic.AuthenticationError as e:
        raise ClaudeServiceError(
            "The Anthropic API key was rejected. Double-check it's correct and active."
        ) from e
    except anthropic.RateLimitError as e:
        raise ClaudeServiceError(
            "Claude is receiving too many requests right now. Please wait a moment and try again."
        ) from e
    except anthropic.APIConnectionError as e:
        raise ClaudeServiceError(
            "Couldn't reach the Anthropic API. Check your internet connection and try again."
        ) from e
    except anthropic.APIStatusError as e:
        raise ClaudeServiceError(
            f"The Anthropic API returned an error (status {e.status_code}). Please try again."
        ) from e
    except Exception as e:  # noqa: BLE001 - last-resort catch for the UI
        raise ClaudeServiceError(f"Unexpected error calling Claude: {e}") from e

    text_parts = [block.text for block in response.content if block.type == "text"]
    return "\n".join(text_parts).strip()


def _extract_json(raw_text: str) -> Optional[dict]:
    """
    Best-effort extraction of a JSON object from Claude's response, in case
    it wraps the JSON in ```json fences or adds stray text around it.
    """
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned.strip())
    cleaned = re.sub(r"```$", "", cleaned.strip())
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return None


# ---------------------------------------------------------------------------
# 1. Natural-language search interpretation
# ---------------------------------------------------------------------------

def interpret_search_query(query: str) -> dict[str, Any]:
    """
    Turn a free-text search ("Python + AI but I'm still an undergrad") into
    structured filter hints: keywords, likely categories, likely fields,
    likely education level. The opportunity_service then does the actual
    filtering against real data -- Claude only proposes search terms, it
    never sees or invents opportunity results here.

    Returns a dict like:
    {
        "keywords": ["python", "ai", "machine learning"],
        "categories": ["Internship", "Research"],
        "education_level": "Undergraduate",
        "explanation": "..."
    }
    Falls back to a simple keyword split if Claude/JSON parsing fails.
    """
    try:
        raw = _call_claude(
            system_prompt=SEARCH_INTERPRETER_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": build_search_interpreter_user_prompt(query)}],
            max_tokens=MAX_TOKENS_SHORT,
        )
        parsed = _extract_json(raw)
        if parsed:
            return parsed
    except ClaudeServiceError:
        pass

    # Fallback: naive keyword split, so search still works without Claude.
    return {
        "keywords": [w for w in re.split(r"[\s,]+", query) if len(w) > 2],
        "categories": [],
        "education_level": None,
        "explanation": "Interpreted using simple keyword matching (Claude unavailable).",
    }


# ---------------------------------------------------------------------------
# 2. Opportunity analysis
# ---------------------------------------------------------------------------

def analyze_opportunity(pasted_text: str, student_profile: Optional[dict] = None) -> dict[str, Any]:
    """
    Analyze pasted opportunity text and return a structured breakdown.
    This is the core "Analyze an Opportunity" feature.

    The system prompt strictly instructs Claude to only use information
    present in the pasted text (and the profile, for the "fit" section),
    and to write "Not specified in the provided information." for
    anything absent, rather than inferring or inventing it.
    """
    user_prompt = build_analysis_user_prompt(pasted_text, student_profile)
    raw = _call_claude(
        system_prompt=ANALYSIS_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
        max_tokens=MAX_TOKENS_ANALYSIS,
    )
    parsed = _extract_json(raw)
    if parsed:
        return parsed

    # If structured parsing fails, surface the raw analysis rather than
    # hiding it -- better an unstructured answer than none.
    return {"_raw_fallback": raw}


# ---------------------------------------------------------------------------
# 3. Opportunity Q&A (multi-turn, grounded in one opportunity)
# ---------------------------------------------------------------------------

def ask_about_opportunity(
    opportunity: dict,
    conversation_history: list[dict[str, str]],
    student_profile: Optional[dict] = None,
) -> str:
    """
    Continue a conversation about a specific opportunity.

    conversation_history is a list of {"role": "user"/"assistant", "content": str}
    in Messages API format, NOT including the system prompt. The opportunity
    record and student profile are injected into the system prompt on every
    call, so Claude always has the grounding context even in a long thread.
    """
    system_prompt = ASSISTANT_SYSTEM_PROMPT.format(
        opportunity_json=json.dumps(opportunity, indent=2),
        profile_json=json.dumps(student_profile, indent=2) if student_profile else "Not provided.",
    )
    return _call_claude(
        system_prompt=system_prompt,
        messages=conversation_history,
        max_tokens=MAX_TOKENS_CHAT,
    )


# ---------------------------------------------------------------------------
# 4. Recommendation explanations
# ---------------------------------------------------------------------------

def explain_recommendation(opportunity: dict, student_profile: dict, score_breakdown: dict) -> str:
    """
    Given a deterministic score_breakdown (computed by recommendation_service,
    NOT by Claude), ask Claude to explain the match in plain language.
    Claude explains reasoning; it does not compute the score itself.
    """
    user_prompt = build_recommendation_user_prompt(opportunity, student_profile, score_breakdown)
    return _call_claude(
        system_prompt=RECOMMENDATION_EXPLAIN_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
        max_tokens=MAX_TOKENS_SHORT,
    )


# ---------------------------------------------------------------------------
# 5. Application Helper (coach, not ghostwriter)
# ---------------------------------------------------------------------------

def application_helper_respond(
    conversation_history: list[dict[str, str]],
    opportunity: Optional[dict] = None,
) -> str:
    """
    Drive the Application Helper conversation. The system prompt instructs
    Claude to first help the student understand the prompt and identify
    relevant real experiences, and to only draft text using experiences the
    student has actually supplied -- never fabricated achievements.
    """
    context = json.dumps(opportunity, indent=2) if opportunity else "No specific opportunity selected."
    system_prompt = APPLICATION_HELPER_SYSTEM_PROMPT.format(opportunity_json=context)
    return _call_claude(
        system_prompt=system_prompt,
        messages=conversation_history,
        max_tokens=MAX_TOKENS_CHAT,
    )
