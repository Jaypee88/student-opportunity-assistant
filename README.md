# Student Opportunity Assistant

An AI-assisted platform that helps university students **discover, understand, evaluate, and prepare for** opportunities — including internships, scholarships, fellowships, hackathons, competitions, grants, research programs, conferences, training programs, and other student-development opportunities.

**Discover → Understand → Match → Evaluate → Prepare → Apply**

Built with **Streamlit**, with selectable **Google Gemini and Anthropic Claude** AI providers.

The core design principle is simple:

> **AI should reason over information, not invent it.**

The application separates opportunity data and deterministic application logic from AI reasoning. This makes the system more transparent, easier to evaluate, and safer for students relying on eligibility and deadline information.

---

## The problem

Students often spend significant time searching across different websites for opportunities and then trying to determine:

* Whether an opportunity is legitimate
* Whether they are eligible
* Whether the deadline is still active
* What documents are required
* What the organization is actually looking for
* Whether the opportunity is relevant to their field, skills, and academic level
* How to prepare a strong application

Generic AI chatbots can make this harder when they generate plausible-sounding but unsupported opportunities, deadlines, eligibility requirements, or application links.

The goal of this project is therefore not simply to put a chatbot in front of students.

It is to combine **structured opportunity data, deterministic matching logic, and AI reasoning** in a way that keeps the boundaries between facts and AI-generated explanations clear.

---

## The solution

The application follows a layered approach:

```text
SOURCE
   ↓
STRUCTURED OPPORTUNITY DATA
   ↓
RULE-BASED ELIGIBILITY & MATCHING
   ↓
GEMINI OR CLAUDE REASONING / EXPLANATION
   ↓
STUDENT
```

Not:

```text
Internet
   ↓
AI guesses
   ↓
Student
```

The current dataset is intentionally small because the project is still in its **testing/prototype phase**.

The current opportunities are manually curated and researched from authoritative sources. Each record can contain information such as:

* Official application URL
* Eligibility information
* Deadline
* Location
* Skills
* Fields
* Education level
* Country eligibility
* Funding information
* Source information
* Verification date
* Verification status

The long-term goal is to expand this into a much larger and continuously maintained opportunity dataset without changing the core application architecture.

---

# Key features

## Discover Opportunities

Students can search and filter the curated opportunity dataset using:

* Opportunity category
* Location
* Field
* Skills
* Education level
* Deadline/status
* Other supported filters

Natural-language search can also be interpreted by the configured AI provider and converted into structured search criteria.

Claude does **not** return invented opportunities.

---

## Opportunity Details

Each opportunity has a dedicated detail view containing the available information, including:

* Description
* Eligibility
* Deadline
* Location
* Skills
* Education level
* Official application page
* Source information
* Verification status

Students are directed to the official application page rather than an AI-generated or unofficial application link.

---

## My Profile

Students can create a profile containing information that can be used for personalization.

Current profile information includes:

* Field of study
* Academic level
* CGPA
* Country/location
* Remote/on-site preference
* Fields of interest
* Skills
* Preferred opportunity types

The profile is currently stored in Streamlit session state as an MVP approach. Persistent accounts and cross-device profile storage are future improvements.

---

## My Recommendations

Recommendations use a **transparent, rule-based matching system**.

The system evaluates factors such as:

* Field of study
* Skills
* Academic level
* Location
* Opportunity category

The result produces a match score and an explanation of how the score was obtained.

Students can either:

### Use My Profile

Use their saved student profile to generate personalized recommendations.

### Customize This Search

Create a temporary recommendation profile for a specific search without changing their saved profile.

This separation allows another student, or the same student with different goals, to explore opportunities without overwriting their permanent profile.

### Eligibility vs. Match

The application intentionally separates **match score** from **eligibility**.

A student can have a high match score while still failing a specific eligibility requirement.

For example:

```text
Match score: 82/100

Eligibility:
❌ Not eligible

Reason:
Required CGPA: 3.5
Student CGPA: 3.2
```

