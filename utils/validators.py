"""
validators.py

Small, dependency-free validation helpers.

Why this file exists:
Opportunity data ultimately gets shown to real students making real decisions
(deadlines, eligibility, links). Before anything reaches the UI or gets
passed to Claude, we want a single place that checks "is this record shaped
the way we expect?" rather than scattering ad-hoc checks across pages.
"""

from __future__ import annotations
from datetime import date, datetime
from typing import Any

REQUIRED_OPPORTUNITY_FIELDS = [
    "id",
    "title",
    "organization",
    "category",
    "description",
    "eligibility",
    "location",
    "remote_status",
    "deadline",
    "application_url",
    "official_source",
    "skills",
    "fields",
    "education_level",
    "country_eligibility",
    "funding",
    "date_added",
    "last_verified",
]

VALID_CATEGORIES = {
    "Internship",
    "Scholarship",
    "Fellowship",
    "Hackathon",
    "Competition",
    "Grant",
    "Research",
    "Conference",
    "Volunteer",
    "AI/Tech Program",
    "Other",
}


def validate_opportunity(record: dict[str, Any]) -> list[str]:
    """
    Check a single opportunity record against the schema.

    Returns a list of human-readable problems. An empty list means the
    record is structurally valid. This does NOT check factual accuracy
    (that's what last_verified / verification_status are for) -- only
    shape: are the required fields present and roughly the right type.
    """
    problems: list[str] = []

    for field in REQUIRED_OPPORTUNITY_FIELDS:
        if field not in record:
            problems.append(f"Missing required field: '{field}'")

    if problems:
        # No point checking types if fields are missing outright.
        return problems

    if not isinstance(record["title"], str) or not record["title"].strip():
        problems.append("'title' must be a non-empty string")

    if not isinstance(record["application_url"], str) or not record["application_url"].startswith(
        ("http://", "https://")
    ):
        problems.append("'application_url' must be a full http(s) URL")

    if record["category"] not in VALID_CATEGORIES:
        problems.append(
            f"'category' value '{record['category']}' is not one of {sorted(VALID_CATEGORIES)}"
        )

    for list_field in ("skills", "fields", "education_level", "country_eligibility"):
        if not isinstance(record[list_field], list):
            problems.append(f"'{list_field}' must be a list")

    deadline = record.get("deadline")
    if deadline is not None:
        if not _is_valid_iso_date(deadline):
            problems.append("'deadline' must be an ISO date (YYYY-MM-DD) or null")

    for date_field in ("date_added", "last_verified"):
        if not _is_valid_iso_date(record.get(date_field, "")):
            problems.append(f"'{date_field}' must be a valid ISO date (YYYY-MM-DD)")

    return problems


def _is_valid_iso_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except (TypeError, ValueError):
        return False


def validate_dataset(records: list[dict[str, Any]]) -> dict[str, list[str]]:
    """
    Validate an entire opportunity list.
    Returns a dict of {opportunity_id_or_index: [problems]} for any record
    that failed validation. Empty dict means everything passed.
    """
    errors: dict[str, list[str]] = {}
    seen_ids: set[str] = set()

    for i, record in enumerate(records):
        key = record.get("id", f"index_{i}")
        problems = validate_opportunity(record)

        rec_id = record.get("id")
        if rec_id in seen_ids:
            problems.append(f"Duplicate id '{rec_id}'")
        elif rec_id:
            seen_ids.add(rec_id)

        if problems:
            errors[key] = problems

    return errors


def is_valid_url(value: str) -> bool:
    return isinstance(value, str) and value.startswith(("http://", "https://")) and len(value) > 10


def clean_text_input(value: str, max_length: int = 8000) -> str:
    """Trim and cap user-pasted text before it goes anywhere near a prompt."""
    if not isinstance(value, str):
        return ""
    value = value.strip()
    return value[:max_length]
