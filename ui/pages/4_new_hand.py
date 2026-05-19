"""Page 4: New Hand — analyze a spot and log the result."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from ui.api_client import api_get, api_post, require_auth

st.set_page_config(page_title="New Hand — Poker Coach", page_icon="🎯", layout="wide")
require_auth()
st.title("🎯 New Hand")

# ── Check active session ───────────────────────────────────────────────────────
active_id = st.session_state.get("active_session_id")
if not active_id:
    st.warning("No active session. Go to **Sessions** to start one.")
    st.stop()

try:
    session = api_get(f"/sessions/{active_id}")
except Exception:
    st.error("Could not load session.")
    st.stop()

try:
    tables = api_get("/tables")
    table = next((t for t in tables if t["id"] == session["table_id"]), None)
    bb_usd = table["bb_usd"] if table else 1.0
except Exception:
    bb_usd = 1.0
    table = None

# ── Session info bar ──────────────────────────────────────────────────────────
col_s1, col_s2, col_s3 = st.columns(3)
with col_s1:
    st.metric("Session", f"#{active_id}")
with col_s2:
    st.metric("Current Stack", f"${session['current_stack_usd']:.2f}",
              delta=f"{session['current_stack_usd'] - session['start_stack_usd']:+.2f}")
with col_s3:
    if table:
        st.metric("Blinds", f"${table['sb_usd']:.2f}/${table['bb_usd']:.2f}")

st.divider()

POSITIONS = ["BTN", "CO", "HJ", "LJ", "UTG", "UTG1", "UTG2", "SB", "BB"]
RANKS_UI  = ["A","K","Q","J","T","9","8","7","6","5","4","3","2"]
SUITS_UI  = ["s","h","d","c"]
SUIT_SYMBOLS = {"s":"♠","h":"♥","d":"♦","c":"♣"}

# ── Hand setup form ────────────────────────────────────────────────────────────
with st.form("hand_form"):
    st.subheader("Hand Setup")
    col1, col2 = st.columns(2)

    with col1:
        hero_pos = st.selectbox("Hero Position", POSITIONS, index=0)
        villain_pos = st.selectbox("Villain Position", POSITIONS, index=5)
        street = st.selectbox("Street", ["preflop","flop","turn","river"])
        pot_type = st.selectbox("Pot Type", ["srp","3bp","4bp"])
        hero_role = st.selectbox("Hero Role", ["pfr","caller"])
        preflop_spot = st.selectbox("Preflop Spot", ["rfi","vs_open","vs_3bet","vs_4bet"])

    with col2:
        st.markdown("**Hero Cards**")
        hc1, hc2 = st.columns(2)
        with hc1:
            h1r = st.selectbox("Card 1 Rank", RANKS_UI, key="h1r")
            h1s = st.selectbox("Card 1 Suit", SUITS_UI, format_func=lambda x: SUIT_SYMBOLS[x], key="h1s")
        with hc2:
            h2r = st.selectbox("Card 2 Rank", RANKS_UI, index=1, key="h2r")
            h2s = st.selectbox("Card 2 Suit", SUITS_UI, index=1, format_func=lambda x: SUIT_SYMBOLS[x], key="h2s")
        hero_cards = [f"{h1r}{h1s}", f"{h2r}{h2s}"]

        st.markdown("**Board Cards** (leave rank blank for none)")
        board_cards = []
        board_cols = st.columns(5)
        for i, bc in enumerate(board_cols):
            with bc:
                br = st.selectbox(f"B{i+1}R", [""]+RANKS_UI, key=f"br{i}")
                bs = st.selectbox(f"B{i+1}S", SUITS_UI, format_func=lambda x: SUIT_SYMBOLS[x], key=f"bs{i}")
                if br:
                    board_cards.append(f"{br}{bs}")

        pot_bb = st.number_input("Pot (BB)", min_value=0.5, value=10.0, step=0.5)
        stack_bb = st.number_input("Effective Stack (BB)", min_value=1.0, value=100.0, step=5.0)
        ip = st.checkbox("Hero is In Position (IP)", value=True)
        mc_iter = st.select_slider("MC Iterations (speed vs accuracy)",
                                   options=[500, 1000, 2000, 3500, 5000], value=3500)

    analyze_clicked = st.form_submit_button("🔍 Analyze", use_container_width=True, type="primary")

# ── Analyze ────────────────────────────────────────────────────────────────────
if analyze_clicked or st.session_state.get("advice_data"):
    if analyze_clicked:
        payload = {
            "hero_position": hero_pos, "villain_position": villain_pos,
            "hero_cards": hero_cards, "board": board_cards,
            "street": street, "pot_type": pot_type,
            "hero_role": hero_role, "preflop_spot": preflop_spot,
            "pot_bb": pot_bb, "stack_bb": stack_bb,
            "ip": ip, "mc_iterations": mc_iter,
        }
        with st.spinner("Running Monte Carlo simulation…"):
            try:
                advice = api_post("/hands/analyze", payload)
                st.session_state["advice_data"] = advice
                st.session_state["hand_payload"] = payload
            except Exception as e:
                st.error(f"Analysis failed: {e}")
                st.stop()

    advice = st.session_state.get("advice_data")
    if not advice:
        st.stop()

    st.divider()
    st.subheader("📊 Advisor Recommendation")

    # Main recommendation
    ra_col, eq_col, ev_col = st.columns(3)
    action_emoji = {"bet_33":"💚","bet_66":"💛","bet_100":"🔴","check":"🔵","call":"🔵","fold":"⚫","raise":"🔴"}.get(advice["recommended_action"],"❓")
    with ra_col:
        size_str = f" ({advice['recommended_size']*100:.0f}% pot)" if advice.get("recommended_size") else ""
        st.metric("Recommended Action", f"{action_emoji} {advice['recommended_action'].upper()}{size_str}")
    with eq_col:
        st.metric("Hero Equity", f"{advice['equity']*100:.1f}%")
    with ev_col:
        ra_val = advice.get("range_advantage", 0)
        st.metric("Range Advantage", f"{ra_val*100:+.1f}%")

    st.info(advice["explanation"])
    st.caption(f"⚠️ {advice['disclaimer']}")

    # EV comparison table
    st.subheader("EV Breakdown")
    ev_data = sorted(advice["ev_comps"], key=lambda x: x["ev_bb"], reverse=True)
    best_ev = ev_data[0]["ev_bb"] if ev_data else 0

    ev_cols = st.columns(len(ev_data))
    for i, comp in enumerate(ev_data):
        with ev_cols[i]:
            delta = comp["ev_bb"] - best_ev
            action_label = comp["action"].replace("_", " ").upper()
            st.metric(
                action_label,
                f"{comp['ev_bb']:+.2f}bb",
                delta=f"{delta:.2f}bb" if delta < 0 else "best",
                delta_color="normal" if delta >= -0.15 else "inverse",
            )

    # Mix weights
    st.subheader("Mixing Strategy")
    mix_sorted = sorted(advice["mix_json"].items(), key=lambda x: x[1], reverse=True)
    mix_display = {k.replace("_"," ").upper(): v for k, v in mix_sorted}
    st.bar_chart(mix_display)

    # ── Log action ─────────────────────────────────────────────────────────────
    st.divider()
    st.subheader("✍️ Log Your Action & Result")

    action_options = ["fold","check","call","bet_33","bet_66","bet_100","raise"]
    with st.form("save_hand_form"):
        scol1, scol2 = st.columns(2)
        with scol1:
            user_action = st.selectbox(
                "Your Action",
                action_options,
                index=action_options.index(advice["recommended_action"])
                    if advice["recommended_action"] in action_options else 0,
            )
        with scol2:
            result_mode = st.radio("Enter result as", ["Net P&L ($)", "Stack After ($)"], horizontal=True)

        rcol1, rcol2 = st.columns(2)
        with rcol1:
            if result_mode == "Net P&L ($)":
                net_usd = st.number_input("Net P&L ($)", value=0.0, step=0.25, format="%.2f")
                stack_after_input = None
            else:
                stack_after_input = st.number_input(
                    "Stack After ($)", min_value=0.0,
                    value=float(session["current_stack_usd"]), step=1.0, format="%.2f"
                )
                net_usd = None
        with rcol2:
            if bb_usd and bb_usd > 0:
                if result_mode == "Net P&L ($)":
                    st.metric("Net BB", f"{net_usd/bb_usd:+.2f} BB")
                else:
                    diff = (stack_after_input or 0) - session["current_stack_usd"]
                    st.metric("Net BB", f"{diff/bb_usd:+.2f} BB")

        save_clicked = st.form_submit_button("💾 Save Hand", use_container_width=True, type="primary")

    if save_clicked:
        hand_payload = st.session_state.get("hand_payload", {})
        save_data = {
            **hand_payload,
            "session_id": active_id,
            "user_action": user_action,
            "net_usd": net_usd,
            "stack_after_usd": stack_after_input,
        }
        try:
            saved = api_post("/hands", save_data)
            aligned_str = "✅ Aligned" if saved["aligned"] else "❌ Not aligned"
            pts_str = f"{saved['points_earned']:+d} pts"
            ev_loss_str = f"EV loss: {saved['ev_loss_bb']:.2f} BB"
            st.success(f"Hand saved! {aligned_str} · {pts_str} · {ev_loss_str}")
            # Clear advice so form resets
            st.session_state.pop("advice_data", None)
            st.session_state.pop("hand_payload", None)
            st.rerun()
        except Exception as e:
            st.error(f"Save failed: {e}")
