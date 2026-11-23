"""Live web research for current student opportunities.

Search results are treated as leads, not verified facts. The assistant must
distinguish official sources from third-party listings and never call an
opportunity open unless a current official source supports that status.
"""
from __future__ import annotations

from datetime import date
from urllib.parse import urlparse


def search_opportunities(query: str, profile: dict | None = None, max_results: int = 7) -> list[dict]:
    """Search the public web using DDGS. Returns normalized, source-linked results."""
    try:
        from ddgs import DDGS
    except ImportError as exc:
        raise RuntimeError("Live research is not installed. Install the ddgs dependency.") from exc

    profile = profile or {}
    context_terms = []
    if profile.get("country"):
        context_terms.append(str(profile["country"]))
    if profile.get("field_of_study"):
        context_terms.append(str(profile["field_of_study"]))
    if profile.get("academic_level"):
        context_terms.append(f"{profile['academic_level']} level undergraduate")
    if not context_terms:
        context_terms.append("undergraduate students Nigeria")

    search_query = f"{query} {' '.join(context_terms)} current 2026 official application deadline eligibility"
    raw_results = DDGS(timeout=12).text(
        search_query,
        region="wt-wt",
        safesearch="moderate",
        max_results=max_results,
    )

    normalized = []
    seen = set()
    extractor = DDGS(timeout=12)
    for item in raw_results or []:
        url = (item.get("href") or item.get("url") or "").strip()
        if not url.startswith(("http://", "https://")) or url in seen:
            continue
        seen.add(url)
        domain = urlparse(url).netloc.lower().removeprefix("www.")
        page_excerpt = ""
        try:
            extracted = extractor.extract(url, fmt="text_plain")
            page_excerpt = (extracted.get("content") or "")[:5000]
        except Exception:
            # Search snippets remain useful when a publisher blocks page extraction.
            pass
        normalized.append({
            "title": (item.get("title") or "Untitled result").strip(),
            "url": url,
            "domain": domain,
            "snippet": (item.get("body") or item.get("description") or "").strip(),
            "page_excerpt": page_excerpt,
            "source_type": "Potential official source — confirm ownership" if any(
                token in domain for token in (".gov", ".edu", "dangote", "foundation", "un.org")
            ) else "Third-party / verify",
        })
    return normalized


def is_opportunity_discovery(message: str) -> bool:
    """Detect requests that need current opportunity research."""
    text = (message or "").lower()
    terms = (
        "opportunit", "scholarship", "internship", "fellowship", "grant",
        "hackathon", "competition", "currently open", "still open", "deadline",
        "application open", "can i apply", "program accepting", "recruitment",
        "graduate trainee", "dangote", "google summer", "fully funded",
    )
    return any(term in text for term in terms)


def is_simple_greeting(message: str) -> bool:
    normalized = " ".join((message or "").lower().strip(" .,!?").split())
    return normalized in {
        "hi", "hello", "hey", "good morning", "good afternoon",
        "good evening", "how are you", "how are you doing",
    }
