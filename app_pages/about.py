"""pages/about.py — Project purpose, methodology, and how Claude is used."""

import streamlit as st
from services.opportunity_service import load_opportunities


def render() -> None:
    st.markdown("## \u2139\uFE0F About this project")

    st.markdown(
        """
Student Opportunity Assistant helps university students **discover, understand,
evaluate, and prepare for** opportunities — internships, scholarships,
fellowships, hackathons, competitions, grants, research programs, conferences,
and other legitimate student-development programs.

The goal isn't to be another chatbot. It's to move a student through a real
journey:

**Discover \u2192 Filter \u2192 Understand \u2192 Match \u2192 Prepare \u2192 Apply**
        """
    )

    st.markdown("### Why a verified database, not AI-generated results")
    st.markdown(
        """
A language model asked to "list AI internships" will confidently produce
plausible-sounding but sometimes fictional programs, deadlines, and links.
That's unacceptable for something students rely on to make real decisions.

So this platform is built around three layers:

```
SOURCE  →  VERIFIED OPPORTUNITY DATA  →  AI REASONING  →  STUDENT
```

*not*

```
Internet  →  AI guesses  →  Student
```

Every opportunity in the database was researched from its official
organization page (or a reputable platform like Devpost/Forage, cross-checked
against the official page where possible) and stored with its
`official_source`, `application_url`, and `last_verified` date. The AI providers never
generate new opportunities — it only reasons over records that are already
in the database, or text the student pastes themselves.
        """
    )

    st.markdown("### What the AI providers actually do here")
    st.markdown(
        """
| Feature | What AI does | What AI does NOT do |
|---|---|---|
| Smart search | Suggests keywords/categories from a natural-language query | Invent or return opportunities directly |
| Analyze an Opportunity | Structures pasted text into a clear breakdown | Fill in missing eligibility/deadline details |
| Opportunity Assistant | Answers follow-up questions grounded in one verified record | Answer beyond what the record + profile state |
| Recommendations | Explains a match in plain language | Compute the match score itself (that's rule-based) |
| Application Helper | Coaches structure and helps refine the student's own words | Fabricate achievements, awards, or experiences |

Every AI-facing prompt in this app includes an explicit instruction not to
invent information, and to say **"Not specified in the provided information"**
when something is missing, rather than guessing.
        """
    )

    st.markdown("### Architecture")
    st.markdown(
        """
- **Streamlit** — UI, navigation, session state, forms
- **`services/opportunity_service.py`** — loads, validates, searches, filters,
  and sorts the JSON dataset (no AI involved)
- **`services/recommendation_service.py`** — transparent, rule-based scoring
  (field / skill / education level / location / category match)
- **`services/claude_service.py`** — Anthropic API integration for Claude-powered workflows
- **`services/gemini_service.py`** — Google Gemini integration for analysis and interpretation
- **`services/chat_provider_service.py`** — routes Opportunity Assistant conversations to the selected provider
- **`utils/claude_prompts.py`** — Claude system prompts, kept separate for review
        """
    )

    opps = load_opportunities()
    st.markdown("### Current dataset")
    st.caption(
        f"{len(opps)} opportunities, each verified against an official or reputable source "
        f"as of the dates recorded in their `last_verified` field. This is a curated starting "
        f"set for a focused, trustworthy demo — not an exhaustive listing."
    )

    with st.expander("Limitations, honestly"):
        st.markdown(
            """
- The dataset is intentionally small and manually curated — it is **not** a
  live-scraped, comprehensive listing of every opportunity in existence.
- Deadlines can change after `last_verified`. Always confirm on the official
  application page before relying on any date shown here.
- The recommendation score is a simple, transparent heuristic — it is a
  starting point for exploration, not a guarantee of eligibility or a
  substitute for reading the official requirements.
- AI-generated explanations can still contain mistakes when interpreting pasted text (e.g. if the
  text itself is ambiguous or incomplete) — it reports what's missing, but it
  can't recover information that was never given to it.
            """
        )

    with st.expander("Future improvements"):
        st.markdown(
            """
- Move from JSON to SQLite/Postgres for a larger dataset
- A data-ingestion pipeline: discover → normalize → dedupe → validate →
  preserve official URL → flag expired listings
- Scheduled re-verification of `last_verified` dates
- Accounts so saved opportunities persist across devices
            """
        )
