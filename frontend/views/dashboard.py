"""
frontend/pages/dashboard.py

Main dashboard with KPI cards and quick-access actions.
"""

from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go
from services.api_client import APIError, get_summary, get_domain_distribution


def render_dashboard():
    st.title("📊 Dashboard")

    user = st.session_state.get("user") or {}
    st.caption(f"Welcome back, **{user.get('full_name', user.get('email', 'User'))}**")

    # ── KPI Cards ─────────────────────────────────────────────────────────
    try:
        summary = get_summary()
    except APIError as e:
        st.error(f"Failed to load summary: {e.detail}")
        summary = {}

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("📄 Total Resumes", summary.get("total_resumes", "—"))
    with c2:
        st.metric(
            "✅ Processed",
            summary.get("processed_resumes", "—"),
            delta=f"{summary.get('processing_rate_pct', 0):.0f}% rate",
        )
    with c3:
        st.metric("💼 Active Jobs", summary.get("total_active_jobs", "—"))
    with c4:
        st.metric("👤 Candidates", summary.get("total_candidates", "—"))
    with c5:
        pending = summary.get("pending_reviews", 0)
        st.metric(
            "🕐 Pending Reviews",
            pending,
            delta=("Action needed" if pending > 0 else "All clear"),
            delta_color="inverse",
        )

    st.divider()

    # ── Domain Distribution Chart ──────────────────────────────────────────
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("Resume Domain Distribution")
        try:
            dist_data = get_domain_distribution()
            items = dist_data.get("distribution", [])
            if items:
                domains = [d["domain"] for d in items]
                counts = [d["count"] for d in items]
                fig = go.Figure(go.Bar(
                    x=domains,
                    y=counts,
                    marker_color=["#6C63FF", "#48CAE4", "#06D6A0", "#FFD166", "#EF476F"],
                    text=[f"{d['percentage']:.1f}%" for d in items],
                    textposition="outside",
                ))
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(size=13),
                    margin=dict(t=20, b=20),
                    xaxis_title="Domain",
                    yaxis_title="Resume Count",
                    height=320,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No processed resumes yet. Upload resumes to see domain distribution.")
        except APIError as e:
            st.warning(f"Could not load domain distribution: {e.detail}")

    with col_right:
        st.subheader("Quick Actions")
        if st.button("📤 Upload Resume", use_container_width=True, type="primary"):
            st.session_state["page"] = "upload"
            st.rerun()
        if st.button("💼 Create Job", use_container_width=True):
            st.session_state["page"] = "jobs"
            st.rerun()
        if st.button("🔍 View Results", use_container_width=True):
            st.session_state["page"] = "results"
            st.rerun()
        if st.button("📈 Analytics", use_container_width=True):
            st.session_state["page"] = "analytics"
            st.rerun()

        if summary.get("model_unavailable_count", 0) > 0:
            st.warning(
                f"⚠️ {summary['model_unavailable_count']} resume(s) could not be classified "
                "(model not available). Train a model to enable classification.",
                icon="⚠️",
            )
