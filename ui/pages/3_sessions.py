"""Page 3: Sessions — start, view, and close game sessions."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from ui.api_client import api_get, api_post, require_auth

st.set_page_config(page_title="Sessions — Poker Coach", page_icon="📋")
require_auth()
st.title("📋 Sessions")

# ── New session ───────────────────────────────────────────────────────────────
with st.expander("▶️ Start New Session", expanded=False):
    try:
        tables = api_get("/tables")
    except Exception:
        tables = []

    if not tables:
        st.warning("Create a table first.")
    else:
        with st.form("new_session"):
            table_options = {f"{t['name']} (${t['bb_usd']:.2f} BB)": t for t in tables}
            chosen_label = st.selectbox("Select Table", list(table_options.keys()))
            chosen_table = table_options[chosen_label]
            start_stack = st.number_input(
                "Starting Stack ($)", min_value=1.0,
                value=float(chosen_table["bb_usd"] * 100),
                step=1.0, format="%.2f"
            )
            bb_val = chosen_table["bb_usd"]
            st.caption(f"= {start_stack / bb_val:.1f} BB")
            if st.form_submit_button("Start Session", use_container_width=True):
                try:
                    sess = api_post("/sessions", {
                        "table_id": chosen_table["id"],
                        "start_stack_usd": start_stack,
                    })
                    st.session_state["active_session_id"] = sess["id"]
                    st.session_state["active_table_bb"] = chosen_table["bb_usd"]
                    st.success(f"Session #{sess['id']} started!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# ── Active session banner ─────────────────────────────────────────────────────
active_id = st.session_state.get("active_session_id")
if active_id:
    st.info(f"🟢 Active session: **#{active_id}**  ·  Navigate to **New Hand** to log hands.")

# ── List sessions ─────────────────────────────────────────────────────────────
st.divider()
st.subheader("All Sessions")
try:
    sessions = api_get("/sessions")
except Exception as e:
    st.error(f"Could not load sessions: {e}")
    sessions = []

if not sessions:
    st.info("No sessions yet.")
else:
    for s in sessions:
        status_icon = "🟢" if s["status"] == "active" else "⚫"
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([1, 2, 2, 2])
            with col1:
                st.markdown(f"**#{s['id']}** {status_icon}")
            with col2:
                st.metric("Start Stack", f"${s['start_stack_usd']:.2f}")
                st.caption(f"{s['start_stack_bb']:.1f} BB")
            with col3:
                pnl = s["current_stack_usd"] - s["start_stack_usd"]
                delta_color = "normal" if pnl >= 0 else "inverse"
                st.metric("Current Stack", f"${s['current_stack_usd']:.2f}",
                          delta=f"{pnl:+.2f}", delta_color=delta_color)
            with col4:
                if s["status"] == "active":
                    col4a, col4b = st.columns(2)
                    with col4a:
                        if st.button("▶️ Resume", key=f"resume_{s['id']}"):
                            st.session_state["active_session_id"] = s["id"]
                            st.rerun()
                    with col4b:
                        if st.button("⏹ Close", key=f"close_{s['id']}"):
                            try:
                                api_post(f"/sessions/{s['id']}/close")
                                if st.session_state.get("active_session_id") == s["id"]:
                                    st.session_state["active_session_id"] = None
                                st.rerun()
                            except Exception as e:
                                st.error(str(e))
                else:
                    st.caption(f"Closed: {s.get('ended_at','')[:10]}")
