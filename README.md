# Student Opportunity Assistant

An AI-assisted platform that helps university students **discover, understand,
evaluate, and prepare for** opportunities — internships, scholarships,
fellowships, hackathons, competitions, grants, research programs, conferences,
and other legitimate student-development programs.

**Discover → Filter → Understand → Match → Prepare → Apply**

Built with Streamlit and the Claude API. The distinctive design decision:
**Claude never invents opportunities.** It reasons only over a curated,
verified dataset and text the student pastes themselves.

---

## The problem

Students spend hours across scattered aggregator sites trying to figure out
whether an opportunity is legitimate, whether they're eligible, what a
deadline actually means, and what an application is really asking for — often
without a reliable way to prepare.

Generic chatbots make this worse: asked to "list AI internships," a language
model will happily produce plausible-sounding but sometimes fictional
programs, deadlines, and links.

## The solution

A three-layer architecture that keeps AI reasoning separate from data truth:

```
SOURCE  →  VERIFIED OPPORTUNITY DATA  →  CLAUDE  →  STUDENT
```

*not*

```
Internet  →  Claude guesses  →  Student
```

Every opportunity in `data/opportunities.json` was researched from its
official organization page (or cross-checked against it), and stores
`official_source`, `application_url`, and `last_verified`. Claude is used
purely as the **reasoning/language layer** on top of that data — never as the
source of the data itself.

## Key features

- **Discover Opportunities** — natural-language + filtered search over the
  verified database
- **Opportunity Details** — full record with official application link and
  verification date
- **Analyze an Opportunity** — paste any listing/eligibility text and get a
  structured breakdown (overview, eligibility, deadline, requirements,
  documents, concerns, fit, action checklist) — with explicit
  *"Not specified in the provided information"* instead of guesses
- **My Recommendations** — a **transparent, rule-based** match score (field,
  skill, academic level, location, category), with Claude only explaining the
  score in plain language, never computing it
- **Opportunity Assistant** — multi-turn Q&A grounded in one specific,
  verified opportunity record (uses the Claude Messages API's native
  multi-turn support)
- **Application Helper** — an application *coach*, not a ghostwriter: it
  helps you understand the prompt and structure your own real experiences,
  and refuses to fabricate achievements
- **Saved Opportunities** — with an upcoming-deadlines view
- **Deadline-aware status logic** — Open / Closing Soon / Closed / Date
  Uncertain / Verification Needed, computed deterministically so the app
  never claims something is open just because information is missing

## Built with Claude

Every feature that touches Claude lives behind a single module,
`services/claude_service.py`, and every system prompt lives in
`utils/claude_prompts.py` so the "don't invent information" instruction is
consistent and reviewable in one place.

