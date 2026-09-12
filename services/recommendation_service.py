"""
recommendation_service.py

Computes match scores between a student profile and opportunities using
transparent, auditable rules -- NOT an AI black box. Claude is used later,
in claude_service.explain_recommendation, only to put the score breakdown
into natural language. This module never calls Claude.

Why deterministic scoring:
The brief is explicit that recommendations must be explainable, not an
arbitrary percentage. A rule-based score means we can always answer
"why did this opportunity score 78?" by pointing at this file.
"""

from __future__ import annotations
from typing import Any

from utils.helpers import compute_status

# Weights sum to 100. Adjust here (in one place) to retune the whole system.
WEIGHTS = {
    "field_match": 30,
    "skill_match": 25,
    "education_level_match": 20,
    "location_eligibility": 15,
    "category_preference": 10,
}


def _field_score(student: dict, opp: dict) -> tuple[float, str]:
    student_fields = {f.lower() for f in student.get("fields_of_interest", []) if f}
    student_field_of_study = (student.get("field_of_study") or "").lower()
    opp_fields = {f.lower() for f in opp.get("fields", [])}

    if not opp_fields or "any field" in " ".join(opp_fields):
        return WEIGHTS["field_match"], "Open to any field of study."

    if not student_fields and not student_field_of_study:
        return 0.0, "No field of study/interest provided to compare."

    all_student_terms = student_fields | ({student_field_of_study} if student_field_of_study else set())
    overlap = any(
        any(term in of or of in term for term in all_student_terms if term)
        for of in opp_fields
    )
    if overlap:
        return WEIGHTS["field_match"], "Your field of study/interest overlaps with this opportunity's fields."
    return 0.0, "No overlap found between your field and this opportunity's fields."


def _skill_score(student: dict, opp: dict) -> tuple[float, str]:
    student_skills = {s.lower().strip() for s in student.get("skills", []) if s}
    opp_skills = {s.lower().strip() for s in opp.get("skills", []) if s}

    if not opp_skills:
        return WEIGHTS["skill_match"] * 0.5, "This opportunity doesn't list specific required skills."
    if not student_skills:
        return 0.0, "No skills listed in your profile to compare."

    overlap = student_skills & opp_skills
    if not overlap:
        return 0.0, "None of your listed skills match this opportunity's listed skills."

    ratio = len(overlap) / len(opp_skills)
    score = WEIGHTS["skill_match"] * min(ratio, 1.0)
    return score, f"You share {len(overlap)} of {len(opp_skills)} listed skill(s): {', '.join(sorted(overlap))}."


def _education_level_score(student: dict, opp: dict) -> tuple[float, str]:
    student_level = (student.get("academic_level") or "").lower()
    opp_levels = [l.lower() for l in opp.get("education_level", [])]

    if not student_level:
        return 0.0, "No academic level provided."
    if not opp_levels or "any" in opp_levels:
        return WEIGHTS["education_level_match"], "Open to any academic level."

    # Undergraduate levels like "300" / "junior" count as "undergraduate".
    if "undergrad" in student_level or student_level.isdigit():
        matches = any("undergraduate" in l for l in opp_levels)
    elif "grad" in student_level or "master" in student_level or "phd" in student_level:
        matches = any("graduate" in l for l in opp_levels)
    else:
        matches = student_level in opp_levels

    if matches:
        return WEIGHTS["education_level_match"], "Your academic level matches this opportunity's stated level(s)."
    return 0.0, f"This opportunity lists {', '.join(opp_levels) or 'no'} academic level(s), which may not match yours."


def _location_score(student: dict, opp: dict) -> tuple[float, str]:
    student_country = (student.get("country") or "").lower().strip()
    opp_countries = [c.lower() for c in opp.get("country_eligibility", [])]
    remote_pref = (student.get("remote_preference") or "").lower()
    opp_remote = (opp.get("remote_status") or "").lower()

    if not opp_countries:
        country_ok = True
        country_note = "No country restriction listed."
    else:
        country_ok = any("global" in c or (student_country and student_country in c) for c in opp_countries)
        country_note = (
            "Your country appears eligible." if country_ok else
            "Your country may not be listed as eligible -- verify on the official page."
        )

    if remote_pref and remote_pref != "no preference":
        remote_ok = remote_pref in opp_remote or opp_remote in remote_pref
    else:
        remote_ok = True

    if country_ok and remote_ok:
        return WEIGHTS["location_eligibility"], country_note
    if country_ok:
        return WEIGHTS["location_eligibility"] * 0.5, country_note + " Remote/on-site preference differs."
    return 0.0, country_note


