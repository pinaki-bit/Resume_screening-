"""
frontend/pages/candidate_profile.py

Candidate profile page.
"""

from __future__ import annotations

import streamlit as st
from services.api_client import APIError, get_resume


def render_candidate_profile():
    resume_id = st.session_state.get("selected_resume_id")
    if not resume_id:
        st.info("No resume selected. Go to Screening Results and open a candidate.")
        return

    st.title("👤 Candidate Profile")

    try:
        resume = get_resume(resume_id)
    except APIError as e:
        st.error(f"Failed to load resume: {e.detail}")
        return

    # Header
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Predicted Domain", resume.get("predicted_domain") or "Unknown")
    with col2:
        st.metric("Confidence", (resume.get("prediction_confidence") or "N/A").capitalize())
    with col3:
        st.metric("Status", resume.get("status", "unknown").capitalize())

    st.divider()

    # Extracted skills
    skills = resume.get("extracted_skills", [])
    st.subheader(f"🔧 {len(skills)} Skills Extracted")

    if skills:
        by_domain: dict[str, list] = {}
        for s in skills:
            d = s.get("domain") or "Other"
            by_domain.setdefault(d, []).append(s)

        for domain, domain_skills in sorted(by_domain.items()):
            with st.expander(f"**{domain}** ({len(domain_skills)} skills)", expanded=True):
                for s in sorted(domain_skills, key=lambda x: -x.get("frequency", 1)):
                    badge = "🟢" if s.get("frequency", 1) > 2 else "⚪"
                    st.write(f"{badge} **{s['canonical_name']}** × {s.get('frequency', 1)}")
                    if s.get("evidence_snippet"):
                        st.caption(f"> {s['evidence_snippet']}")
    else:
        st.info("No skills extracted.")

    # File metadata
    with st.expander("📄 File Metadata"):
        st.write(f"**Original filename:** {resume.get('original_filename')}")
        st.write(f"**File size:** {resume.get('file_size_bytes', 0):,} bytes")
        st.write(f"**Pages:** {resume.get('page_count', 'N/A')}")
        st.write(f"**Text length:** {resume.get('text_char_count', 0):,} characters")
        st.write(f"**Uploaded:** {resume.get('uploaded_at', '')[:19]}")
