"""
frontend/app.py

Main Streamlit application router.
Manages session state, authentication gate, and page routing.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Resume Intelligence",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state defaults ─────────────────────────────────────────────────

def _init_session():
    defaults = {
        "access_token": None,
        "user": None,           # full user profile dict
        "page": "dashboard",
        "selected_job_id": None,
        "selected_resume_id": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

_init_session()


# ── Auth gate ──────────────────────────────────────────────────────────────

def _is_authenticated() -> bool:
    return bool(st.session_state.get("access_token"))


if not _is_authenticated():
    from views.login import render_login
    render_login()
    st.stop()


# ── Sidebar navigation ──────────────────────────────────────────────────────

from components.sidebar import render_sidebar
render_sidebar()


# ── Page routing ────────────────────────────────────────────────────────────

page = st.session_state.get("page", "dashboard")

if page == "dashboard":
    from views.dashboard import render_dashboard
    render_dashboard()

elif page == "jobs":
    from views.jobs import render_jobs
    render_jobs()

elif page == "upload":
    from views.upload import render_upload
    render_upload()

elif page == "results":
    from views.results import render_results
    render_results()

elif page == "candidate":
    from views.candidate_profile import render_candidate_profile
    render_candidate_profile()

elif page == "analytics":
    from views.analytics import render_analytics
    render_analytics()

elif page == "admin":
    from views.admin import render_admin
    render_admin()

elif page == "audit":
    from views.audit_logs import render_audit_logs
    render_audit_logs()

else:
    st.error(f"Unknown page: {page!r}")
