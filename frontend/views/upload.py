"""
frontend/pages/upload.py

Secure resume upload page.
"""

from __future__ import annotations

import streamlit as st
from services.api_client import APIError, upload_resume


_CONFIDENCE_COLOR = {
    "high": "🟢",
    "medium": "🟡",
    "low": "🔴",
    "unavailable": "⚫",
}

_STATUS_LABEL = {
    "completed": "✅ Completed",
    "needs_review": "⚠️ Needs Review",
    "failed": "❌ Failed",
    "uploaded": "📥 Uploaded",
    "processing": "⏳ Processing",
}


def render_upload():
    st.title("📤 Upload Resume")
    st.caption(
        "Upload a text-based PDF resume. "
        "The system will extract skills and classify the candidate's domain automatically."
    )

    user = st.session_state.get("user") or {}
    role = user.get("role", "readonly")
    if role == "readonly":
        st.warning("Read-only users cannot upload resumes.")
        return

    with st.form("upload_form", clear_on_submit=True):
        uploaded_file = st.file_uploader(
            "Select PDF resume",
            type=["pdf"],
            help="Maximum file size: 10 MB. Text-based PDFs only (no image-only scans).",
        )
        candidate_ref = st.text_input(
            "Candidate Reference Code (optional)",
            placeholder="e.g. CAND-2024-001",
            help="Link this resume to an existing or new candidate record.",
        )
        submitted = st.form_submit_button("Upload & Process", type="primary", use_container_width=True)

    if submitted:
        if not uploaded_file:
            st.error("Please select a PDF file to upload.")
            return

        with st.spinner("Uploading and processing resume… This may take 10–30 seconds."):
            try:
                result = upload_resume(
                    file_bytes=uploaded_file.read(),
                    filename=uploaded_file.name,
                    candidate_ref=candidate_ref.strip() or None,
                )
                _display_result(result)
            except APIError as e:
                if e.status_code == 422:
                    st.error(f"File validation failed: {e.detail}")
                elif e.status_code == 409:
                    st.warning(f"Cannot process resume: {e.detail}")
                else:
                    st.error(f"Upload failed: {e.detail}")


def _display_result(result: dict):
    status = result.get("status", "unknown")
    icon = _STATUS_LABEL.get(status, status)
    conf = result.get("prediction_confidence", "unavailable")
    conf_icon = _CONFIDENCE_COLOR.get(conf, "⚫")

    st.success(f"**Processing complete** — {icon}")
    st.divider()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Status", icon)
    with c2:
        st.metric("Predicted Domain", result.get("predicted_domain") or "Unknown")
    with c3:
        st.metric("Confidence", f"{conf_icon} {conf.capitalize()}")
    with c4:
        st.metric("Text Extracted", f"{result.get('text_char_count', 0):,} chars")

    # Skills
    skills = result.get("extracted_skills", [])
    if skills:
        st.subheader(f"🔧 {len(skills)} Skills Extracted")
        # Group by domain
        by_domain: dict[str, list] = {}
        for s in skills:
            d = s.get("domain") or "Other"
            by_domain.setdefault(d, []).append(s)
        for domain, domain_skills in by_domain.items():
            with st.expander(f"**{domain}** ({len(domain_skills)} skills)"):
                for s in sorted(domain_skills, key=lambda x: -x.get("frequency", 1)):
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.write(f"**{s['canonical_name']}**")
                        if s.get("evidence_snippet"):
                            st.caption(f"…{s['evidence_snippet']}…")
                    with col_b:
                        st.caption(f"×{s.get('frequency', 1)}")
    else:
        st.info("No skills were extracted from this resume.")

    if status == "needs_review":
        st.warning(
            "⚠️ Classification confidence is low. "
            "This resume is flagged for human review before any screening decision."
        )
    if result.get("error_message"):
        st.error(f"Processing note: {result['error_message']}")

    # Actions
    col_l, col_r = st.columns(2)
    with col_l:
        if st.button("🔍 Screen Against a Job", use_container_width=True, type="primary"):
            st.session_state["selected_resume_id"] = result["public_id"]
            st.session_state["page"] = "results"
            st.rerun()
    with col_r:
        if st.button("📤 Upload Another", use_container_width=True):
            st.rerun()
