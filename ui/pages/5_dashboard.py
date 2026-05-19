"""Page 5: Dashboard — P&L, equity curve, leaks, hand history."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from ui.api_client import api_get, require_auth

st.set_page_config(page_title="Dashboard — Poker Coach", page_icon="📊", layout="wide")
require_auth()
st.title("📊 Dashboard")

# ── Filters ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.subheader("Filters")
    try:
        sessions = api_get("/sessions")
        session_opts = {"All sessions": None} | {f"Session #{s['id']} ({s['status']})": s["id"] for s in sessions}
    except Exception:
        sessions = []
        session_opts = {"All sessions": None}

    chosen_label = st.selectbox("Session", list(session_opts.keys()))
    session_id = session_opts[chosen_label]

# ── Summary metrics ────────────────────────────────────────────────────────────
try:
    params = {}
    if session_id:
        params["session_id"] = session_id
    summary = api_get("/stats/summary", params=params)
except Exception as e:
    st.error(f"Could not load stats: {e}")
    st.stop()

st.subheader("📈 Performance Summary")
m1, m2, m3, m4, m5, m6 = st.columns(6)
with m1:
    st.metric("Hands Played", summary["hands_played"])
with m2:
    st.metric("Session P&L", f"${summary['session_pnl_usd']:+.2f}",
              delta=f"{summary['session_pnl_bb']:+.1f} BB")
with m3:
    st.metric("BB/100", f"{summary['bb_per_100']:+.2f}")
with m4:
    st.metric("Alignment Rate", f"{summary['alignment_rate_pct']:.1f}%")
with m5:
    st.metric("EV Loss Total", f"{summary['ev_loss_bb_total']:.2f} BB")
with m6:
    st.metric("Points", summary["total_points"])

col_a, col_b = st.columns(2)
with col_a:
    st.metric("Max Drawdown (USD)", f"${summary['max_drawdown_usd']:.2f}")
with col_b:
    st.metric("Max Drawdown (BB)", f"{summary['max_drawdown_bb']:.2f}")

# ── Equity Curve ───────────────────────────────────────────────────────────────
st.divider()
st.subheader("📉 Equity Curve")
try:
    curve_params = {}
    if session_id:
        curve_params["session_id"] = session_id
    curve = api_get("/stats/equity-curve", params=curve_params)
except Exception:
    curve = []

if curve:
    import json
    try:
        import plotly.graph_objects as go
        times = [p["played_at"][:19].replace("T", " ") for p in curve]
        pnls = [p["cumulative_pnl_usd"] for p in curve]
        stacks = [p["current_stack_usd"] for p in curve]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=times, y=pnls, mode="lines+markers",
                                  name="Cumulative P&L ($)", line=dict(color="#00d26a", width=2)))
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        fig.update_layout(height=300, margin=dict(l=0,r=0,t=20,b=0),
                          yaxis_title="Cumulative P&L ($)", xaxis_title="Time",
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        # Fallback: simple line chart
        chart_data = {p["played_at"][:16]: p["cumulative_pnl_usd"] for p in curve}
        st.line_chart(chart_data)
else:
    st.info("No hands recorded yet — log some hands to see your equity curve.")

# ── Leak Report ────────────────────────────────────────────────────────────────
st.divider()
st.subheader("🔍 Leak Report (by position / street / pot type)")
try:
    leak_params = {}
    if session_id:
        leak_params["session_id"] = session_id
    leaks = api_get("/stats/leaks", params=leak_params)
except Exception:
    leaks = []

if leaks:
    leak_rows = []
    for row in leaks:
        parts = row["group_key"].split("|")
        leak_rows.append({
            "Position": parts[0] if len(parts) > 0 else "",
            "Street": parts[1] if len(parts) > 1 else "",
            "Pot Type": parts[2] if len(parts) > 2 else "",
            "Hands": row["hands"],
            "Net BB": f"{row['net_bb']:+.2f}",
            "Alignment %": f"{row['alignment_rate_pct']:.0f}%",
            "EV Loss (BB)": f"{row['ev_loss_bb_sum']:.2f}",
        })
    st.dataframe(leak_rows, use_container_width=True)
else:
    st.info("No leak data yet.")

# ── Hand History ───────────────────────────────────────────────────────────────
st.divider()
st.subheader("📋 Hand History")
try:
    hand_params = {}
    if session_id:
        hand_params["session_id"] = session_id
    hands = api_get("/hands", params=hand_params)
except Exception:
    hands = []

if hands:
    rows = []
    for h in hands:
        aligned_icon = "✅" if h["aligned"] else "❌"
        rows.append({
            "#": h["id"],
            "Time": h["played_at"][:19].replace("T"," "),
            "Cards": h["hero_cards"].replace(",", " "),
            "Board": h["board"].replace(",", " ") or "—",
            "Street": h["street"],
            "Recommended": h["recommended_action"].upper(),
            "You Played": h["user_action"].upper(),
            "Net $": f"{h['net_usd']:+.2f}",
            "Net BB": f"{h['net_bb']:+.2f}",
            "Equity": f"{h['equity']*100:.0f}%",
            "Aligned": aligned_icon,
            "EV Loss": f"{h['ev_loss_bb']:.2f}",
            "Pts": f"{h['points_earned']:+d}",
        })
    st.dataframe(rows, use_container_width=True, height=400)
else:
    st.info("No hands recorded yet.")
