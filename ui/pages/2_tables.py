"""Page 2: Tables — create and manage poker tables."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from ui.api_client import api_get, api_post, api_delete, require_auth

st.set_page_config(page_title="Tables — Poker Coach", page_icon="🃏")
require_auth()
st.title("🃏 Tables")
st.caption("Create tables that define your blind structure. Each session references a table.")

# ── Create new table ──────────────────────────────────────────────────────────
with st.expander("➕ Create New Table", expanded=False):
    with st.form("create_table"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Table Name", placeholder="NL50 Zoom")
            sb = st.number_input("Small Blind ($)", min_value=0.01, value=0.25, step=0.01, format="%.2f")
            bb = st.number_input("Big Blind ($)", min_value=0.02, value=0.50, step=0.01, format="%.2f")
        with col2:
            ante = st.number_input("Ante ($)", min_value=0.0, value=0.0, step=0.01, format="%.2f")
            game_type = st.selectbox("Game Type", ["cash", "mtt"])
            max_players = st.selectbox("Max Players", [6, 9])
        if st.form_submit_button("Create Table", use_container_width=True):
            try:
                api_post("/tables", {
                    "name": name, "sb_usd": sb, "bb_usd": bb,
                    "ante_usd": ante, "game_type": game_type, "max_players": max_players,
                })
                st.success(f"Table '{name}' created!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# ── List tables ───────────────────────────────────────────────────────────────
try:
    tables = api_get("/tables")
except Exception as e:
    st.error(f"Could not load tables: {e}")
    tables = []

if not tables:
    st.info("No tables yet. Create one above.")
else:
    for t in tables:
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.subheader(t["name"])
                st.caption(f"{t['game_type'].upper()} · {t['max_players']}-max")
            with col2:
                st.metric("Blinds", f"${t['sb_usd']:.2f} / ${t['bb_usd']:.2f}")
                if t["ante_usd"] > 0:
                    st.caption(f"Ante: ${t['ante_usd']:.2f}")
            with col3:
                if st.button("🗑️ Delete", key=f"del_{t['id']}"):
                    try:
                        api_delete(f"/tables/{t['id']}")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
