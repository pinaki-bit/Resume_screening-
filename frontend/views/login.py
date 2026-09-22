"""
frontend/pages/login.py

Login page.
"""

from __future__ import annotations

import streamlit as st
from services.api_client import APIError, login, get_me


def render_login():
    # Center the login card
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            """
            <div style="text-align:center; padding: 2rem 0 1rem 0;">
                <h1 style="font-size:2.8rem;">🎯</h1>
                <h2 style="font-size:1.8rem; margin:0;">Resume Intelligence</h2>
                <p style="color:#888; margin:0.5rem 0 2rem 0;">AI-Powered Candidate Screening System</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            email = st.text_input("Email", placeholder="admin@example.com")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")

        if submitted:
            if not email or not password:
                st.error("Please enter your email and password.")
                return
            with st.spinner("Authenticating…"):
                try:
                    token_data = login(email, password)
                    st.session_state["access_token"] = token_data["access_token"]
                    # Load user profile
                    user = get_me()
                    st.session_state["user"] = user
                    st.session_state["page"] = "dashboard"
                    st.success("Logged in successfully!")
                    st.rerun()
                except APIError as e:
                    if e.status_code == 401:
                        st.error("Incorrect email or password.")
                    elif e.status_code == 403:
                        st.error("Your account is disabled. Contact an administrator.")
                    else:
                        st.error(f"Login failed: {e.detail}")
                except Exception:
                    st.error("Cannot reach the API. Ensure the backend is running on port 8000.")

        st.markdown(
            "<p style='text-align:center; color:#666; font-size:0.8rem; margin-top:2rem;'>"
            "For authorized personnel only.</p>",
            unsafe_allow_html=True,
        )