Eligibility checks are handled deterministically by application code rather than delegated entirely to an AI model.

This helps prevent an AI model from incorrectly deciding that a student qualifies for an opportunity.

---

## Analyze an Opportunity

Students can paste an opportunity description or eligibility text and receive a structured analysis.

The analysis can include:

* Overview
* Eligibility
* Deadline
* Requirements
* Documents needed
* What the organization appears to be looking for
* Important details
* Potential concerns
* Fit for the student
* Action checklist

The system is instructed to distinguish between information explicitly provided in the text and reasonable observations.

When information is missing, it should report that the information was not specified rather than inventing an answer.

Students can optionally use their saved profile to receive a more personalized fit and eligibility assessment.

---

## Opportunity Assistant

The Opportunity Assistant provides multi-turn conversational assistance around an opportunity.

The assistant can help students understand:

* Eligibility
* Requirements
* Deadlines
* Application expectations
* Opportunity details
* Questions about how the opportunity relates to their profile

The assistant is grounded in the opportunity information supplied to it rather than being treated as an unrestricted source of opportunity facts.

---

## Application Helper

The Application Helper acts as an **application coach rather than a ghostwriter**.

It helps students:

* Understand application questions
* Identify relevant personal experiences
* Structure their responses
* Improve clarity
* Reflect on their actual achievements
* Develop stronger application narratives

The system is designed not to fabricate achievements, experiences, or qualifications on behalf of the student.

---

## Saved Opportunities

Students can save opportunities they are interested in and view them later.

The application also provides deadline-aware status information to help students distinguish between opportunities that are:

* Open
* Closing Soon
* Closed
* Date Uncertain
* Verification Needed

Deadline status is calculated deterministically rather than inferred by Claude.

---

# AI providers

**Students can choose Gemini or Claude for supported AI-assisted workflows. Gemini is the default for the Opportunity Assistant; Claude is optional and requires an Anthropic API key.**

Claude API calls are centralized through:

```text
services/claude_service.py
```

System prompts are centralized through:

```text
utils/claude_prompts.py
```

This makes the AI behavior easier to review, maintain, and improve.

| Feature               | Claude's role                                        | What Claude is NOT responsible for                 |
| --------------------- | ---------------------------------------------------- | -------------------------------------------------- |
| Smart search          | Interpret natural-language search intent             | Invent or return opportunities                     |
| Opportunity analysis  | Structure and explain pasted opportunity information | Invent missing eligibility or deadline information |
| Opportunity Assistant | Answer grounded follow-up questions                  | Act as an unrestricted opportunity database        |
| Recommendations       | Explain deterministic matching results               | Calculate the match score                          |
| Application Helper    | Coach the student through their own experiences      | Fabricate achievements or qualifications           |

The project uses the Anthropic **Messages API** for Claude-powered features, including structured analysis and multi-turn conversations.

---

# Development and Gemini testing

During development, **Gemini was temporarily integrated as a testing provider**.

This was primarily because Anthropic API credits were not available during development.

Gemini allowed the application structure and AI-assisted workflows to be tested without blocking development.

Gemini is **not the core product direction**.

The intended architecture and application story remain **Claude-first**, with Claude serving as the primary AI provider.

The AI service layer is structured so that providers can be tested independently without changing the application's main UI and business logic.

---

# Architecture

```text
Student
   │
   ├── Search
   ├── Profile
   ├── Pasted opportunity
   └── Application question
          │
          ▼
┌─────────────────────────────┐
│       Streamlit UI          │
│ pages / forms / navigation  │
└──────────────┬──────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
Opportunity Data     Student Profile
       │                │
       └───────┬────────┘
               ▼
┌─────────────────────────────┐
│ Rule-based application      │
│ logic                       │
│                             │
│ • Eligibility checks        │
│ • Match scoring             │
│ • Deadline/status logic     │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│       Claude Service        │
│                             │
│ • Analysis                 │
│ • Explanation              │
│ • Search interpretation    │
│ • Conversational support   │
│ • Application coaching     │
└──────────────┬──────────────┘
               │
               ▼
            Student
```

