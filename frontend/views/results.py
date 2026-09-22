"""
frontend/pages/results.py

Screening results page — ranked candidates per job, with match breakdown and review.
"""

from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go
from services.api_client import (
    APIError, list_jobs, list_resumes, match_resume_to_job,
    get_job_results, update_review
)


_TIER_COLOR = {
    "Excellent": "#06D6A0",
    "Good": "#48CAE4",
    "Fair": "#FFD166",
    "Low Match": "#EF476F",
}

_REVIEW_OPTIONS = ["pending", "approved", "rejected", "on_hold"]


def render_results():
    st.title("🔍 Screening Results")

    tab1, tab2 = st.tabs(["📊 Ranked Results", "➕ Run Screening"])

    with tab1:
        _render_ranked_results()
    with tab2:
        _render_run_screening()


def _render_ranked_results():
    # Job selector
    try:
        jobs = list_jobs()
    except APIError as e:
        st.error(f"Failed to load jobs: {e.detail}")
        return

    if not jobs:
        st.info("No active jobs found. Create a job first.")
        return

    job_options = {j["title"]: j["public_id"] for j in jobs}
    selected_title = st.selectbox("Select Job", options=list(job_options.keys()))
    job_id = job_options[selected_title]

    review_filter = st.selectbox("Filter by review status", ["All"] + _REVIEW_OPTIONS)
    status_param = None if review_filter == "All" else review_filter

    try:
        ranked = get_job_results(job_id, review_status=status_param)
    except APIError as e:
        st.error(f"Failed to load results: {e.detail}")
        return

    if not ranked:
        st.info("No screening results for this job yet. Use 'Run Screening' to match resumes.")
        return

    st.caption(f"**{len(ranked)} candidates** screened for {selected_title}")

    # Score bar chart
    names = [f"#{r['rank']} Resume {str(r['resume_id'])}" for r in ranked]
    scores = [r["relevance_score"] for r in ranked]
    colors = [_TIER_COLOR.get(r["tier"], "#888") for r in ranked]

    fig = go.Figure(go.Bar(
        x=scores, y=names, orientation="h",
        marker_color=colors,
        text=[f"{s:.1f}%" for s in scores],
        textposition="outside",
    ))
    fig.update_layout(
        height=max(200, len(ranked) * 40),
        margin=dict(l=20, r=60, t=10, b=10),
        xaxis=dict(range=[0, 105], title="Relevance Score"),
        yaxis=dict(autorange="reversed"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Detailed cards
    for r in ranked:
        tier = r.get("tier", "Unknown")
        color = _TIER_COLOR.get(tier, "#888")
        with st.expander(
            f"**#{r['rank']}** — Relevance: {r['relevance_score']:.1f}% "
            f"[{tier}] | {r.get('review_status', 'pending').upper()}",
            expanded=(r["rank"] == 1),
        ):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Required Coverage", f"{r.get('required_coverage', 0):.1f}%")
            with c2:
                st.metric("Preferred Coverage", f"{r.get('preferred_coverage', 0):.1f}%")
            with c3:
                st.metric("Domain Match", r.get("predicted_domain") or "Unknown")

            c4, c5 = st.columns(2)
            with c4:
                st.metric("Required Skills Matched", r.get("matched_required_count", 0))
            with c5:
                st.metric("Required Skills Missing", r.get("missing_required_count", 0))

            # Score breakdown
            if r.get("score_breakdown"):
                with st.expander("📋 Score Breakdown (Explainability)", expanded=False):
                    bd = r["score_breakdown"]
                    if isinstance(bd, dict):
                        for k, v in bd.items():
                            st.write(f"**{k}:** {v}")

            # Review action
            st.markdown("---")
            col_rev, col_note = st.columns([2, 3])
            with col_rev:
                new_status = st.selectbox(
                    "Update Review Status",
                    _REVIEW_OPTIONS,
                    index=_REVIEW_OPTIONS.index(r.get("review_status", "pending")),
                    key=f"rev_status_{r['public_id']}",
                )
            with col_note:
                note = st.text_input(
                    "Review Note",
                    key=f"rev_note_{r['public_id']}",
                    placeholder="Optional reviewer note…",
                )
            if st.button("💾 Save Review", key=f"save_rev_{r['public_id']}"):
                try:
                    update_review(r["public_id"], new_status, note or None)
                    st.success("Review updated.")
                    st.rerun()
                except APIError as e:
                    st.error(f"Failed to update review: {e.detail}")


def _render_run_screening():
    st.subheader("Match a Resume to a Job")

    try:
        jobs = list_jobs()
        resumes = list_resumes(status_filter=None)
    except APIError as e:
        st.error(f"Failed to load data: {e.detail}")
        return

    if not jobs:
        st.info("No active jobs. Create a job first.")
        return

    if not resumes:
        st.info("No resumes uploaded yet. Upload resumes first.")
        return

    job_options = {j["title"]: j["public_id"] for j in jobs}
    resume_options = {
        f"Resume {r['public_id'][:8]}… — {r['predicted_domain'] or 'Unclassified'} "
        f"[{r['status']}]": r["public_id"]
        for r in resumes
    }

    selected_job = st.selectbox("Job", list(job_options.keys()))
    selected_resume = st.selectbox("Resume", list(resume_options.keys()))

    if st.button("▶ Run Skill Match", type="primary", use_container_width=True):
        job_id = job_options[selected_job]
        resume_id = resume_options[selected_resume]
        with st.spinner("Computing skill match…"):
            try:
                result = match_resume_to_job(job_id, resume_id)
                st.success(f"Match complete — Relevance Score: **{result['relevance_score']:.1f}%**")
                st.json({
                    "required_coverage": result.get("required_skill_coverage"),
                    "preferred_coverage": result.get("preferred_skill_coverage"),
                    "relevance_score": result.get("relevance_score"),
                    "review_status": result.get("review_status"),
                })
                st.session_state["page"] = "results"
                st.rerun()
            except APIError as e:
                st.error(f"Matching failed: {e.detail}")
