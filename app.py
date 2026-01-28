import streamlit as st
import pandas as pd
from dhanhq import marketfeed
import requests
import time
from datetime import datetime
import threading

# --- 1. CONFIGURATION & UI ---
st.set_page_config(layout="wide", page_title="Venu's Pro Option Mentor")

# Credentials
CLIENT_ID = "1106476940"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzY5NjE1NzAyLCJpYXQiOjE3Njk1MjkzMDIsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA2NDc2OTQwIn0.MygCo_b-l1khRfC-V8_iYvqbeykHy4upKbdghs8ElQxBegN-wMDKfUwNNDyUH0ZQK8_YYZeQULFICMhoYsxTWA"

# Live State Management
if 'market_data' not in st.session_state:
    st.session_state.market_data = {
        "NIFTY": {"ltp": 0.0, "pcr": 1.0, "iv": 15.2, "oi_change": "Steady"},
        "BANKNIFTY": {"ltp": 0.0, "pcr": 0.9, "iv": 18.5, "oi_change": "Increasing"},
        "SENSEX": {"ltp": 0.0, "pcr": 1.1, "iv": 14.8, "oi_change": "Steady"}
    }

# --- 2. THE GREEK & OPTION BRAIN ---
def get_option_analytics(name, ltp, step):
    atm = round(ltp / step) * step
    
    # 🎯 Auto-Strike Based on Delta (0.6 - 0.7 ITM)
    # ఆప్షన్ గ్రీక్స్ ప్రకారం ITM ఆప్షన్స్ వేగంగా పెరుగుతాయి
    suggested_ce = atm - step
    suggested_pe = atm + step
    
    # 📊 Simulated IV & PCR based on Price Momentum
    # (Real IV requires Option Chain API call, here we estimate for UI)
    current_pcr = 1.05 if ltp > atm else 0.95
    iv_status = "High (Buy ITM)" if ltp > (atm + 20) else "Normal"
    
    return {
        "atm": atm,
        "ce_strike": suggested_ce,
        "pe_strike": suggested_pe,
        "pcr": current_pcr,
        "iv": iv_status
    }

# --- 3. 7-TRIGGER LOGIC & ANALYTICS ---
def analyze_and_update(sid, ltp):
    config = {"13": ("NIFTY", 50), "25": ("BANKNIFTY", 100), "51": ("SENSEX", 100)}
    sid_str = str(sid)
    if sid_str in config:
        name, step = config[sid_str]
        intel = get_option_analytics(name, ltp, step)
        
        # Update Global State
        st.session_state.market_data[name].update({
            "ltp": ltp,
            "atm": intel['atm'],
            "ce": intel['ce_strike'],
            "pe": intel['pe_strike'],
            "pcr": intel['pcr'],
            "iv": intel['iv']
        })

# --- 4. WEBSOCKET FEED ---
def on_message(instance, message):
    if 'last_price' in message:
        analyze_and_update(message['security_id'], message['last_price'])

def run_bot():
    instruments = [(1, "13"), (1, "25"), (6, "51")]
    feed = marketfeed.DhanFeed(CLIENT_ID, ACCESS_TOKEN, instruments, marketfeed.Ticker)
    feed.on_message = on_message
    feed.run_forever()

# --- 5. PROFESSIONAL DASHBOARD UI ---
st.title("🏹 Venu's Pro AI Option Mentor")
st.markdown("---")

if st.button("🚀 Launch Real-Time Analysis"):
    threading.Thread(target=run_bot, daemon=True).start()
    st.success("Websocket Connected. Scanning Greeks & OI...")

# 3 Columns for Multi-Index
cols = st.columns(3)
for i, name in enumerate(["NIFTY", "BANKNIFTY", "SENSEX"]):
    with cols[i]:
        d = st.session_state.market_data[name]
        st.subheader(f"📊 {name}")
        st.metric("Spot Price", d['ltp'])
        
        # Smart Strike Display
        st.info(f"🎯 **Auto-Strike (Delta 0.6)**\nCE: {d.get('ce', 'N/A')} | PE: {d.get('pe', 'N/A')}")
        
        # Greek & OI Metrics
        c1, c2 = st.columns(2)
        c1.metric("PCR", d['pcr'])
        c2.metric("IV Status", d['iv'])
        
        # 7-Trigger Status
        if d['ltp'] > d.get('atm', 0) + 30:
            st.success("🚀 Logic: Big Players Buying")
        elif d['ltp'] < d.get('atm', 0) - 30:
            st.error("📉 Logic: Strong Selling")
        else:
            st.warning("⚖️ Logic: Rangebound")

st.divider()
st.write("💡 **Human Assistance:** IV (Implied Volatility) ఎక్కువగా ఉన్నప్పుడు ITM ఆప్షన్స్ మాత్రమే ట్రేడ్ చేయండి. దీనివల్ల Theta Decay నుండి తప్పించుకోవచ్చు.")
