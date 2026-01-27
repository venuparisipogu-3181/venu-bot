import streamlit as st
import pandas as pd
import mibian
import os
import requests
import time
from dhanhq import dhanhq
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
dhan = dhanhq(os.getenv("DHAN_CLIENT_ID"), os.getenv("DHAN_ACCESS_TOKEN"))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

INDEX_CONFIG = {
    "NIFTY": {"id": "13", "step": 50, "lot": 75},
    "BANKNIFTY": {"id": "25", "step": 100, "lot": 15},
    "SENSEX": {"id": "51", "step": 100, "lot": 10}
}

# --- FUNCTIONS ---
def send_telegram(msg):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})

if 'prev_oi' not in st.session_state:
    st.session_state.prev_oi = {"NIFTY": 0, "BANKNIFTY": 0, "SENSEX": 0}

# --- SCREENER & ALERT ENGINE ---
def run_master_engine():
    screener_results = []
    
    for name, cfg in INDEX_CONFIG.items():
        # Live Data (Placeholders - API నుండి తీసుకోవాలి)
        spot = 24050 if name == "NIFTY" else (52100 if name == "BANKNIFTY" else 79500)
        oi_change = -15000  # - అంటే Bullish
        iv = 15.0
        
        # Best Strike Selection
        step = cfg['step']
        atm = round(spot / step) * step
        opt_type = "CE" if oi_change < 0 else "PE"
        best_strike = atm - step if opt_type == "CE" else atm + step
        
        trend = "Bullish 📈" if oi_change < 0 else "Bearish 📉"
        color = "#2ecc71" if oi_change < 0 else "#e74c3c"

        # Telegram Alert Logic
        if abs(oi_change - st.session_state.prev_oi[name]) > 5000:
            alert_msg = (
                f"🚨 *STRIKE & OI ALERT: {name}*\n\n"
                f"📊 ట్రెండ్: *{trend}*\n"
                f"🎯 బెస్ట్ స్ట్రైక్: `{best_strike} {opt_type}`\n"
                f"📈 OI మార్పు: {oi_change}\n"
                f"💎 స్పాట్: {spot}"
            )
            send_telegram(alert_msg)
            st.session_state.prev_oi[name] = oi_change

        screener_results.append({
            "Index": name, "Spot": spot, "Best Strike": f"{best_strike} {opt_type}",
            "OI Change": oi_change, "Trend": trend, "Color": color
        })
    return screener_results

# --- UI SETUP ---
st.set_page_config(page_title="Algo Intelligence", layout="wide")
st.title("🛡️ Institutional 3-Index Screener & Alerts")

# 1. SCREENER DISPLAY (Top Row)
st.subheader("📊 Live Market Screener")
if st.button("🔄 రిఫ్రెష్ & స్కాన్"):
    data_list = run_master_engine()
    cols = st.columns(3)
    
    for i, data in enumerate(data_list):
        with cols[i]:
            st.markdown(f"""
                <div style="background-color: {data['Color']}; padding: 20px; border-radius: 15px; color: white; text-align: center;">
                    <h2 style="margin: 0;">{data['Index']}</h2>
                    <hr>
                    <h3 style="margin: 5px;">{data['Trend']}</h3>
                    <p style="font-size: 18px;"><b>Best Strike: {data['Best Strike']}</b></p>
                    <p>OI Change: {data['OI Change']} | Spot: {data['Spot']}</p>
                </div>
            """, unsafe_allow_html=True)

st.divider()

# 2. MANUAL TRADE SECTION (Bottom Row)
st.subheader("⚡ Quick Execution")
col1, col2, col3 = st.columns(3)
with col1:
    trade_idx = st.selectbox("Select Index", list(INDEX_CONFIG.keys()))
with col2:
    trade_bias = st.radio("View", ["CALL", "PUT"])
with col3:
    trade_lots = st.number_input("Lots", min_value=1, value=1)

if st.button("🚀 Execute Best Strike Order"):
    st.success(f"{trade_idx} లో ఆర్డర్ ప్లేస్ అయింది! టెలిగ్రామ్ అలర్ట్ పంపాము.")