def _category_score(student: dict, opp: dict) -> tuple[float, str]:
    preferred = {c.lower() for c in student.get("preferred_categories", []) if c}
    if not preferred:
        return WEIGHTS["category_preference"] * 0.5, "No category preference provided."
    if opp.get("category", "").lower() in preferred:
        return WEIGHTS["category_preference"], f"Matches your preferred category: {opp['category']}."
    return 0.0, f"{opp.get('category')} is not among your preferred categories."


def check_eligibility(student_profile, opportunity):
    """
    Perform deterministic eligibility checks.

    Returns:
        {
            "status": "Eligible" | "Not eligible" | "Needs review",
            "checks": [...],
        }
    """

    checks = []

    # ---------------------------------------------------------
    # CGPA requirement
    # ---------------------------------------------------------

    required_cgpa = opportunity.get("minimum_cgpa")
    student_cgpa = student_profile.get("cgpa")

    if required_cgpa is not None:
        if student_cgpa is None or student_cgpa == 0:
            checks.append({
                "requirement": "Minimum CGPA",
                "result": "unknown",
                "reason": f"Requires CGPA of {required_cgpa}+; your CGPA is not provided.",
            })
        elif student_cgpa >= required_cgpa:
            checks.append({
                "requirement": "Minimum CGPA",
                "result": "pass",
                "reason": f"Requires {required_cgpa}+; your CGPA is {student_cgpa}.",
            })
        else:
            checks.append({
                "requirement": "Minimum CGPA",
                "result": "fail",
                "reason": f"Requires {required_cgpa}+; your CGPA is {student_cgpa}.",
            })

    # ---------------------------------------------------------
    # Country / location
    # ---------------------------------------------------------

    eligible_countries = opportunity.get("eligible_countries", [])
    student_country = student_profile.get("country", "").strip().lower()

    if eligible_countries and student_country:
        normalized_countries = [
            country.strip().lower()
            for country in eligible_countries
        ]

        if student_country in normalized_countries:
            checks.append({
                "requirement": "Country eligibility",
                "result": "pass",
                "reason": "Your country is listed as eligible.",
            })
        else:
            checks.append({
                "requirement": "Country eligibility",
                "result": "fail",
                "reason": "Your country is not listed among the eligible countries.",
            })

    # ---------------------------------------------------------
    # Determine overall status
    # ---------------------------------------------------------

    results = [check["result"] for check in checks]

    if "fail" in results:
        overall_status = "Not eligible"
    elif "unknown" in results:
        overall_status = "Needs review"
    else:
        overall_status = "Eligible"

    return {
        "status": overall_status,
        "checks": checks,
    }

def score_opportunity(student_profile: dict, opportunity: dict) -> dict[str, Any]:
    """
    Returns a full, transparent score breakdown:
    {
        "total_score": 0-100,
        "match_level": "High" | "Medium" | "Low",
        "components": {
            "field_match": {"score": .., "max": .., "reason": "..."},
            ...
        },
        "status": "Open" | "Closing Soon" | ...
    }
    """
    components = {
        "field_match": _field_score(student_profile, opportunity),
        "skill_match": _skill_score(student_profile, opportunity),
        "education_level_match": _education_level_score(student_profile, opportunity),
        "location_eligibility": _location_score(student_profile, opportunity),
        "category_preference": _category_score(student_profile, opportunity),
    }

    total = sum(score for score, _ in components.values())

    if total >= 65:
        match_level = "High"
    elif total >= 35:
        match_level = "Medium"
    else:
        match_level = "Low"

    return {
        "opportunity_id": opportunity["id"],
        "total_score": round(total, 1),
        "match_level": match_level,
        "components": {
            key: {"score": round(score, 1), "max": WEIGHTS[key], "reason": reason}
            for key, (score, reason) in components.items()
        },
        "status": compute_status(opportunity),
                "eligibility": check_eligibility(
                student_profile,
                opportunity,
        ),
    }


def rank_opportunities(student_profile: dict, opportunities: list[dict], min_score: float = 0.0) -> list[dict]:
    """
    Score every opportunity and return them sorted best-first, each paired
    with its score breakdown as {"opportunity": ..., "score": ...}.
    Closed opportunities are still scored (a student might want to see it
    for next year) but sink slightly via a small penalty, applied AFTER
    the transparent score so it doesn't muddy the score breakdown itself.
    """
    scored = []
    for opp in opportunities:
        result = score_opportunity(student_profile, opp)
        if result["total_score"] < min_score:
            continue
        sort_key = result["total_score"] - (15 if result["status"] == "Closed" else 0)
        scored.append({"opportunity": opp, "score": result, "_sort_key": sort_key})

    scored.sort(key=lambda x: x["_sort_key"], reverse=True)
    for item in scored:
        item.pop("_sort_key", None)
    return scored
