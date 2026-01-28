import streamlit as st
import pandas as pd
from dhanhq import marketfeed
import requests
import time
from datetime import datetime

# --- 1. CONFIG & AUTH ---
st.set_page_config(layout="wide", page_title="Venu's AI WebSocket Bot")

try:
    CLIENT_ID = st.secrets["DHAN_CLIENT_ID"]
    ACCESS_TOKEN = st.secrets["DHAN_ACCESS_TOKEN"]
    TG_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    TG_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
except:
    st.error("Secrets missing in Streamlit Settings!")
    st.stop()

# అలర్ట్స్ పదే పదే రాకుండా ఉండేందుకు
if 'alert_history' not in st.session_state:
    st.session_state.alert_history = {}

# --- 2. TELEGRAM SENDER ---
def send_tg_alert(title, msg):
    now = time.time()
    if title not in st.session_state.alert_history or (now - st.session_state.alert_history[title] > 300):
        full_msg = f"⚡ *{title} ALERT*\n\n{msg}\n\n⏰ {datetime.now().strftime('%H:%M:%S')}"
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TG_CHAT_ID, "text": full_msg, "parse_mode": "Markdown"})
        st.session_state.alert_history[title] = now

# --- 3. 7-TRIGGER LOGIC ENGINE ---
def process_logic(ltp, sid):
    # ID మ్యాపింగ్
    name = "NIFTY" if sid == 13 else "BANKNIFTY" if sid == 25 else "SENSEX"
    step = 50 if sid == 13 else 100
    atm = round(ltp / step) * step
    
    # Logic 1: Big Players & Logic 2: Price Action
    # (ఇక్కడ WebSocket లో వచ్చే వాల్యూమ్/OI డేటాను బట్టి కండిషన్స్ మారుతాయి)
    if ltp > (atm + (step * 0.8)):
        send_tg_alert("🐘 BIG PLAYERS", f"Index: {name}\nPrice: {ltp}\nLogic: Institutional Buying at {atm}!")

    # Logic 3: Fake Move Detection
    # ప్రైస్ పెరిగినా స్ట్రెంత్ లేకపోతే
    if ltp > atm and ltp < (atm + 10):
        send_tg_alert("⚠️ FAKE MOVE", f"Index: {name}\nPrice: {ltp}\nLogic: Breakout లో బలం లేదు, జాగ్రత్త!")

    # Logic 4: Reversal Alert
    resistance = atm + step
    if ltp >= (resistance - 5):
        send_tg_alert("🔄 REVERSAL", f"Index: {name}\nPrice: {ltp}\nLogic: Resistance దగ్గర రివర్స్ అయ్యే ఛాన్స్. PE చూడండి.")

    # Logic 5: Target Hit
    target = atm + (step * 1.5)
    if ltp >= target:
        send_tg_alert("🎯 TARGET HIT", f"Index: {name}\nPrice: {ltp}\nLogic: టార్గెట్ రీచ్ అయ్యింది, ప్రాఫిట్ బుక్ చేయండి!")

    # Logic 6: Best Strike Suggestion
    strike = f"{atm - step} CE" if ltp > atm else f"{atm + step} PE"
    
    return {"name": name, "strike": strike, "atm": atm}

# --- 4. WEBSOCKET CALLBACKS ---
async def on_message(instance, message):
    if 'last_price' in message:
        ltp = message['last_price']
        sid = message['security_id']
        
        # రన్ లాజిక్
        result = process_logic(ltp, sid)
        
        # UI అప్‌డేట్ (Streamlit లో WebSocket UI కి చిన్న లిమిటేషన్ ఉంటుంది)
        st.write(f"📡 {result['name']} Live: {ltp} | Strike: {result['strike']}")

async def on_connect(instance):
    st.success("✅ WebSocket Connected! Real-time scanning active.")

# --- 5. MAIN UI ---
st.title("🏹 Venu's Elite WebSocket AI Assistant")

# Risk Manager (Logic 7)
with st.sidebar:
    st.header("💰 Risk Manager")
    cap = st.number_input("Capital", value=50000)
    st.write(f"Max Risk: ₹{cap * 0.02}")
    st.info("Human Assist: ఈరోజు 3 ట్రేడ్స్ దాటితే ఆపేయండి.")

# Instruments to track
instruments = [(marketfeed.NSE_INDEX, "13"), (marketfeed.NSE_INDEX, "25")]

if st.button("🚀 Start Live WebSocket Feed"):
    feed = marketfeed.DhanFeed(CLIENT_ID, ACCESS_TOKEN, instruments, 
                               marketfeed.Ticker, on_connect=on_connect, 
                               on_message=on_message)
    feed.run_forever()
