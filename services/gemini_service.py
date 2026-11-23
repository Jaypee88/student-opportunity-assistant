"""
Gemini AI service for the Student Opportunity Assistant.

This module provides the Gemini equivalent of the Claude AI service.
It is intended for free development/testing when Claude API access
is unavailable.
"""

import os
import json
import re
from typing import Any, Optional

from google import genai
import streamlit as st


class GeminiServiceError(Exception):
    """Raised when a Gemini API operation fails."""
    pass


class GeminiService:
    """Handles communication with Google's Gemini API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        if not self.api_key:
            try:
                self.api_key = st.secrets.get("GEMINI_API_KEY")
            except Exception:
                self.api_key = None
        if not self.api_key:
            self.api_key = os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            raise GeminiServiceError(
                "No Gemini API key found. Add GEMINI_API_KEY to your .env file."
            )

        try:
            self.client = genai.Client(api_key=self.api_key)
        except Exception as exc:
            raise GeminiServiceError(
                f"Could not initialize Gemini client: {exc}"
            ) from exc

        # A current Gemini model suitable for general text tasks.
        self.model = "gemini-3.8-flash"

    def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
    ) -> str:
        """
        Send a prompt to Gemini and return the generated text.
        """

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "temperature": temperature,
                },
            )

            if not response.text:
                raise GeminiServiceError(
                    "Gemini returned an empty response."
                )

            return response.text.strip()

        except Exception as exc:
            raise GeminiServiceError(
                f"Gemini request failed: {exc}"
            ) from exc

    def generate_json(
        self,
        prompt: str,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        """
        Ask Gemini to return structured JSON and safely parse the result.
        """

        json_prompt = f"""
{prompt}

IMPORTANT:
Return ONLY valid JSON.
Do not use Markdown code fences.
Do not add explanations before or after the JSON.
"""

        result = self.generate(
            prompt=json_prompt,
            temperature=temperature,
        )

        # Remove accidental Markdown fences if Gemini adds them.
        cleaned = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            result.strip(),
            flags=re.IGNORECASE,
        ).strip()

        try:
            return json.loads(cleaned)

        except json.JSONDecodeError as exc:
            raise GeminiServiceError(
                f"Gemini returned invalid JSON: {exc}"
            ) from exc


def get_gemini_service() -> GeminiService:
    """
    Create and return a GeminiService instance.
    """
    return GeminiService()


def interpret_search_query(
    query: str,
) -> dict[str, Any]:
    """
    Interpret a student's natural-language opportunity search query.

    Example:
        'Find AI internships for Nigerian students that are still open'

    Gemini converts this into structured search criteria.
    """

    service = get_gemini_service()

    prompt = f"""
You are an assistant helping students discover scholarships,
internships, fellowships, competitions, grants, hackathons,
volunteer opportunities, and other educational or career
opportunities.

Interpret the student's search request and extract useful
search criteria.

Student query:
{query}

Return a JSON object with exactly these fields:

{{
    "keywords": [],
    "category": "",
    "field": "",
    "country": "",
    "eligibility": "",
    "remote": null,
    "deadline_status": "",
    "additional_requirements": []
}}

Use empty strings when information is not provided.

For "remote":
- use true if the student explicitly asks for remote opportunities
- use false if the student explicitly asks for in-person opportunities
- use null if they do not specify

Do not invent information that the student did not provide.
"""

    return service.generate_json(prompt)


def analyze_opportunity(
    opportunity: dict[str, Any] | str,
    student_profile: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Analyze an opportunity against a student's profile.

    Returns the same structured format used by the main Claude
    analysis flow so the application UI can use either provider.
    """

    service = get_gemini_service()

    # The function may receive either opportunity text or
    # an opportunity dictionary.
    if isinstance(opportunity, str):
        opportunity_text = opportunity
    else:
        opportunity_text = json.dumps(
            opportunity,
            indent=2,
            ensure_ascii=False,
        )

    student_text = json.dumps(
        student_profile or {},
        indent=2,
        ensure_ascii=False,
    )

    prompt = f"""
You are the AI analysis assistant inside a Student Opportunity Assistant.

Your job is to carefully analyze the opportunity information provided
by the student.

IMPORTANT:
- Use ONLY information contained in the opportunity text.
- Do not invent requirements, eligibility criteria, deadlines,
  documents, benefits, or application procedures.
- If something is not stated, explicitly say that it is not specified.
- Do not infer that a student is eligible unless the available
  information supports that conclusion.
- Distinguish clearly between facts stated in the opportunity and
  reasonable observations.
- Pay particular attention to eligibility, deadline, requirements,
  documents, skills, and application instructions.

OPPORTUNITY INFORMATION:
{opportunity_text}

STUDENT PROFILE:
{student_text}

Analyze the opportunity and return ONLY valid JSON.

Use exactly this structure:

{{
    "overview": "",
    "eligibility": "",
    "deadline": "",
    "requirements": [],
    "documents_needed": [],
    "what_they_look_for": "",
    "important_details": [],
    "potential_concerns": [],
    "fit_for_me": "",
    "action_checklist": []
}}

FIELD INSTRUCTIONS:

overview:
Give a concise explanation of what the opportunity is and what
participants are expected to do or gain, based only on the information
provided.

eligibility:
Explain who is eligible according to the provided information.
If a student profile is provided, explain whether the profile appears
to match the stated criteria. Clearly identify anything that cannot
be verified.

deadline:
Give the exact deadline if one is stated. If no deadline is provided,
write "Not specified in the provided information."

requirements:
List the actual requirements stated in the opportunity.
Do not invent requirements.

documents_needed:
List documents or materials that applicants are explicitly asked
to provide. If none are stated, use an empty list.

what_they_look_for:
Explain the qualities, skills, experience, interests, or background
the opportunity appears to value, based on the provided information.

important_details:
List important facts the student should know before applying.

potential_concerns:
List uncertainties, restrictions, missing information, or possible
issues the student should verify before applying.

fit_for_me:
If a student profile is provided, explain how well the opportunity
appears to fit that student. If no profile is provided, write
"No student profile provided."

action_checklist:
Give practical actions the student should take before applying,
based only on the opportunity information and reasonable preparation
steps. Do not invent application requirements.

Return ONLY the JSON object.
Do not use Markdown code fences.
Do not add any explanation before or after the JSON.
"""

    return service.generate_json(prompt)
