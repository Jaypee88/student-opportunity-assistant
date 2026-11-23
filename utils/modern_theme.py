"""Modern visual polish shared across the Streamlit application."""

import streamlit as st


MODERN_CSS = """
<style>
:root {
  --brand: #635bdb;
  --brand-deep: #4b43bd;
  --ink: #182033;
  --muted: #68738a;
  --line: #e7eaf2;
  --surface: #ffffff;
  --canvas: #f7f8fc;
}
html, body, [class*="css"] {
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
}
.stApp { background: var(--canvas); color: var(--ink); }
[data-testid="stHeader"] { background: rgba(247,248,252,.88); }
.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1240px; }
h1, h2, h3 { color: var(--ink); letter-spacing: -.035em; font-weight: 750; }
h1 { font-size: clamp(2rem, 4vw, 2.8rem); }
h2 { font-size: 1.7rem; }
p, label, .stCaption { color: var(--muted); }
[data-testid="stSidebar"] {
  background: #171d35;
  border-right: 1px solid rgba(255,255,255,.08);
}
[data-testid="stSidebar"] * { color: #edf0ff; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #b8c0dc; }
[data-testid="stSidebar"] [role="radiogroup"] label { padding: .35rem .45rem; border-radius: 9px; }
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: rgba(255,255,255,.08); }
.stButton > button, .stLinkButton > a {
  border-radius: 10px; font-weight: 650; min-height: 2.55rem;
  border: 1px solid var(--line); transition: all .18s ease;
}
.stButton > button[kind="primary"] {
  background: var(--brand); border-color: var(--brand); color: #fff;
}
.stButton > button[kind="primary"]:hover {
  background: var(--brand-deep); border-color: var(--brand-deep);
  box-shadow: 0 5px 16px rgba(99,91,219,.22);
}
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
  border-radius: 10px;
}
[data-testid="stMetric"] {
  background: var(--surface); border: 1px solid var(--line);
  padding: 1rem 1.1rem; border-radius: 15px;
  box-shadow: 0 4px 18px rgba(28,39,72,.035);
}
[data-testid="stMetricValue"] { color: var(--ink); font-weight: 750; }
[data-testid="stExpander"] {
  border: 1px solid var(--line); border-radius: 13px; background: var(--surface);
}
.opp-card {
  border: 1px solid var(--line); border-radius: 15px; background: #fff;
  padding: 1.2rem 1.35rem; box-shadow: 0 5px 20px rgba(28,39,72,.035);
  transition: transform .18s ease, box-shadow .18s ease;
}
.opp-card:hover { transform: translateY(-2px); box-shadow: 0 10px 26px rgba(28,39,72,.08); }
.opp-title { color: var(--ink); font-size: 1.08rem; font-weight: 750; }
.opp-org, .opp-meta, .muted { color: var(--muted); }
.opp-tag { background: #f0efff; color: #5048bd; border-radius: 999px; padding: 3px 10px; }
.section-label { color: var(--ink); font-weight: 750; }
.verify-banner { background: #f4f1ff; border-left: 4px solid var(--brand); border-radius: 9px; padding: .7rem 1rem; }
[data-testid="stChatMessage"] {
  border: 1px solid var(--line); border-radius: 16px;
  padding: .8rem 1rem; background: #fff; margin-bottom: .65rem;
}
[data-testid="stChatInput"] {
  border-radius: 16px; border: 1px solid #dfe3ef;
  box-shadow: 0 8px 28px rgba(28,39,72,.07);
}
hr { border-color: var(--line); }
@media (max-width: 760px) {
  .block-container { padding: 1.1rem 1rem 2rem; }
}
</style>
"""


def inject_modern_theme() -> None:
    st.markdown(MODERN_CSS, unsafe_allow_html=True)
