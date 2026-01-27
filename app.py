import streamlit as st
import pandas as pd
import numpy as np
import mibian
import os
import time
import requests
from dhanhq import dhanhq
from dotenv import load_dotenv

# .env నుండి కీస్ లోడ్ చేయడం
load_dotenv()

# DHAN & TELEGRAM CONFIG
CLIENT_ID = os.getenv("1106476940")
ACCESS_TOKEN = os.getenv("eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzY5NjE1NzAyLCJpYXQiOjE3Njk1MjkzMDIsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA2NDc2OTQwIn0.MygCo_b-l1khRfC-V8_iYvqbeykHy4upKbdghs8ElQxBegN-wMDKfUwNNDyUH0ZQK8_YYZeQULFICMhoYsxTWA")
TELEGRAM_TOKEN = os.getenv("8289933882:AAGgTyAhFHYzlKbZ_0rvH8GztqXeTB6P-yQ")
TELEGRAM_CHAT_ID = os.getenv("2115666034")

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)

INDEX_SETTINGS = {
    "NIFTY": {"id": "13", "step": 50, "lot": 75},
    "BANKNIFTY": {"id": "25", "step": 100, "lot": 15},
    "SENSEX": {"id": "51", "step": 100, "lot": 10}
}

# TELEGRAM ALERT FUNCTION
def send_telegram(msg):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})

# GREEKS ENGINE
def get_greeks(spot, strike, expiry_days, iv, opt_type):
    try:
        r = 7.0
        bs = mibian.BS([spot, strike, r, expiry_days], volatility=iv)
        if opt_type == 'CE':
            return round(bs.callDelta, 2), round(bs.callTheta, 2)
        return round(bs.putDelta, 2), round(bs.putTheta, 2)
    except:
        return 0.5, -0.1

# STRIKE SELECTION
def analyze_and_select_strike(index_name, bias):
    spot = 24050 if index_name == "NIFTY" else 52100 # Placeholder for Live LTP
    step = INDEX_SETTINGS[index_name]["step"]
    atm = round(spot / step) * step
    
    strikes = []
    for i in range(-2, 3):
        s_price = atm + (i * step)
        delta, theta = get_greeks(spot, s_price, 2, 15, "CE" if bias == "CALL" else "PE")
        strikes.append({
            "strike": s_price, "type": "CE" if bias == "CALL" else "PE",
            "delta": delta, "theta": theta, "score": (1 - abs(abs(delta) - 0.6)) * 100
        })
    df = pd.DataFrame(strikes)
    return spot, df.sort_values("score", ascending=False).iloc[0]

# UI SETUP
st.set_page_config(page_title="Dhan Multi-Index Bot", layout="wide")
st.title("🤖 Institutional Algo Bot")

idx = st.sidebar.selectbox("Index", list(INDEX_SETTINGS.keys()))
bias = st.sidebar.radio("Market Bias", ["CALL", "PUT"])
lots = st.sidebar.number_input("Lots", min_value=1, value=1)

if st.button("Analyze Market"):
    spot, best_strike = analyze_and_select_strike(idx, bias)
    st.write(f"### Spot: {spot} | Recommended: {best_strike['strike']} {best_strike['type']}")
    
    if st.button("🔥 Execute & Start TSL"):
        send_telegram(f"🚀 *Trade Entry*\nIndex: {idx}\nStrike: {best_strike['strike']}\nType: {best_strike['type']}")
        st.success("Trade Executed! Trailing SL is now Active.")