| Feature | Claude's job | Explicitly NOT Claude's job |
|---|---|---|
| Smart search | Suggest keywords/categories from a natural-language query | Return or invent opportunities itself |
| Analyze an Opportunity | Structure pasted text into a clear breakdown | Fill in missing eligibility/deadline details |
| Opportunity Assistant | Answer follow-ups grounded in one verified record | Answer beyond what the record + profile state |
| Recommendations | Explain a match in plain language | Compute the match score (that's rule-based) |
| Application Helper | Coach structure, refine the student's own words | Fabricate achievements or write generic answers |

Uses the Anthropic **Messages API** (`claude-sonnet-4-6`) for both single-turn
calls (analysis, search interpretation, recommendation explanations) and
multi-turn conversations (Opportunity Assistant, Application Helper), with
structured JSON output for anything the UI needs to parse reliably.

## Architecture

```
Student Input (search / profile / pasted text)
        │
        ▼
┌─────────────────────────┐
│   Streamlit UI (pages)   │  navigation, forms, cards, session state
└───────────┬───────────────┘
            │
┌───────────▼───────────────┐
│  opportunity_service.py    │  load / validate / search / filter / sort JSON
│  recommendation_service.py │  transparent rule-based scoring
└───────────┬───────────────┘
            │ (structured data only — never free text)
┌───────────▼───────────────┐
│    claude_service.py       │  the ONLY module calling the Anthropic API
│  (Messages API, JSON mode) │
└───────────┬───────────────┘
            │
        Anthropic API
```

## Project structure

```
student-opportunity-assistant/
│
├── app.py                       # Entry point: config, session state, nav, routing
├── requirements.txt
├── README.md
├── .gitignore
├── .env.example
├── .streamlit/
│   ├── config.toml              # Theme
│   └── secrets.toml.example     # Template for Streamlit Cloud secrets
│
├── data/
│   └── opportunities.json       # Curated, verified opportunity dataset
│
├── services/
│   ├── claude_service.py        # All Anthropic API calls
│   ├── opportunity_service.py   # Data loading/search/filter/sort (no AI)
│   └── recommendation_service.py# Deterministic match scoring (no AI)
│
├── utils/
│   ├── validators.py            # Schema validation for opportunity records
│   ├── helpers.py                # Date/status logic, formatting
│   ├── claude_prompts.py         # All system prompts, as reviewable data
│   └── ui_components.py          # Shared cards / detail view / CSS
│
└── app_pages/                    # (named app_pages, not "pages", to avoid
    ├── home.py                   #  colliding with Streamlit's automatic
    ├── discover.py                #  pages/ multipage detection)
    ├── analyze.py
    ├── recommendations.py
    ├── assistant.py
    ├── application_helper.py
    ├── saved.py
    └── about.py
```

## Data schema

Each opportunity in `data/opportunities.json` follows this shape:

```json
{
  "id": "opp_001",
  "title": "...",
  "organization": "...",
  "category": "Internship | Scholarship | Fellowship | Hackathon | Competition | Grant | Research | Conference | Volunteer | AI/Tech Program | Other",
  "description": "...",
  "eligibility": "...",
  "location": "...",
  "remote_status": "Remote | On-site | Hybrid",
  "deadline": "YYYY-MM-DD or null",
  "deadline_note": "human-readable clarification, especially when deadline is null",
  "application_url": "https://... (the official application page)",
  "official_source": "Name of the authoritative organization/page",
  "source_url": "Where the record was discovered/verified",
  "skills": ["..."],
  "fields": ["..."],
  "education_level": ["Undergraduate", "Graduate", "..."],
  "country_eligibility": ["..."],
  "funding": "...",
  "date_added": "YYYY-MM-DD",
  "last_verified": "YYYY-MM-DD",
  "verification_status": "Verified against official source | Needs verification — ..."
}
```

`utils/validators.py` enforces this shape at load time; a malformed record is
dropped (with the rest of the app still working) rather than crashing the
page for every student.

## Data sourcing & verification approach

Discovery source and authoritative source are treated as different things.
The current seed dataset (6 opportunities) was researched directly from
official pages (`spaceappschallenge.org`, `schwarzmanscholars.org`,
`summerofcode.withgoogle.com`, `ieeextreme.org`, `theforage.com`, and a
university's official Mastercard Foundation Scholars Program page) as of
**September 10, 2026**. Two entries are intentionally shown as **Closed**
(their real deadlines have passed) and one as **Verification Needed** (because
third-party sources disagreed on its exact date) — this is deliberate: the
deadline-status logic is designed to never claim something is open just
because we haven't checked.

For a production version, `services/opportunity_service.py` is structured so
a future ingestion module could plug in the same validation/dedup pipeline
described in the project brief (discover → normalize → dedupe → validate →
preserve official URL → flag stale/expired listings) without changing any
page code.

## Setup — run locally

**1. Clone and enter the project**

```bash
git clone <your-repo-url>
cd student-opportunity-assistant
```

**2. Create a virtual environment (recommended)**

```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Set your API key**

```bash
cp .env.example .env
# then edit .env and paste your real key:
# ANTHROPIC_API_KEY=sk-ant-...
```

Get a key at <https://console.anthropic.com/settings/keys>. **Never** commit
`.env` — it's already in `.gitignore`.

**5. Run the app**

```bash
streamlit run app.py
```

It opens at `http://localhost:8501`. Pages without a key still work (browsing,
filtering, saving, the transparent score breakdown) — only the Claude-powered
features (Analyze, Assistant, Application Helper, smart search, recommendation
explanations) need the key, and they'll show a clear error if it's missing.

## Adding or verifying opportunities

Open `data/opportunities.json` and add an object to the `opportunities` array
following the schema above. Then check it's valid:

```bash
python3 -c "
from services.opportunity_service import load_opportunities
load_opportunities(strict=True)
print('Dataset is valid.')
"
```

This raises a clear error listing exactly which record/field is wrong if
something doesn't match the schema.

To re-verify an existing record, revisit its `application_url`, update any
changed fields, and bump `last_verified` to today's date.

## Testing the Claude features

With `ANTHROPIC_API_KEY` set:

1. **Analyze an Opportunity** — paste a paragraph like: *"The Example
   Foundation AI Fellowship is open to undergraduate students studying
   computer science. Applicants must submit a CV and a 500-word essay by
   December 1."* Confirm the structured output correctly reports the missing
   fields (e.g. funding, location) as *"Not specified in the provided
   information"* rather than inventing them.
2. **Opportunity Assistant** — pick any opportunity, ask *"Am I eligible?"*
   with no profile set, then set a profile on the Recommendations page and
   ask again — the answer should change to reference your profile.
3. **My Recommendations** — fill in the profile form, confirm the score
   breakdown bars sum sensibly, and click "Explain in plain English" on a
   couple of cards.
4. **Application Helper** — paste an essay prompt and confirm Claude asks
   about your real experiences before offering to draft anything.

## GitHub setup

```bash
git init
git add .
git commit -m "Initial commit: Student Opportunity Assistant"
git branch -M main
git remote add origin https://github.com/<your-username>/student-opportunity-assistant.git
git push -u origin main
```

Double-check `.env` and `.streamlit/secrets.toml` are **not** in `git status`
before your first push (they're git-ignored by default in this repo).

## Deploying on Streamlit Community Cloud

1. Push this repo to GitHub (above).
2. Go to <https://share.streamlit.io>, sign in, and click **"New app"**.
3. Select your repo, branch (`main`), and set the main file path to `app.py`.
4. Before/after deploying, open **"Manage app" → "Settings" → "Secrets"** and
   paste:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-your-real-key"
   ```
5. Deploy. The app reads the key via `st.secrets` in the cloud automatically
   (see `services/claude_service.py::_get_api_key`) — no code changes needed.

## Limitations

- The dataset is a small, manually curated starting set (6 opportunities) —
  not a live, comprehensive listing.
- Deadlines can change after `last_verified`; always confirm on the official
  page before relying on any date shown.
- The recommendation score is a transparent heuristic, not a guarantee of
  eligibility.
- Claude can only work with what it's given — if pasted text is ambiguous or
  incomplete, it will report the gap rather than fill it in, which is by
  design, but means the output is only as good as what you paste.

## Future improvements

- Move from JSON to SQLite/Postgres as the dataset grows
- A real ingestion pipeline (discover → normalize → dedupe → validate →
  preserve official URL → flag expired listings) plugged into
  `opportunity_service.py`
- Scheduled re-verification jobs updating `last_verified`
- Accounts so saved opportunities and profiles persist across devices/sessions

## Final demo-readiness checklist

- [ ] `ANTHROPIC_API_KEY` set in `.env` (local) or Streamlit secrets (deployed)
- [ ] `streamlit run app.py` boots with no errors
- [ ] Home page loads and all four CTA buttons navigate correctly
- [ ] Discover Opportunities returns results for a plain-language query
- [ ] A card's "View details" and "Save" both work
- [ ] Analyze an Opportunity returns a structured, non-fabricated breakdown
- [ ] Opportunity Assistant maintains context across at least 2 turns
- [ ] Recommendations page produces a saved profile and a ranked, explainable list
- [ ] Application Helper asks about real experiences before drafting anything
- [ ] Saved Opportunities shows upcoming deadlines correctly
- [ ] `.env` / `.streamlit/secrets.toml` are confirmed absent from `git status`
- [ ] Deployed Streamlit Cloud app works end-to-end with secrets configured
