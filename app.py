import streamlit as st
import pandas as pd
from dhanhq import marketfeed
import requests
import time
from datetime import datetime
import asyncio

# --- 1. CREDENTIALS ---
CLIENT_ID = "1106476940"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzY5NjE1NzAyLCJpYXQiOjE3Njk1MjkzMDIsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA2NDc2OTQwIn0.MygCo_b-l1khRfC-V8_iYvqbeykHy4upKbdghs8ElQxBegN-wMDKfUwNNDyUH0ZQK8_YYZeQULFICMhoYsxTWA"
TG_TOKEN = "8289933882:AAGgTyAhFHYzlKbZ_0rvH8GztqXeTB6P-yQ"
TG_CHAT_ID = "2115666034"

# --- 2. THE MISSING PIECE: OPTION SELECTION LOGIC ---
def get_best_option(name, ltp, step):
    atm = round(ltp / step) * step
    # Safe Trading కోసం 1 Step ITM (In The Money) సూచిస్తున్నాను
    call_itm = atm - step
    put_itm = atm + step
    return atm, call_itm, put_itm

# --- 3. TELEGRAM ALERT WITH HUMAN TOUCH ---
def send_ai_alert(title, index, price, logic, strike, emoji):
    if 'alert_history' not in st.session_state:
        st.session_state.alert_history = {}
    
    now = time.time()
    alert_key = f"{index}_{title}"
    
    # 5 నిమిషాల గ్యాప్ ఉంటేనే మెసేజ్ పంపుతుంది
    if alert_key not in st.session_state.alert_history or (now - st.session_state.alert_history[alert_key] > 300):
        msg = (f"{emoji} *{title} ALERT*\n\n"
               f"📊 *Index:* {index} | 💰 *LTP:* {price}\n"
               f"🎯 *Suggested Strike:* {strike}\n"
               f"🧠 *Mentor Logic:* {logic}\n"
               f"⏰ {datetime.now().strftime('%H:%M:%S')}")
        
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        try:
            requests.post(url, data={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
            st.session_state.alert_history[alert_key] = now
        except: pass

# --- 4. 7-TRIGGER ENGINE (REFINED) ---
def process_market_intel(sid, ltp):
    config = {"13": ("NIFTY", 50), "25": ("BANKNIFTY", 100), "51": ("SENSEX", 100)}
    if str(sid) not in config: return
    
    name, step = config[str(sid)]
    atm, itm_c, itm_p = get_best_option(name, ltp, step)
    
    # Logic: Big Players Momentum
    if ltp > (atm + (step * 0.7)):
        send_ai_alert("🚀 MOMENTUM", name, ltp, "పెద్ద ప్లేయర్స్ ఎంటర్ అయ్యారు. బ్రేక్ అవుట్ వచ్చే అవకాశం ఉంది!", f"{itm_c} CE", "🐘")
    
    # Logic: Trap/Fake Detection
    elif ltp > atm and ltp < (atm + 10):
        send_ai_alert("🛑 TRAP WARNING", name, ltp, "ఇది ఫేక్ మూవ్ లా కనిపిస్తోంది. తొందరపడి ఎంట్రీ తీసుకోవద్దు!", "WAIT", "⚠️")

    # Logic: Resistance Reversal
    if ltp >= (atm + step - 5):
        send_ai_alert("📉 REVERSAL", name, ltp, "రెసిస్టెన్స్ లెవల్ కి వచ్చాం. ఇక్కడ నుండి కిందకి పడొచ్చు.", f"{itm_p} PE", "🔄")

# --- 5. WEBSOCKET HANDLERS ---
async def on_message(instance, message):
    if 'last_price' in message:
        ltp = message['last_price']
        sid = message['security_id']
        process_market_intel(sid, ltp)
        # UI Update
        st.session_state.live_price = f"{sid}: {ltp}"

async def on_connect(instance):
    st.success("✅ AI Mentor is now Live and Watching the Markets!")

# --- 6. STREAMLIT UI ---
st.title("🏹 Venu's Elite AI Trading System")
st.markdown("---")

if 'live_price' not in st.session_state:
    st.session_state.live_price = "Waiting for data..."

st.metric("Live Ticker", st.session_state.live_price)

with st.sidebar:
    st.header("🛡️ Risk Control")
    st.info("ఒకవేళ వరుసగా 2 స్టాప్ లాస్ లు హిట్ అయితే, ఈరోజుకి ట్రేడింగ్ ఆపేయండి. రేపు మళ్ళీ చూద్దాం.")

instruments = [(1, "13"), (1, "25"), (6, "51")]

if st.button("🚀 Connect to Market Feed"):
    feed = marketfeed.DhanFeed(CLIENT_ID, ACCESS_TOKEN, instruments, 
                               marketfeed.Ticker, on_connect=on_connect, 
                               on_message=on_message)
    feed.run_forever()

