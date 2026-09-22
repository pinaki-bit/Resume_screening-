"""
frontend/pages/admin.py

Admin panel — user management and model versions.
"""

from __future__ import annotations

import streamlit as st
from services.api_client import APIError, create_user, list_users, list_model_versions, update_user


def render_admin():
    user = st.session_state.get("user") or {}
    if user.get("role") != "admin":
        st.error("Access denied. Admin role required.")
        return

    st.title("⚙️ Admin Panel")

    tab_users, tab_models = st.tabs(["👥 User Management", "🤖 Model Versions"])

    with tab_users:
        _render_users()

    with tab_models:
        _render_models()


def _render_users():
    st.subheader("User Accounts")

    try:
        users = list_users()
    except APIError as e:
        st.error(f"Failed to load users: {e.detail}")
        return

    # Existing users table
    for u in users:
        status_icon = "🟢" if u["is_active"] else "🔴"
        role_icon = {"admin": "👑", "hr": "🧑‍💼", "readonly": "👁️"}.get(u["role"], "")
        with st.expander(
            f"{status_icon} {role_icon} {u.get('full_name') or u['email']} [{u['role']}]"
        ):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Email:** {u['email']}")
                st.write(f"**Created:** {u['created_at'][:10]}")
            with col2:
                new_role = st.selectbox(
                    "Role",
                    ["admin", "hr", "readonly"],
                    index=["admin", "hr", "readonly"].index(u["role"]),
                    key=f"role_{u['id']}",
                )
                new_active = st.toggle("Active", value=u["is_active"], key=f"active_{u['id']}")
            with col3:
                if st.button("Update", key=f"upd_{u['id']}"):
                    try:
                        update_user(u["id"], {"role": new_role, "is_active": new_active})
                        st.success("User updated.")
                        st.rerun()
                    except APIError as e:
                        st.error(f"Update failed: {e.detail}")

    st.divider()
    st.subheader("Create New User")
    with st.form("create_user_form"):
        email = st.text_input("Email *")
        password = st.text_input("Password *", type="password")
        full_name = st.text_input("Full Name")
        role = st.selectbox("Role", ["hr", "admin", "readonly"])
        submitted = st.form_submit_button("Create User", type="primary")

    if submitted:
        if not email or not password:
            st.error("Email and password are required.")
        elif len(password) < 8:
            st.error("Password must be at least 8 characters.")
        else:
            try:
                create_user({
                    "email": email,
                    "password": password,
                    "full_name": full_name or None,
                    "role": role,
                })
                st.success(f"User '{email}' created with role '{role}'.")
                st.rerun()
            except APIError as e:
                st.error(f"Failed to create user: {e.detail}")


def _render_models():
    st.subheader("Trained Model Versions")
    st.caption(
        "Train a model using `ml/scripts/train_model.py`, then register it here. "
        "Only the active model is used for classification."
    )

    try:
        versions = list_model_versions()
    except APIError as e:
        st.error(f"Failed to load model versions: {e.detail}")
        return

    if not versions:
        st.info(
            "No model versions registered yet.\n\n"
            "Train a model and register it via the admin API, "
            "or run `ml/scripts/train_model.py` after providing your dataset."
        )
        return

    for v in versions:
        active_badge = "🟢 **ACTIVE**" if v["is_active"] else "⚪ Inactive"
        with st.expander(
            f"{active_badge} — v{v['version_tag']} | macro-F1: {v.get('test_macro_f1', 'N/A')}"
        ):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Macro F1", f"{v.get('test_macro_f1', 0):.4f}" if v.get("test_macro_f1") else "N/A")
            with c2:
                st.metric("Weighted F1", f"{v.get('test_weighted_f1', 0):.4f}" if v.get("test_weighted_f1") else "N/A")
            with c3:
                st.metric("Training Samples", v.get("training_samples", "N/A"))
