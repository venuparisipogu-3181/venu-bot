import streamlit as st
import pandas as pd
from dhanhq import marketfeed
import requests
import time
from datetime import datetime
import asyncio

# --- 1. CONFIGURATION & SECRETS ---
st.set_page_config(layout="wide", page_title="Venu's AI WebSocket")

try:
    CLIENT_ID = st.secrets["1106476940"]
    ACCESS_TOKEN = st.secrets["eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzY5NjE1NzAyLCJpYXQiOjE3Njk1MjkzMDIsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA2NDc2OTQwIn0.MygCo_b-l1khRfC-V8_iYvqbeykHy4upKbdghs8ElQxBegN-wMDKfUwNNDyUH0ZQK8_YYZeQULFICMhoYsxTWA"]
    TG_TOKEN = st.secrets["https://github.com/twopirllc/pandas-ta/archive/refs/heads/master.zip"]
    TG_CHAT_ID = st.secrets["2115666034"]
except Exception as e:
    st.error("Secrets missing! Please check Streamlit Settings.")
    st.stop()

# Alert Control (5 నిమిషాల గ్యాప్ కోసం)
if 'alert_history' not in st.session_state:
    st.session_state.alert_history = {}

# --- 2. TELEGRAM ALERT ENGINE ---
def send_ai_alert(title, index, price, logic, strike, emoji):
    now = time.time()
    alert_key = f"{index}_{title}"
    
    if alert_key not in st.session_state.alert_history or (now - st.session_state.alert_history[alert_key] > 300):
        msg = (f"{emoji} *{title} ALERT*\n\n"
               f"📊 *Index:* {index}\n"
               f"💰 *LTP:* {price}\n"
               f"🎯 *Strike:* {strike}\n"
               f"🧠 *Mentor Logic:* {logic}\n"
               f"⏰ {datetime.now().strftime('%H:%M:%S')}")
        
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        try:
            requests.post(url, data={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
            st.session_state.alert_history[alert_key] = now
        except:
            pass

# --- 3. THE 7-TRIGGER AI LOGIC ---
def analyze_and_trigger(sid, ltp):
    # Mapping Data
    config = {
        "13": {"name": "NIFTY", "step": 50},
        "25": {"name": "BANKNIFTY", "step": 100},
        "51": {"name": "SENSEX", "step": 100}
    }
    
    info = config.get(str(sid))
    if not info: return
    
    name = info["name"]
    step = info["step"]
    atm = round(ltp / step) * step
    res = atm + step
    
    # Logic 1: Big Players (Momentum Check)
    if ltp > (atm + (step * 0.7)):
        send_ai_alert("🐘 BIG PLAYERS", name, ltp, "ఇన్స్టిట్యూషన్స్ కొంటున్నారు! స్ట్రాంగ్ మొమెంటం ఉంది.", f"{atm} CE", "🚀")
    
    # Logic 2: Fake Move (Weak Breakout)
    elif ltp > atm and ltp < (atm + (step * 0.1)):
        send_ai_alert("⚠️ FAKE MOVE", name, ltp, "ధర పెరిగినా బలం లేదు. ఇది ట్రాప్ అయ్యే ఛాన్స్ ఉంది!", "WAIT", "🛑")

    # Logic 3: Reversal (Resistance Zone)
    if ltp >= (res - 10):
        send_ai_alert("🔄 REVERSAL", name, ltp, "రెసిస్టెన్స్ దగ్గరకు వచ్చాం. ఇక్కడ నుండి మార్కెట్ రివర్స్ అవ్వొచ్చు.", f"{atm+step} PE", "📉")

    # Logic 4: Target Hit
    target = atm + (step * 1.5)
    if ltp >= target:
        send_ai_alert("🎯 TARGET HIT", name, ltp, "ఈరోజు సెట్ చేసిన టార్గెట్ లెవల్ రీచ్ అయ్యింది. ప్రాఫిట్ బుక్ చేయండి!", "EXIT", "🏆")

    # Return data for UI
    return {"name": name, "strike": f"{atm} CE/PE"}

# --- 4. WEBSOCKET CALLBACKS ---
async def on_message(instance, message):
    if 'last_price' in message:
        ltp = message['last_price']
        sid = message['security_id']
        
        # Run AI Mentoring
        intel = analyze_and_trigger(sid, ltp)
        if intel:
            st.write(f"📡 {intel['name']} Live: **{ltp}** | Suggestion: {intel['strike']}")

async def on_connect(instance):
    st.success("✅ NSE & BSE WebSocket Live! Scanning Markets...")

# --- 5. UI DASHBOARD ---
st.title("🏹 Venu's Elite Multi-Index Mentor")
st.markdown("---")

with st.sidebar:
    st.header("💰 Human Assistant")
    cap = st.number_input("Capital (₹)", value=50000)
    risk = cap * 0.02
    st.warning(f"రిస్క్ లిమిట్: ₹{risk}")
    st.info("సలహా: ఒకవేళ 2 ట్రేడ్స్ లాస్ అయితే, ఈరోజుకి సిస్టమ్ ఆపేయండి.")

# Instruments: (Segment_ID, Security_ID)
# 1 = NSE, 6 = BSE
instruments = [
    (1, "13"), # NIFTY
    (1, "25"), # BANKNIFTY
    (6, "51")  # SENSEX
]

if st.button("🚀 Start Live AI Monitoring"):
    feed = marketfeed.DhanFeed(CLIENT_ID, ACCESS_TOKEN, instruments, 
                               marketfeed.Ticker, on_connect=on_connect, 
                               on_message=on_message)
    feed.run_forever()
