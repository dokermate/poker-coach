"""Shared API client for Streamlit pages."""
import os
import requests
import streamlit as st

API_BASE = os.environ.get("API_BASE", "http://localhost:8000")


def get_headers() -> dict:
    token = st.session_state.get("token", "")
    return {"Authorization": f"Bearer {token}"} if token else {}


def api_get(path: str, params: dict | None = None):
    r = requests.get(f"{API_BASE}{path}", headers=get_headers(), params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def api_post(path: str, json: dict | None = None):
    r = requests.post(f"{API_BASE}{path}", headers=get_headers(), json=json, timeout=30)
    r.raise_for_status()
    return r.json()


def api_delete(path: str):
    r = requests.delete(f"{API_BASE}{path}", headers=get_headers(), timeout=10)
    r.raise_for_status()
    return r.status_code


def require_auth():
    """Redirect to login if not authenticated."""
    if not st.session_state.get("token"):
        st.warning("Please log in first.")
        st.stop()
