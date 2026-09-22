"""
frontend/pages/jobs.py

Job management page — create, view, and manage job descriptions.
"""

from __future__ import annotations

import streamlit as st
from services.api_client import APIError, create_job, deactivate_job, get_job, list_jobs


def render_jobs():
    st.title("💼 Job Management")

    user = st.session_state.get("user") or {}
    role = user.get("role", "readonly")

    tab1, tab2 = st.tabs(["📋 All Jobs", "➕ Create Job"])

    with tab1:
        _render_job_list(role)

    with tab2:
        if role in ("hr", "admin"):
            _render_create_job(role)
        else:
            st.info("You do not have permission to create jobs.")


def _render_job_list(role: str):
    try:
        jobs = list_jobs(active_only=False)
    except APIError as e:
        st.error(f"Failed to load jobs: {e.detail}")
        return

    if not jobs:
        st.info("No jobs found. Create a job using the 'Create Job' tab.")
        return

    for job in jobs:
        with st.expander(
            f"{'🟢' if job['is_active'] else '🔴'} {job['title']} "
            f"— {job.get('domain', 'Unspecified')} "
            f"({len(job.get('requirements', []))} requirements)",
            expanded=False,
        ):
            col1, col2 = st.columns([3, 1])
            with col1:
                if job.get("department"):
                    st.caption(f"**Department:** {job['department']}")
                if job.get("description"):
                    st.write(job["description"])
                # Requirements
                reqs = job.get("requirements", [])
                if reqs:
                    req_strs = [
                        f"{'🔴 Required' if r['is_required'] else '🟡 Preferred'}: "
                        f"**{r['skill_name']}** (weight {r['weight']})"
                        for r in reqs
                    ]
                    st.markdown("\n".join(f"- {r}" for r in req_strs))
            with col2:
                st.caption(f"ID: `{job['public_id'][:8]}…`")
                if role == "admin" and job["is_active"]:
                    if st.button("Deactivate", key=f"deact_{job['public_id']}"):
                        try:
                            deactivate_job(job["public_id"])
                            st.success("Job deactivated.")
                            st.rerun()
                        except APIError as e:
                            st.error(e.detail)
                if st.button("🔍 Screen Candidates", key=f"screen_{job['public_id']}"):
                    st.session_state["selected_job_id"] = job["public_id"]
                    st.session_state["page"] = "results"
                    st.rerun()


def _render_create_job(role: str):
    st.subheader("Create New Job Description")

    domains = ["Data Science", "Web Development", "Cloud Computing", "DevOps", "Cybersecurity"]

    with st.form("create_job_form"):
        title = st.text_input("Job Title *", placeholder="e.g. Senior Data Scientist")
        department = st.text_input("Department", placeholder="e.g. Analytics")
        domain = st.selectbox("Domain", options=[""] + domains)
        description = st.text_area("Job Description", height=120)

        st.subheader("Requirements")
        st.caption("Add required and preferred skills. Required skills carry 70% of the match score.")

        num_req = st.number_input("Number of required skills to add", min_value=0, max_value=20, value=3)
        requirements = []

        for i in range(int(num_req)):
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                skill = st.text_input(f"Required skill #{i+1}", key=f"req_skill_{i}")
            with c2:
                weight = st.number_input("Weight", min_value=0.1, max_value=5.0, value=1.0, key=f"req_w_{i}")
            with c3:
                is_req = st.selectbox("Type", ["Required", "Preferred"], key=f"req_type_{i}")
            if skill:
                requirements.append({
                    "skill_name": skill,
                    "is_required": is_req == "Required",
                    "weight": weight,
                })

        submitted = st.form_submit_button("Create Job", type="primary", use_container_width=True)

    if submitted:
        if not title.strip():
            st.error("Job title is required.")
            return
        payload = {
            "title": title.strip(),
            "department": department.strip() or None,
            "domain": domain or None,
            "description": description.strip() or None,
            "requirements": requirements,
        }
        try:
            job = create_job(payload)
            st.success(f"✅ Job '{job['title']}' created successfully!")
            st.rerun()
        except APIError as e:
            st.error(f"Failed to create job: {e.detail}")
