"""
helpers.py

Small formatting and date/status utilities shared across pages.

The most important function here is `compute_status`: it is the single
source of truth for whether an opportunity is shown as Open, Closing Soon,
Closed, Date Uncertain, or Verification Needed. Centralizing this logic
means every page (Discover, Details, Saved, Recommendations) agrees on
what "open" means, and we never accidentally claim something is open
just because we haven't checked.
"""

from __future__ import annotations
from datetime import date, datetime, timedelta
from typing import Optional

CLOSING_SOON_WINDOW_DAYS = 14

STATUS_STYLES = {
    "Open": {"color": "#1a7f37", "bg": "#e6f4ea", "icon": "\U0001F7E2"},
    "Closing Soon": {"color": "#9a5b00", "bg": "#fff4e0", "icon": "\U0001F7E1"},
    "Closed": {"color": "#8b1f1f", "bg": "#fbe9e9", "icon": "\U0001F534"},
    "Date Uncertain": {"color": "#4b4b4b", "bg": "#eeeeee", "icon": "\u26AA"},
    "Verification Needed": {"color": "#5b3fa0", "bg": "#f0ecfb", "icon": "\U0001F7E3"},
}


def parse_iso_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def compute_status(opportunity: dict, today: Optional[date] = None) -> str:
    """
    Determine the display status of an opportunity.

    Rules (in priority order):
    1. If verification_status flags a problem -> "Verification Needed".
    2. If there is no deadline at all -> "Date Uncertain" UNLESS the
       deadline_note explicitly says it's rolling/always-open, in which
       case -> "Open".
    3. If deadline has passed -> "Closed".
    4. If deadline is within the closing-soon window -> "Closing Soon".
    5. Otherwise -> "Open".

    We never default to "Open" just because information is missing --
    that's the whole point of this function.
    """
    today = today or date.today()

    verification = (opportunity.get("verification_status") or "").lower()
    if "needs verification" in verification or "unverified" in verification:
        return "Verification Needed"

    deadline = parse_iso_date(opportunity.get("deadline"))

    if deadline is None:
        note = (opportunity.get("deadline_note") or "").lower()
        if "rolling" in note or "always open" in note or "no application deadline" in note:
            return "Open"
        return "Date Uncertain"

    if deadline < today:
        return "Closed"

    if deadline - today <= timedelta(days=CLOSING_SOON_WINDOW_DAYS):
        return "Closing Soon"

    return "Open"


def days_until(deadline_str: Optional[str], today: Optional[date] = None) -> Optional[int]:
    d = parse_iso_date(deadline_str)
    if d is None:
        return None
    today = today or date.today()
    return (d - today).days


def format_deadline(opportunity: dict, today: Optional[date] = None) -> str:
    """Human-readable deadline string used on cards and detail pages."""
    deadline = opportunity.get("deadline")
    if deadline is None:
        note = opportunity.get("deadline_note")
        return note if note else "Not specified"

    d = parse_iso_date(deadline)
    if d is None:
        return "Not specified"

    remaining = days_until(deadline, today)
    formatted = d.strftime("%B %d, %Y")

    if remaining is None:
        return formatted
    if remaining < 0:
        return f"{formatted} (closed)"
    if remaining == 0:
        return f"{formatted} (today)"
    return f"{formatted} ({remaining} day{'s' if remaining != 1 else ''} left)"


def status_badge_markdown(status: str) -> str:
    """Return a small HTML badge for a status, for use with st.markdown(..., unsafe_allow_html=True)."""
    style = STATUS_STYLES.get(status, STATUS_STYLES["Date Uncertain"])
    return (
        f'<span style="background-color:{style["bg"]}; color:{style["color"]}; '
        f'padding:2px 10px; border-radius:12px; font-size:0.8rem; font-weight:600;">'
        f'{style["icon"]} {status}</span>'
    )


def truncate(text: str, length: int = 160) -> str:
    if not text:
        return ""
    text = text.strip()
    if len(text) <= length:
        return text
    return text[:length].rsplit(" ", 1)[0] + "\u2026"


def safe_join(items: Optional[list], sep: str = ", ", empty: str = "Not specified") -> str:
    if not items:
        return empty
    return sep.join(str(i) for i in items)
