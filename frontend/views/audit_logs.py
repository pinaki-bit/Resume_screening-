"""
frontend/pages/audit_logs.py

Audit log viewer — admin only.
"""

from __future__ import annotations

import streamlit as st
from services.api_client import APIError, get_audit_logs


def render_audit_logs():
    user = st.session_state.get("user") or {}
    if user.get("role") != "admin":
        st.error("Access denied. Admin role required.")
        return

    st.title("📋 Audit Logs")
    st.caption("All security-sensitive actions are logged here. Logs are append-only.")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        event_type_filter = st.text_input(
            "Filter by event type prefix",
            placeholder="e.g. auth, resume, admin",
        )
    with col2:
        actor_filter = st.text_input("Filter by actor email")
    with col3:
        page = st.number_input("Page", min_value=1, value=1)

    try:
        data = get_audit_logs(
            page=page,
            event_type=event_type_filter.strip() or None,
        )
    except APIError as e:
        st.error(f"Failed to load audit logs: {e.detail}")
        return

    total = data.get("total", 0)
    events = data.get("events", [])

    st.caption(f"**{total}** total events | Page {page}")

    if not events:
        st.info("No audit events found.")
        return

    _OUTCOME_ICON = {"success": "✅", "failure": "❌", "error": "⚠️"}

    for event in events:
        icon = _OUTCOME_ICON.get(event.get("outcome", "success"), "")
        with st.expander(
            f"{icon} [{event.get('occurred_at', '')[:19]}] "
            f"**{event.get('event_type')}** — {event.get('actor_email', 'System')}"
        ):
            cols = st.columns(3)
            with cols[0]:
                st.write(f"**Summary:** {event.get('summary')}")
                st.write(f"**Outcome:** {event.get('outcome')}")
            with cols[1]:
                st.write(f"**Resource:** {event.get('resource_type')} `{event.get('resource_id', '—')}`")
                st.write(f"**IP:** {event.get('ip_address', '—')}")
            with cols[2]:
                st.write(f"**Event ID:** {event.get('id')}")
