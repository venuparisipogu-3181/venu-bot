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
dhan = dhanhq(os.getenv("1106476940"), os.getenv("eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzY5NjE1NzAyLCJpYXQiOjE3Njk1MjkzMDIsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA2NDc2OTQwIn0.MygCo_b-l1khRfC-V8_iYvqbeykHy4upKbdghs8ElQxBegN-wMDKfUwNNDyUH0ZQK8_YYZeQULFICMhoYsxTWA"))
TELEGRAM_TOKEN = os.getenv("8289933882:AAGgTyAhFHYzlKbZ_0rvH8GztqXeTB6P-yQ")
TELEGRAM_CHAT_ID = os.getenv("2115666034")

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
import streamlit as st
import streamlit.components.v1 as components

# 1. చార్ట్ ఫంక్షన్ - ఇక్కడ symbol ని డైరెక్ట్ గా వాడుతున్నాం
def display_tradingview_chart(symbol_name):
    tradingview_html = f"""
    <div class="tradingview-widget-container" style="height:800px; width:100%;">
      <div id="tradingview_full_widget" style="height:800px;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
        "autosize": true,
        "symbol": "{symbol_name}",  // ఇక్కడ కరెక్ట్ సింబల్ వస్తుంది
        "interval": "5",
        "timezone": "Asia/Kolkata",
        "theme": "dark",
        "style": "1",
        "locale": "in",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "withdateranges": true,
        "hide_side_toolbar": false,
        "allow_symbol_change": true,
        "details": true,
        "container_id": "tradingview_full_widget"
      }});
      </script>
    </div>
    """
    components.html(tradingview_html, height=820)

# --- UI సెక్షన్ ---
st.divider()
st.subheader("📈 Live Market Chart")

# 2. ఇండెక్స్ సెలెక్షన్
chart_choice = st.selectbox(
    "చార్ట్ చూడాల్సిన ఇండెక్స్ సెలెక్ట్ చేయండి:", 
    ["NIFTY 50", "BANKNIFTY", "SENSEX"]
)

# 3. కరెక్ట్ సింబల్ ని అసైన్ చేయడం (IMPORTANT STEP)
if chart_choice == "NIFTY 50":
    target_symbol = "NSE:NIFTY"
elif chart_choice == "BANKNIFTY":
    target_symbol = "NSE:BANKNIFTY"
elif chart_choice == "SENSEX":
    target_symbol = "BSE:SENSEX"
else:
    target_symbol = "NSE:NIFTY" # డిఫాల్ట్ గా నిఫ్టీ

# 4. చార్ట్ ని పిలవడం (Calling the function with the target_symbol)
display_tradingview_chart(target_symbol)
