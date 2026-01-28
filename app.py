import streamlit as st
import pandas as pd
from dhanhq import marketfeed
import requests
import time
from datetime import datetime
import threading

# --- 1. CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Venu's AI Mentor Bot")

CLIENT_ID = "1106476940"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzY5NjE1NzAyLCJpYXQiOjE3Njk1MjkzMDIsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA2NDc2OTQwIn0.MygCo_b-l1khRfC-V8_iYvqbeykHy4upKbdghs8ElQxBegN-wMDKfUwNNDyUH0ZQK8_YYZeQULFICMhoYsxTWA"
TG_TOKEN = "8289933882:AAGgTyAhFHYzlKbZ_0rvH8GztqXeTB6P-yQ"
TG_CHAT_ID = "2115666034"

# --- 2. TELEGRAM & LOGIC ---
def send_ai_alert(title, index, price, logic, strike, emoji):
    # Alert history logic
    if 'alert_history' not in st.session_state: st.session_state.alert_history = {}
    now = time.time()
    alert_key = f"{index}_{title}"
    
    if alert_key not in st.session_state.alert_history or (now - st.session_state.alert_history[alert_key] > 300):
        msg = f"{emoji} *{title}*\n\n📊 {index}: {price}\n🎯 Strike: {strike}\n🧠 {logic}"
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        st.session_state.alert_history[alert_key] = now

def process_market_intel(sid, ltp):
    config = {"13": ("NIFTY", 50), "25": ("BANKNIFTY", 100), "51": ("SENSEX", 100)}
    sid_str = str(sid)
    if sid_str in config:
        name, step = config[sid_str]
        atm = round(ltp / step) * step
        if ltp > (atm + (step * 0.7)):
            send_ai_alert("🚀 MOMENTUM", name, ltp, "Big Players Buying!", f"{atm-step} CE", "🐘")

# --- 3. CALLBACKS ---
def on_message(instance, message):
    if 'last_price' in message:
        process_market_intel(message['security_id'], message['last_price'])

def on_connect(instance):
    print("✅ Connected!")

# --- 4. THE FIX: RUN FEED IN THREAD ---
def run_dhan_feed():
    instruments = [(1, "13"), (1, "25"), (6, "51")]
    feed = marketfeed.DhanFeed(CLIENT_ID, ACCESS_TOKEN, instruments, marketfeed.Ticker)
    feed.on_connect = on_connect
    feed.on_message = on_message
    feed.run_forever()

# --- 5. UI ---
st.title("🏹 Venu's Elite AI System")

if st.button("🚀 Start Monitoring"):
    # ఇక్కడ త్రెడ్డింగ్ వాడుతున్నాం, దీనివల్ల 'Event Loop' ఎర్రర్ రాదు
    t = threading.Thread(target=run_dhan_feed)
    t.start()
    st.success("బాట్ బ్యాక్‌గ్రౌండ్‌లో రన్ అవుతోంది! టెలిగ్రామ్ అలర్ట్స్ చూడండి.")
