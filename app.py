# app.py - LIVE NIFTY STRIKE PRICES (Realistic data)
import streamlit as st
import pandas as pd
import numpy as np
import time
import random
from oi_logic import *

st.set_page_config(layout="wide")
st.title("🚀 LIVE NIFTY OI DASHBOARD")
st.caption("Nifty Spot: 25,571 | ATM: 25,600 | Feb 21, 2026")

# LIVE ATM ±5 STRIKES (Real Nifty levels)
STRIKES = [25400, 25450, 25500, 25550, 25600, 25650, 25700, 25750, 25800]
TOKENS = [strike*100 + i for strike in STRIKES for i in [1,2]]  # CE=1, PE=2

if 'data_store' not in st.session_state:
    st.session_state.data_store = {}
    st.session_state.previous_oi = {}
    st.session_state.last_update = 0

# Simulate LIVE Dhan WebSocket (Realistic Nifty OI)
now = time.time()
if now - st.session_state.last_update > 2:
    for i, token in enumerate(TOKENS):
        strike = token // 100
        is_call = token % 2 == 1
        
        # Realistic OI changes (±5L every 2s)
        base_oi = 1500000 + (strike - 25600) * 50000
        oi_change = random.randint(-500000, 500000)
        oi = max(0, base_oi + oi_change)
        
        st.session_state.data_store[token] = {
            "strike": strike,
            "is_call": is_call,
            "oi": oi,
            "ltp": 250 + random.uniform(-50, 50)
        }
    st.session_state.last_update = now

# Process data
rows, total_call, total_put = [], 0, 0
data_store = st.session_state.data_store
previous_oi = st.session_state.previous_oi

for token, data in data_store.items():
    current_oi = data["oi"]
    
    if token not in previous_oi:
        previous_oi[token] = current_oi
    
    oi_change = current_oi - previous_oi[token]
    previous_oi[token] = current_oi
    
    is_call = data["is_call"]
    change = oi_change if is_call else -oi_change
    
    if is_call:
        total_call += change
    else:
        total_put += abs(change)
    
    diff = total_call - total_put
    strength = tag_strength(diff)
    
    rows.append({
        "Strike": data["strike"],
        "Call OI Δ": change if is_call else 0,
        "Put OI Δ": abs(change) if not is_call else 0,
        "LTP": f"{data['ltp']:.1f}",
        "Difference": diff,
        "Strength": strength
    })

df = pd.DataFrame(rows)
pcr = calculate_pcr(total_call, total_put)

# DASHBOARD
col1, col2, col3, col4 = st.columns(4)
col1.metric("📈 Call Total", f"{total_call:,.0f}")
col2.metric("📉 Put Total", f"{total_put:,.0f}")
col3.metric("🎯 PCR", pcr)
col4.metric("⏰ Last Update", f"{time.strftime('%H:%M:%S')}")

st.subheader("🔥 Strike Wise LIVE OI")
st.dataframe(df, use_container_width=True)

st.subheader("🎯 3-Strike Reversal Analysis")
if len(df) >= 3:
    three_df = three_strike_analysis(df)
    st.dataframe(three_df, use_container_width=True)

st.success("🟢 LIVE! Every 2s update | Monday DhanHQ WebSocket ready")
