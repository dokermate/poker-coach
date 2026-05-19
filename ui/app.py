"""
Poker Coach — Streamlit multipage app entry point.
Run: streamlit run ui/app.py
"""
import streamlit as st

st.set_page_config(
    page_title="Poker Coach",
    page_icon="♠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state defaults ────────────────────────────────────────────────────
for key in ("token", "user_email", "active_session_id", "active_table_bb"):
    if key not in st.session_state:
        st.session_state[key] = None

# ── Navigation ────────────────────────────────────────────────────────────────
pages = {
    "🔐 Login / Register": "pages/1_auth.py",
    "🃏 Tables":            "pages/2_tables.py",
    "📋 Sessions":          "pages/3_sessions.py",
    "🎯 New Hand":          "pages/4_new_hand.py",
    "📊 Dashboard":         "pages/5_dashboard.py",
}

with st.sidebar:
    st.title("♠️ Poker Coach")
    st.caption("Monte Carlo advisor + bankroll tracker")

    if st.session_state.get("user_email"):
        st.success(f"Logged in as **{st.session_state['user_email']}**")
        if st.button("Log Out", use_container_width=True):
            for k in ("token", "user_email", "active_session_id", "active_table_bb"):
                st.session_state[k] = None
            st.rerun()
    else:
        st.info("Not logged in")

    st.divider()
    for label, path in pages.items():
        st.page_link(f"ui/{path}", label=label)

st.title("♠️ Poker Coach")
st.markdown(
    """
    Welcome to **Poker Coach** — a Monte Carlo–powered hand analyzer and bankroll tracker.

    > ⚠️ Advice is based on Monte Carlo simulation + simplified ranges.  
    > This is **NOT** a GTO/Nash equilibrium solver. Use as a learning tool.

    **Get started:** Log in (or register) using the sidebar, then create a table and start a session.
    """
)
