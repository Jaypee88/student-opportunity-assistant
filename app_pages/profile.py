"""pages/profile.py — Persistent student profile for personalization."""

import streamlit as st


REMOTE_OPTIONS = [
    "No preference",
    "Remote",
    "On-site",
    "Hybrid",
]

OPPORTUNITY_TYPES = [
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
]


def render() -> None:
    st.markdown("## 👤 My Profile")
    st.caption(
        "Save your student information once. Your profile can then be used "
        "for personalized recommendations and opportunity analysis."
    )

    profile = st.session_state.student_profile

    with st.form("profile_form"):
        st.markdown("### Academic information")

        c1, c2, c3 = st.columns(3)

        with c1:
            field_of_study = st.text_input(
                "Field of study",
                value=profile.get("field_of_study", ""),
                placeholder="e.g. Computer Engineering",
            )

        with c2:
            academic_level = st.text_input(
                "Academic level",
                value=profile.get("academic_level", ""),
                placeholder="e.g. 300",
            )

        with c3:
            cgpa = st.number_input(
                "CGPA",
                min_value=0.0,
                max_value=5.0,
                value=float(profile.get("cgpa", 0.0)),
                step=0.01,
                format="%.2f",
                help="Use your institution's CGPA scale, e.g. 4.00/5.00.",
            )
        institution = st.text_input(
            "University / institution",
            value=profile.get("institution", ""),
            placeholder="e.g. Nnamdi Azikiwe University",
        )

        country = st.text_input(
            "Country / location",
            value=profile.get("country", ""),
            placeholder="e.g. Nigeria",
        )

        st.markdown("### Preferences")

        remote_pref = st.selectbox(
            "Remote / on-site preference",
            REMOTE_OPTIONS,
            index=(
                REMOTE_OPTIONS.index(profile.get("remote_preference"))
                if profile.get("remote_preference") in REMOTE_OPTIONS
                else 0
            ),
        )

        interests = st.text_input(
            "Interests / fields",
            value=", ".join(profile.get("fields_of_interest", [])),
            placeholder="AI/ML, software engineering, embedded systems",
        )

        skills = st.text_input(
            "Skills",
            value=", ".join(profile.get("skills", [])),
            placeholder="Python, Machine Learning, Arduino",
        )

        preferred_categories = st.multiselect(
            "Preferred opportunity types",
            OPPORTUNITY_TYPES,
            default=profile.get("preferred_categories", []),
        )

        submitted = st.form_submit_button(
            "Save profile",
            type="primary",
        )

        if submitted:
            st.session_state.student_profile = {
                "field_of_study": field_of_study.strip(),
                "academic_level": academic_level.strip(),
                "institution": institution.strip(),
                "country": country.strip(),
                "cgpa": cgpa,
                "remote_preference": remote_pref,
                "fields_of_interest": [
                    item.strip()
                    for item in interests.split(",")
                    if item.strip()
                ],
                "skills": [
                    item.strip()
                    for item in skills.split(",")
                    if item.strip()
                ],
                "preferred_categories": preferred_categories,
            }

            st.success("Profile saved successfully.")
            st.rerun()

    # Show a small summary when a profile already exists.
    if profile:
        st.markdown("---")
        st.markdown("### Current profile")

        col1, col2 = st.columns(2)

        with col1:
            st.write(
                f"**Field:** {profile.get('field_of_study') or 'Not set'}"
            )
            st.write(
                f"**Academic level:** "
                f"{profile.get('academic_level') or 'Not set'}"
            )
            st.write(
                f"**Institution:** {profile.get('institution') or 'Not set'}"
            )
            st.write(
                f"**Location:** {profile.get('country') or 'Not set'}"
            )

        with col2:
            st.write(
                f"**Interests:** "
                f"{', '.join(profile.get('fields_of_interest', [])) or 'Not set'}"
            )
            st.write(
                f"**Skills:** "
                f"{', '.join(profile.get('skills', [])) or 'Not set'}"
            )
            st.write(
                f"**Opportunity types:** "
                f"{', '.join(profile.get('preferred_categories', [])) or 'Not set'}"
            )

    def _extract_academic_year(level):
        """Extract a numeric academic level such as 100, 200, 300, 400."""

        level = str(level).lower()

        for year in [100, 200, 300, 400, 500]:
            if str(year) in level:
                return year

        return None