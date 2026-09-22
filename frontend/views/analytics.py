"""
frontend/pages/analytics.py

Analytics page with skill heatmap, score histogram, and review status charts.
"""

from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from services.api_client import APIError, get_domain_distribution, get_skill_heatmap, get_score_distribution


def render_analytics():
    st.title("📈 Analytics & Intelligence")

    tab_heatmap, tab_scores, tab_domain = st.tabs([
        "🔥 Skill Heatmap", "📊 Score Distribution", "🎯 Domain Distribution"
    ])

    with tab_heatmap:
        _render_skill_heatmap()

    with tab_scores:
        _render_score_histogram()

    with tab_domain:
        _render_domain_pie()


def _render_skill_heatmap():
    st.subheader("Top Skills by Domain")
    st.caption(
        "Frequency of skills extracted across all processed resumes. "
        "Brighter cells = higher frequency."
    )

    top_n = st.slider("Top N skills per domain", 5, 25, 10)

    try:
        data = get_skill_heatmap(top_n=top_n)
    except APIError as e:
        st.warning(f"Could not load skill heatmap: {e.detail}")
        return

    domains_data = data.get("domains", {})
    if not domains_data:
        st.info("No skill data available yet. Process resumes to populate this chart.")
        return

    # Build matrix
    all_skills = sorted({
        s["skill"] for skills in domains_data.values() for s in skills
    })
    domains = sorted(domains_data.keys())

    matrix = []
    for domain in domains:
        skill_map = {s["skill"]: s["frequency"] for s in domains_data.get(domain, [])}
        row = [skill_map.get(skill, 0) for skill in all_skills]
        matrix.append(row)

    if not matrix or not all_skills:
        st.info("Insufficient data for heatmap.")
        return

    fig = go.Figure(go.Heatmap(
        z=matrix,
        x=all_skills,
        y=domains,
        colorscale="Viridis",
        text=[[str(v) if v > 0 else "" for v in row] for row in matrix],
        texttemplate="%{text}",
        showscale=True,
        colorbar=dict(title="Frequency"),
    ))
    fig.update_layout(
        height=max(300, len(domains) * 60),
        margin=dict(l=20, r=20, t=20, b=100),
        xaxis=dict(tickangle=-45),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_score_histogram():
    st.subheader("Relevance Score Distribution")
    st.caption("How screening scores are distributed across all candidates.")

    try:
        data = get_score_distribution()
    except APIError as e:
        st.warning(f"Could not load score distribution: {e.detail}")
        return

    total = data.get("total_screened", 0)
    mean_score = data.get("mean_score")
    buckets = data.get("buckets", [])

    if total == 0:
        st.info("No screening results yet.")
        return

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Screened", total)
    with col2:
        st.metric("Mean Score", f"{mean_score:.1f}%" if mean_score else "N/A")

    ranges = [b["range"] for b in buckets]
    counts = [b["count"] for b in buckets]
    pcts = [b["percentage"] for b in buckets]

    fig = go.Figure(go.Bar(
        x=ranges, y=counts,
        marker_color=["#EF476F", "#FFD166", "#06D6A0", "#48CAE4", "#6C63FF"],
        text=[f"{p:.0f}%" for p in pcts],
        textposition="outside",
    ))
    fig.update_layout(
        xaxis_title="Score Range",
        yaxis_title="Number of Candidates",
        height=320,
        margin=dict(t=20, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_domain_pie():
    st.subheader("Resume Domain Distribution")

    try:
        data = get_domain_distribution()
    except APIError as e:
        st.warning(f"Could not load domain distribution: {e.detail}")
        return

    items = data.get("distribution", [])
    if not items:
        st.info("No processed resumes yet.")
        return

    fig = px.pie(
        names=[i["domain"] for i in items],
        values=[i["count"] for i in items],
        color_discrete_sequence=["#6C63FF", "#48CAE4", "#06D6A0", "#FFD166", "#EF476F"],
        hole=0.4,
    )
    fig.update_layout(
        height=380,
        margin=dict(t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)