The architectural principle is:

> **Application code determines structured facts and calculations; Claude explains, interprets, and assists.**

---

# Project structure

```text
student-opportunity-assistant/
│
├── app.py
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
│
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example
│
├── data/
│   └── opportunities.json
│
├── services/
│   ├── __init__.py
│   ├── claude_service.py
│   ├── gemini_service.py
│   ├── opportunity_service.py
│   └── recommendation_service.py
│
├── utils/
│   ├── __init__.py
│   ├── validators.py
│   ├── helpers.py
│   ├── claude_prompts.py
│   └── ui_components.py
│
└── app_pages/
    ├── __init__.py
    ├── home.py
    ├── discover.py
    ├── analyze.py
    ├── profile.py
    ├── recommendations.py
    ├── assistant.py
    ├── application_helper.py
    ├── saved.py
    └── about.py
```

---

# Recommendation architecture

The recommendation system is intentionally deterministic.

```text
Student Profile
       ↓
Opportunity
       ↓
Field matching
       ↓
Skill matching
       ↓
Academic-level matching
       ↓
Location matching
       ↓
Category matching
       ↓
Match Score
       ↓
Eligibility Checks
       ↓
Claude explanation
```

This makes the system more transparent than asking an LLM to produce an arbitrary percentage.

The user can inspect why a recommendation received its score.

---

# Data schema

Each opportunity follows a structured schema similar to:

```json
{
  "id": "opp_001",
  "title": "...",
  "organization": "...",
  "category": "Internship",
  "description": "...",
  "eligibility": "...",
  "location": "...",
  "remote_status": "Remote",
  "deadline": "YYYY-MM-DD",
  "deadline_note": "...",
  "application_url": "https://...",
  "official_source": "...",
  "source_url": "https://...",
  "skills": ["Python", "Machine Learning"],
  "fields": ["Computer Science", "Engineering"],
  "education_level": ["Undergraduate"],
  "country_eligibility": ["Nigeria"],
  "funding": "...",
  "date_added": "YYYY-MM-DD",
  "last_verified": "YYYY-MM-DD",
  "verification_status": "Verified against official source"
}
```

Where available, records can also contain structured eligibility information such as:

```json
{
  "minimum_cgpa": 3.5
}
```

and:

```json
{
  "eligible_levels": [300, 400]
}
```

These structured fields allow the application to perform deterministic eligibility checks rather than relying entirely on AI interpretation.

---

# Data sourcing and verification

The current dataset is intentionally a **small seed/testing dataset**.

It is not intended to represent a comprehensive listing of all available student opportunities.

The current phase is focused on validating:

* The application architecture
* Search and filtering
* Opportunity analysis
* Profile-based personalization
* Recommendation scoring
* Eligibility logic
* Claude integration
* Conversational assistance
* Application coaching
* Deadline/status handling

The opportunities currently included in the dataset were researched from authoritative sources and include source and verification information where available.

The application is designed so that the dataset can grow substantially in future development.

### Planned data expansion

A future version can introduce a significantly larger dataset and an automated or semi-automated ingestion pipeline:

```text
Discover
   ↓
Collect
   ↓
Normalize
   ↓
Deduplicate
   ↓
Validate
   ↓
Verify official source
   ↓
Store
   ↓
Flag stale/expired records
```

The existing service architecture is intended to allow this larger data pipeline to be introduced without requiring a complete rewrite of the application UI.

---

# Setup — run locally

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd student-opportunity-assistant
```

### 2. Create a virtual environment

Windows:

```bash
py -m venv venv
venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy:

```text
.env.example
```

to:

```text
.env
```

Then add your API keys.

```env
ANTHROPIC_API_KEY=your_anthropic_key
GEMINI_API_KEY=your_gemini_key
```

Gemini is the default chat provider and requires GEMINI_API_KEY. Claude is optional and requires ANTHROPIC_API_KEY.

