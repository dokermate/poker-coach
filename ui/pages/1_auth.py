"""Page 1: Login / Register"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from ui.api_client import api_post, API_BASE
import requests

st.set_page_config(page_title="Auth — Poker Coach", page_icon="🔐")
st.title("🔐 Login / Register")

tab_login, tab_reg = st.tabs(["Log In", "Register"])

with tab_login:
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log In", use_container_width=True)
    if submitted:
        try:
            data = api_post("/auth/login", {"email": email, "password": password})
            st.session_state["token"] = data["access_token"]
            me = api_post  # just a reference; re-fetch user
            import requests as req
            r = req.get(f"{API_BASE}/auth/me",
                        headers={"Authorization": f"Bearer {data['access_token']}"})
            if r.ok:
                user = r.json()
                st.session_state["user_email"] = user["email"]
            st.success("Logged in! Navigate using the sidebar.")
            st.rerun()
        except Exception as e:
            st.error(f"Login failed: {e}")

with tab_reg:
    with st.form("reg_form"):
        r_email = st.text_input("Email", key="r_email")
        r_pass = st.text_input("Password", type="password", key="r_pass")
        r_pass2 = st.text_input("Confirm Password", type="password", key="r_pass2")
        submitted2 = st.form_submit_button("Create Account", use_container_width=True)
    if submitted2:
        if r_pass != r_pass2:
            st.error("Passwords don't match")
        else:
            try:
                data = api_post("/auth/register", {"email": r_email, "password": r_pass})
                st.session_state["token"] = data["access_token"]
                st.session_state["user_email"] = r_email
                st.success("Account created! Welcome.")
                st.rerun()
            except Exception as e:
                st.error(f"Registration failed: {e}")
