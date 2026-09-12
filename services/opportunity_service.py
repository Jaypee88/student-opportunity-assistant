"""
opportunity_service.py

This module owns the opportunity dataset. It is the ONLY place in the app
that reads data/opportunities.json. Every other module (pages, the
recommendation service, Claude prompts) goes through the functions here.

Why centralize this:
- One place to swap JSON for SQLite/Postgres later without touching pages.
- One place to enforce "we never show a record that failed validation."
- Search/filter logic stays consistent across Discover, Recommendations,
  and the Assistant's opportunity picker.

This module does NOT call Claude. Natural-language search *interpretation*
(turning "something with Python and AI for undergrads" into filter terms)
is handled by claude_service.interpret_search_query, and the result is fed
back into search_opportunities() here as plain keywords/filters. This keeps
a hard boundary: Claude proposes, this module disposes.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Optional

from utils.validators import validate_dataset
from utils.helpers import compute_status

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "opportunities.json"


def load_opportunities(path: Path = DATA_PATH, strict: bool = False) -> list[dict[str, Any]]:
    """
    Load and validate the opportunity dataset.

    If strict=True, raises on any validation error (useful for a CI/test
    check). If strict=False (default, used by the running app), invalid
    records are dropped and skipped rather than crashing the app for every
    student -- a single malformed record in the JSON should not take the
    whole platform down.
    """
    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    records = raw.get("opportunities", [])
    errors = validate_dataset(records)

    if errors and strict:
        lines = [f"{k}: {', '.join(v)}" for k, v in errors.items()]
        raise ValueError("Invalid opportunity records:\n" + "\n".join(lines))

    valid_ids = {r.get("id") for r in records if r.get("id") not in errors}
    return [r for r in records if r.get("id") in valid_ids]


def get_opportunity_by_id(opp_id: str, opportunities: Optional[list[dict]] = None) -> Optional[dict]:
    opportunities = opportunities if opportunities is not None else load_opportunities()
    for opp in opportunities:
        if opp["id"] == opp_id:
            return opp
    return None


def _matches_keywords(opp: dict, keywords: list[str]) -> bool:
    """A record matches if ANY keyword appears in title/description/fields/skills/org/category."""
    if not keywords:
        return True

    haystack = " ".join(
        [
            opp.get("title", ""),
            opp.get("description", ""),
            opp.get("organization", ""),
            opp.get("category", ""),
            opp.get("eligibility", ""),
            " ".join(opp.get("skills", [])),
            " ".join(opp.get("fields", [])),
        ]
    ).lower()

    return any(kw.lower().strip() in haystack for kw in keywords if kw.strip())


def search_opportunities(
    keywords: Optional[list[str]] = None,
    category: Optional[str] = None,
    field: Optional[str] = None,
    location: Optional[str] = None,
    remote_status: Optional[str] = None,
    education_level: Optional[str] = None,
    country: Optional[str] = None,
    skills: Optional[list[str]] = None,
    status_filter: Optional[list[str]] = None,
    opportunities: Optional[list[dict]] = None,
) -> list[dict]:
    """
    Filter the dataset by any combination of criteria. All filters are
    optional and combine with AND logic. `keywords` combine with OR logic
    against each other (matching any keyword is enough).

    This function does plain, deterministic filtering -- no AI involved.
    """
    opportunities = opportunities if opportunities is not None else load_opportunities()
    results = []

    for opp in opportunities:
        if keywords and not _matches_keywords(opp, keywords):
            continue
        if category and opp.get("category") != category:
            continue
        if field and not any(field.lower() in f.lower() for f in opp.get("fields", [])):
            continue
        if location and location.lower() not in opp.get("location", "").lower():
            continue
        if remote_status and opp.get("remote_status") != remote_status:
            continue
        if education_level and education_level not in opp.get("education_level", []):
            continue
        if country:
            eligible_countries = [c.lower() for c in opp.get("country_eligibility", [])]
            if not any(country.lower() in c or "global" in c for c in eligible_countries):
                continue
        if skills:
            opp_skills = [s.lower() for s in opp.get("skills", [])]
            if not any(s.lower() in opp_skills for s in skills):
                continue
        if status_filter:
            if compute_status(opp) not in status_filter:
                continue

        results.append(opp)

    return results


def sort_opportunities(opportunities: list[dict], sort_by: str = "deadline_asc") -> list[dict]:
    """
    sort_by options: 'deadline_asc', 'deadline_desc', 'recently_added', 'title_az'
    Records with no deadline sort to the end for deadline sorts.
    """
    from utils.helpers import parse_iso_date

    if sort_by == "title_az":
        return sorted(opportunities, key=lambda o: o.get("title", "").lower())

    if sort_by == "recently_added":
        return sorted(opportunities, key=lambda o: o.get("date_added", ""), reverse=True)

    def deadline_key(o):
        d = parse_iso_date(o.get("deadline"))
        return (d is None, d)  # None deadlines sort last

    reverse = sort_by == "deadline_desc"
    return sorted(opportunities, key=deadline_key, reverse=reverse)


def get_all_categories(opportunities: Optional[list[dict]] = None) -> list[str]:
    opportunities = opportunities if opportunities is not None else load_opportunities()
    return sorted({o["category"] for o in opportunities})


def get_all_fields(opportunities: Optional[list[dict]] = None) -> list[str]:
    opportunities = opportunities if opportunities is not None else load_opportunities()
    fields = set()
    for o in opportunities:
        fields.update(o.get("fields", []))
    return sorted(fields)


def get_all_skills(opportunities: Optional[list[dict]] = None) -> list[str]:
    opportunities = opportunities if opportunities is not None else load_opportunities()
    skills = set()
    for o in opportunities:
        skills.update(o.get("skills", []))
    return sorted(skills)
