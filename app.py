import streamlit as st
import pandas as pd
from dhanhq import marketfeed
import requests
import time
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Venu's AI Mentor Bot")

# Credentials
CLIENT_ID = "1106476940"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzY5NzAxNTY0LCJpYXQiOjE3Njk2MTUxNjQsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA2NDc2OTQwIn0.w-bpRUgKqGt4BtWGr1YRxfvaJhLy8mTFiNln3qUU4DEakeVlKlPfIfAu1XDmpmJr12uByHC4EhK0pa32Akmg9A"
TG_TOKEN = "8289933882:AAGgTyAhFHYzlKbZ_0rvH8GztqXeTB6P-yQ"
TG_CHAT_ID = "2115666034"

# Alert History
if 'alert_history' not in st.session_state:
    st.session_state.alert_history = {}

# --- 2. TELEGRAM ENGINE ---
def send_ai_alert(title, index, price, logic, strike, emoji):
    now = time.time()
    alert_key = f"{index}_{title}"
    
    if alert_key not in st.session_state.alert_history or (now - st.session_state.alert_history[alert_key] > 300):
        msg = (f"{emoji} *{title} ALERT*\n\n"
               f"📊 *Index:* {index} | 💰 *LTP:* {price}\n"
               f"🎯 *Strike:* {strike}\n"
               f"🧠 *Logic:* {logic}\n"
               f"⏰ {datetime.now().strftime('%H:%M:%S')}")
        
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        try:
            requests.post(url, data={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
            st.session_state.alert_history[alert_key] = now
        except: pass

# --- 3. THE 7-TRIGGER AI BRAIN ---
def process_market_intel(sid, ltp):
    config = {"13": ("NIFTY", 50), "25": ("BANKNIFTY", 100), "51": ("SENSEX", 100)}
    sid_str = str(sid)
    if sid_str not in config: return
    
    name, step = config[sid_str]
    atm = round(ltp / step) * step
    
    # Logic 1: Big Players Momentum
    if ltp > (atm + (step * 0.7)):
        send_ai_alert("🚀 MOMENTUM", name, ltp, "పెద్ద ప్లేయర్స్ ఎంటర్ అయ్యారు. బ్రేక్ అవుట్ వచ్చే అవకాశం ఉంది!", f"{atm-step} CE", "🐘")
    
    # Logic 2: Trap Detection
    elif ltp > atm and ltp < (atm + (step * 0.1)):
        send_ai_alert("🛑 TRAP WARNING", name, ltp, "ఇది ఫేక్ మూవ్ లా కనిపిస్తోంది. జాగ్రత్త!", "WAIT", "⚠️")

    # Logic 3: Reversal (Resistance Zone)
    if ltp >= (atm + step - 10):
        send_ai_alert("📉 REVERSAL", name, ltp, "రెసిస్టెన్స్ దగ్గరకు వచ్చాం. ప్రాఫిట్ బుక్ లేదా PE చూడండి.", f"{atm+step} PE", "🔄")

# --- 4. WEBSOCKET CALLBACKS (FIXED FOR SDK) ---
def on_message(instance, message):
    if 'last_price' in message:
        ltp = message['last_price']
        sid = message['security_id']
        process_market_intel(sid, ltp)
        # Display live ticks in console/UI
        print(f"Live Update: {sid} -> {ltp}")

def on_connect(instance):
    print("✅ Connected to Dhan WebSocket!")

# --- 5. UI & EXECUTION ---
st.title("🏹 Venu's Elite AI Mentor System")
st.markdown("---")

with st.sidebar:
    st.header("🛡️ Human Assistance")
    st.info("సలహా: వరుసగా 2 ఎస్.ఎల్ (SL) హిట్ అయితే ఈరోజుకి ట్రేడింగ్ ఆపేయండి.")
    st.warning("Dhan Access Token కేవలం 24 గంటలు మాత్రమే పనిచేస్తుంది.")

# Instruments: (Segment, SecurityID)
instruments = [(1, "13"), (1, "25"), (6, "51")]

if st.button("🚀 Start Live Monitoring"):
    try:
        # Dhan SDK New Format
        feed = marketfeed.DhanFeed(CLIENT_ID, 
                                   ACCESS_TOKEN, 
                                   instruments, 
                                   marketfeed.Ticker)
        
        # Callbacks assignment (Fix for TypeError)
        feed.on_connect = on_connect
        feed.on_message = on_message
        
        st.success("WebSocket కనెక్ట్ అయ్యింది! మీ టెలిగ్రామ్ అలర్ట్స్ గమనిస్తూ ఉండండి.")
        feed.run_forever()
        
    except Exception as e:
        st.error(f"Error: {e}")
