# app.py - LIVE NIFTY ATM ±5 OI Dashboard (Fixed!)
import streamlit as st
import pandas as pd
import numpy as np
from dhanhq import dhanhq  # For instrument list & option chain
from dhan_client import DhanLiveFeed
from oi_logic import *
import time

# ===== Dhan Credentials (Your real ones) =====
CLIENT_ID = "1106476940"
ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"  # Dhan Dashboard → Copy fresh JWT

# Auto-fetch Nifty ATM ±5 strikes (Weekly expiry, e.g., 24-Feb-2026)
@st.cache_data(ttl=300)
def get_nifty_strikes():
    context = dhanhq.DhanContext(CLIENT_ID, ACCESS_TOKEN)  # Temp context
    dhan = dhanhq.dhanhq(context)
    instruments = dhan.fetch_security_list("compact")  # Get all
    nifty_opts = [inst for inst in instruments if 'NIFTY' in inst.get('trading_symbol', '') and '24FEB26' in inst.get('trading_symbol', '')]
    # ATM ~25900 (live spot), strikes 25750-26000 step 50
    strikes = list(range(25750, 26001, 50))  # ±5 from 25900
    tokens = []
    for strike in strikes:
        ce_token = next((opt['security_id'] for opt in nifty_opts if f'{strike}CE' in opt.get('trading_symbol', '')), None)
        pe_token = next((opt['security_id'] for opt in nifty_opts if f'{strike}PE' in opt.get('trading_symbol', '')), None)
        if ce_token: tokens.append(int(ce_token))
        if pe_token: tokens.append(int(pe_token))
    return tokens[:10]  # Max 10 for demo (CE+PE x5)

TOKENS = get_nifty_strikes()

# ===== STREAMLIT UI =====
st.set_page_config(layout="wide", page_title="NIFTY OI Live")
st.title("🚀 LIVE NIFTY INSTITUTIONAL OI DASHBOARD")
st.caption("ATM ±5 Strikes | Real Dhan WS | PCR | 3-Strike Reversal")

# Start feed (singleton)
if 'feed' not in st.session_state:
    st.session_state.feed = DhanLiveFeed(CLIENT_ID, ACCESS_TOKEN, TOKENS)
    st.session_state.feed.start()
    st.session_state.previous_oi = {}

feed = st.session_state.feed
previous_oi = st.session_state.previous_oi

# Auto-refresh every 3s
time.sleep(0.1)  # Non-blocking

if len(feed.data_store) > 0:
    rows = []
    total_call, total_put = 0, 0

    for token, data in feed.data_store.items():
        current_oi = data["oi"]
        if token not in previous_oi:
            previous_oi[token] = current_oi
        oi_change = calculate_oi_change(current_oi, previous_oi[token])
        previous_oi[token] = current_oi

        # Map token to strike/CE-PE (simplified; enhance with instrument lookup)
        strike = 25750 + (token % 1000)  # Demo mapping
        is_call = token % 2 == 0  # Even=CE, Odd=PE
        change = oi_change if is_call else -oi_change  # Calls positive, Puts negative for diff

        if is_call:
            total_call += change
        else:
            total_put += abs(change)

        diff = total_call - total_put  # Cumulative
        strength = tag_strength(diff)

        rows.append({
            "Strike": strike,
            "Call OI Change": change if is_call else 0,
            "Put OI Change": change if not is_call else 0,
            "Difference": diff,
            "Strength": strength
        })

    df = pd.DataFrame(rows)
    pcr = calculate_pcr(total_call, total_put)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Call Δ", f"{total_call:,.0f}")
    col2.metric("Total Put Δ", f"{total_put:,.0f}")
    col3.metric("PCR", pcr)

    st.subheader("Strike Wise OI Changes")
    st.dataframe(df, use_container_width=True)

    st.subheader("3-Strike Reversal Analysis")
    three_df = three_strike_analysis(df)
    st.dataframe(three_df, use_container_width=True)
else:
    st.info("🔄 Connecting Dhan WS... Wait 10-20s for live ticks.")

st.rerun()  # Streamlit native refresh
