"""
frontend/components/sidebar.py

Sidebar navigation component.
"""

from __future__ import annotations

import streamlit as st


def render_sidebar():
    user = st.session_state.get("user") or {}
    role = user.get("role", "")
    name = user.get("full_name") or user.get("email", "User")

    with st.sidebar:
        st.markdown("## 🎯 Resume Intelligence")
        st.caption(f"Logged in as **{name}** `[{role}]`")
        st.divider()

        # Navigation buttons
        nav_items = [
            ("📊 Dashboard", "dashboard"),
            ("💼 Jobs", "jobs"),
            ("📤 Upload Resume", "upload"),
            ("🔍 Screening Results", "results"),
            ("📈 Analytics", "analytics"),
        ]

        # Admin-only items
        if role == "admin":
            nav_items += [
                ("⚙️ Admin Panel", "admin"),
                ("📋 Audit Logs", "audit"),
            ]

        for label, page_key in nav_items:
            is_active = st.session_state.get("page") == page_key
            btn_type = "primary" if is_active else "secondary"
            if st.button(label, key=f"nav_{page_key}", use_container_width=True, type=btn_type):
                st.session_state["page"] = page_key
                st.rerun()

        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