**Never commit `.env` or API keys to GitHub.**

### 5. Run the application

```bash
streamlit run app.py
```

The application will normally open at:

```text
http://localhost:8501
```

---

# Streamlit deployment

The application can be deployed through Streamlit Community Cloud using the GitHub repository.

The main entry point is:

```text
app.py
```

After deployment, API keys should be stored in Streamlit Secrets rather than committed to the repository.

Example:

```toml
ANTHROPIC_API_KEY = "your-real-anthropic-key"
```

If Gemini testing is required:

```toml
GEMINI_API_KEY = "your-real-gemini-key"
```

---

# Security

API keys are loaded through environment variables locally and Streamlit Secrets in deployment.

The following files must never be committed:

```text
.env
.streamlit/secrets.toml
```

They are excluded through `.gitignore`.

---

# Current project status

This project is currently in an **active prototype/testing phase**.

The current implementation is focused on validating the core experience and architecture rather than providing a production-scale opportunity database.

The current priorities are:

* Validate the user experience
* Test Claude-powered workflows
* Validate recommendation and eligibility logic
* Test profile personalization
* Gather feedback
* Expand the opportunity dataset
* Improve verification and data ingestion
* Prepare the application for broader student use

---

# Limitations

* The current opportunity dataset is intentionally small.
* It is not a live or comprehensive opportunity database.
* Opportunity information can change after verification.
* Students should always confirm important requirements and deadlines on the official opportunity page.
* Match scores are heuristic indicators and are not guarantees of eligibility or acceptance.
* Some eligibility information may be unavailable if it is not structured in the dataset.
* AI responses depend on the information provided to the model.
* Profile persistence is currently session-based rather than account-based.

---

# Future development

Planned improvements include:

* Significantly expanding the opportunity dataset
* Automated/semi-automated opportunity ingestion
* Better deduplication and source verification
* Scheduled deadline and source re-verification
* More detailed eligibility rules
* More precise academic-level matching
* SQLite/PostgreSQL for larger datasets
* User accounts and persistent profiles
* Persistent saved opportunities across devices
* Better recommendation personalization
* Improved opportunity freshness monitoring
* Additional application-preparation workflows

The long-term goal is to evolve the current prototype into a reliable student opportunity discovery and preparation platform with a much larger, continuously maintained opportunity dataset.

---

# GitHub setup

```bash
git init
git add .
git commit -m "Initial Student Opportunity Assistant implementation"
git branch -M main
git remote add origin https://github.com/<your-username>/student-opportunity-assistant.git
git push -u origin main
```

Before pushing, verify:

```bash
git status
```

and make sure `.env` and `.streamlit/secrets.toml` are not listed as files to commit.

---

# Final demo-readiness checklist

* [ ] `ANTHROPIC_API_KEY` configured locally or in Streamlit Secrets
* [ ] Application starts without errors
* [ ] Home page loads
* [ ] Discover Opportunities works
* [ ] Opportunity details work
* [ ] Official application links work
* [ ] Save/unsave functionality works
* [ ] My Profile saves student information
* [ ] CGPA is stored in the profile
* [ ] Recommendations work using the saved profile
* [ ] Custom recommendation search works without changing the saved profile
* [ ] Match score breakdown is visible
* [ ] Eligibility checks are displayed separately from match score
* [ ] Analyze an Opportunity returns a structured breakdown
* [ ] Analyze can use the saved profile
* [ ] Opportunity Assistant maintains conversation context
* [ ] Application Helper coaches rather than fabricates experiences
* [ ] Claude-powered features work when ANTHROPIC_API_KEY is configured
* [ ] Gemini chat and analysis work when GEMINI_API_KEY is configured
* [ ] Saved Opportunities works
* [ ] Deadline status logic works
* [ ] `.env` is excluded from Git
* [ ] `.streamlit/secrets.toml` is excluded from Git
* [ ] GitHub repository is public and clean
* [ ] Streamlit deployment works
* [ ] Deployed application works end-to-end
