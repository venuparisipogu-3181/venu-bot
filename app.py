import streamlit as st
import pandas as pd
import mibian
import os
import requests
from dhanhq import dhanhq
import streamlit.components.v1 as components

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Algo Intelligence", layout="wide")

# Secrets/Env నుండి డేటా (GitHub లో అప్‌లోడ్ చేసేటప్పుడు జాగ్రత్త)
# గమనిక: వీటిని నేరుగా కోడ్‌లో కాకుండా Streamlit Secrets లో ఉంచడం మంచిది.
DHAN_CLIENT_ID = "1106476940"
DHAN_ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzY5NjE1NzAyLCJpYXQiOjE3Njk1MjkzMDIsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA2NDc2OTQwIn0.MygCo_b-l1khRfC-V8_iYvqbeykHy4upKbdghs8ElQxBegN-wMDKfUwNNDyUH0ZQK8_YYZeQULFICMhoYsxTWA"
TELEGRAM_TOKEN = "8289933882:AAGgTyAhFHYzlKbZ_0rvH8GztqXeTB6P-yQ"
TELEGRAM_CHAT_ID = "2115666034"

dhan = dhanhq(DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN)

INDEX_CONFIG = {
    "NIFTY 50": {"id": "13", "step": 50, "lot": 75, "tv_sym": "NSE:NIFTY"},
    "BANKNIFTY": {"id": "25", "step": 100, "lot": 15, "tv_sym": "NSE:BANKNIFTY"},
    "SENSEX": {"id": "51", "step": 100, "lot": 10, "tv_sym": "BSE:SENSEX"}
}

# --- 2. FUNCTIONS ---
def send_telegram(msg):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})

def display_tradingview_chart(symbol_name):
    tradingview_html = f"""
    <div class="tradingview-widget-container" style="height:800px; width:100%;">
      <div id="tradingview_full_widget" style="height:800px;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
        "autosize": true,
        "symbol": "{symbol_name}",
        "interval": "5",
        "timezone": "Asia/Kolkata",
        "theme": "dark", "style": "1", "locale": "in",
        "toolbar_bg": "#f1f3f6", "enable_publishing": false,
        "withdateranges": true, "hide_side_toolbar": false,
        "allow_symbol_change": true, "details": true,
        "container_id": "tradingview_full_widget"
      }});
      </script>
    </div>
    """
    components.html(tradingview_html, height=820)

if 'prev_oi' not in st.session_state:
    st.session_state.prev_oi = {"NIFTY 50": 0, "BANKNIFTY": 0, "SENSEX": 0}

# --- 3. SCREENER ENGINE ---
def run_master_engine():
    results = []
    for name, cfg in INDEX_CONFIG.items():
        # ఇక్కడ అసలు API డేటా కాల్స్ ఉండాలి
        spot = 24150 if "NIFTY" in name else (52200 if "BANK" in name else 80100)
        oi_change = -12000 # Sample Bullish OI
        
        atm = round(spot / cfg['step']) * cfg['step']
        opt_type = "CE" if oi_change < 0 else "PE"
        best_strike = atm - cfg['step'] if opt_type == "CE" else atm + cfg['step']
        trend = "Bullish 📈" if oi_change < 0 else "Bearish 📉"
        color = "#2ecc71" if oi_change < 0 else "#e74c3c"

        # Alert Logic
        if abs(oi_change - st.session_state.prev_oi[name]) > 5000:
            msg = f"🚨 *OI ALERT: {name}*\nTrend: {trend}\nStrike: {best_strike} {opt_type}"
            send_telegram(msg)
            st.session_state.prev_oi[name] = oi_change

        results.append({"Index": name, "Spot": spot, "Best Strike": f"{best_strike} {opt_type}", 
                        "OI Change": oi_change, "Trend": trend, "Color": color})
    return results

# --- 4. UI LAYOUT ---
st.title("🦅 Venu Algo-Intelligence Dashboard")

# 1. Screener Row (Refresh బటన్ మరియు స్క్రీనర్ ఇక్కడే ఉంటాయి)
st.subheader("📊 Institutional Screener")
if st.button("🔄 Refresh Data & Scan"):
    data_list = run_master_engine()
    cols = st.columns(3)
    for i, data in enumerate(data_list):
        with cols[i]:
            st.markdown(f"""
                <div style="background-color: {data['Color']}; padding: 20px; border-radius: 15px; color: white; text-align: center;">
                    <h2 style="margin: 0;">{data['Index']}</h2>
                    <h3>{data['Trend']}</h3>
                    <p style="font-size: 18px;"><b>Strike: {data['Best Strike']}</b></p>
                    <small>Spot: {data['Spot']} | OI: {data['OI Change']}</small>
                </div>
            """, unsafe_allow_html=True)

st.divider()

# 2. Execution & Charts Row
col_a, col_b = st.columns([1, 2])

with col_a:
    st.subheader("⚡ Quick Execution")
    # ఇక్కడ సింబల్స్ ని సింపుల్ లిస్ట్ గా మార్చాను
    trade_idx = st.selectbox("Select Trade Index", ["NIFTY 50", "BANKNIFTY", "SENSEX"])
    trade_bias = st.radio("View", ["CALL", "PUT"])
    trade_lots = st.number_input("Lots", min_value=1, value=1)
    if st.button("🚀 Execute Order"):
        st.success(f"{trade_idx} Order Placed!")

with col_b:
    st.subheader("📈 Live Analytics Chart")
    
    # ముఖ్యమైన మార్పు: ఇక్కడ డైరెక్ట్ గా పేరు సెలెక్ట్ చేసుకునేలా మార్చాను
    chart_choice = st.selectbox("Select Chart Index", ["NIFTY 50", "BANKNIFTY", "SENSEX"])
    
    # సింబల్ మ్యాపింగ్
    if chart_choice == "NIFTY 50":
        final_symbol = "NSE:NIFTY"
    elif chart_choice == "BANKNIFTY":
        final_symbol = "NSE:BANKNIFTY"
    elif chart_choice == "SENSEX":
        final_symbol = "BSE:SENSEX"
    else:
        final_symbol = "NSE:NIFTY"

    # చార్ట్ ని ప్రదర్శించడం
    display_tradingview_chart(final_symbol)
