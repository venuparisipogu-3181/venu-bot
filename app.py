import streamlit as st
import pandas as pd
import mibian
import os
import requests
from dhanhq import dhanhq
from dotenv import load_dotenv

# .env ఫైల్ నుండి కీస్ లోడ్ చేయడం
load_dotenv()

# --- CONFIGURATION ---
dhan = dhanhq(os.getenv("DHAN_CLIENT_ID"), os.getenv("DHAN_ACCESS_TOKEN"))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

INDEX_CONFIG = {
    "NIFTY": {"id": "13", "step": 50},
    "BANKNIFTY": {"id": "25", "step": 100},
    "SENSEX": {"id": "51", "step": 100}
}

# --- TELEGRAM ALERT FUNCTION ---
def send_telegram_alert(msg):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        try:
            requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        except Exception as e:
            st.error(f"Telegram Alert Error: {e}")

# --- OI TRACKER (గత OI ని గుర్తుంచుకోవడానికి) ---
if 'prev_oi_data' not in st.session_state:
    st.session_state.prev_oi_data = {"NIFTY": 0, "BANKNIFTY": 0, "SENSEX": 0}

# --- ALERT ENGINE ---
def check_market_and_alert():
    for name, cfg in INDEX_CONFIG.items():
        # ఇక్కడ నిజానికి Dhan API నుండి Live Data తీసుకోవాలి
        # ప్రస్తుతానికి ఉదాహరణ డేటా:
        spot_price = 24050 if name == "NIFTY" else 52100
        current_oi_change = -20000  # - అంటే Short Covering (Bullish)
        iv = 15.5

        # 1. Best Strike Selection (Delta 0.6 Logic)
        step = cfg['step']
        atm = round(spot_price / step) * step
        
        if current_oi_change < 0:
            best_strike = atm - step # ITM Call
            option_type = "CE"
            trend_label = "🚀 బుల్లిష్ (Short Covering)"
        else:
            best_strike = atm + step # ITM Put
            option_type = "🔥 బేరిష్ (Short Build-up)"
            trend_label = "Bearish"

        # 2. అలర్ట్ లాజిక్: OI లో మార్పు వచ్చినప్పుడు లేదా కొత్త స్ట్రైక్ దొరికినప్పుడు
        if abs(current_oi_change - st.session_state.prev_oi_data[name]) > 2000:
            alert_text = (
                f"🚨 *SMART ALERT: {name}*\n\n"
                f"📊 *ట్రెండ్:* {trend_label}\n"
                f"🎯 *బెస్ట్ స్ట్రైక్:* `{best_strike} {option_type}`\n"
                f"📈 *OI మార్పు:* {current_oi_change}\n"
                f"💎 *స్పాట్ ధర:* {spot_price}\n"
                f"📉 *IV:* {iv}\n\n"
                f"📢 _సూచన: వెంటనే చార్ట్ చెక్ చేసి ఎంట్రీ ప్లాన్ చేయండి!_"
            )
            send_telegram_alert(alert_text)
            st.session_state.prev_oi_data[name] = current_oi_change

# --- UI DISPLAY ---
st.title("🛡️ OI & Strike Intelligence Bot")

if st.button("🔴 లైవ్ మానిటరింగ్ స్టార్ట్ చేయి"):
    st.write("మార్కెట్ ని గమనిస్తున్నాను... ట్రెండ్ మారగానే మీకు టెలిగ్రామ్ మెసేజ్ వస్తుంది.")
    check_market_and_alert()
