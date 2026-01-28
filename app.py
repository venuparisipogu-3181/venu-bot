import streamlit as st
import pandas as pd
import requests
import streamlit.components.v1 as components
from dhanhq import dhanhq

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Venu Algo Intelligence", layout="wide")

# Secrets (Dhan & Telegram)
# మీ Streamlit Cloud Secrets లో వీటిని ఖచ్చితంగా సెట్ చేయండి
CLIENT_ID = st.secrets.get("DHAN_CLIENT_ID", "1106476940")
ACCESS_TOKEN = st.secrets.get("DHAN_ACCESS_TOKEN", "YOUR_TOKEN_HERE")
TELEGRAM_TOKEN = st.secrets.get("TELEGRAM_TOKEN", "8289933882:AAGgTyAhFHYzlKbZ_0rvH8GztqXeTB6P-yQ")
TELEGRAM_CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "2115666034")

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)

# ఇండెక్స్ సెట్టింగ్స్
INDEX_MAP = {
    "NIFTY 50": {"id": "13", "step": 50, "exch": "NSE_INDEX", "tv": "NSE:NIFTY"},
    "BANKNIFTY": {"id": "25", "step": 100, "exch": "NSE_INDEX", "tv": "NSE:BANKNIFTY"},
    "SENSEX": {"id": "51", "step": 100, "exch": "BSE_INDEX", "tv": "BSE:SENSEX"}
}

# --- 2. CORE FUNCTIONS ---

def send_telegram(msg):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        try:
            requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        except:
            pass

def display_tradingview_chart(symbol_name):
    # Full Feature Advanced Chart (800px Height)
    tradingview_html = f"""
    <div style="height:800px; width:100%;">
      <div id="tv_chart_merged" style="height:800px;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
        "autosize": true, "symbol": "{symbol_name}", "interval": "5",
        "timezone": "Asia/Kolkata", "theme": "dark", "style": "1",
        "locale": "in", "toolbar_bg": "#f1f3f6", "enable_publishing": false,
        "withdateranges": true, "hide_side_toolbar": false,
        "allow_symbol_change": true, "details": true, "container_id": "tv_chart_merged"
      }});
      </script>
    </div>
    """
    components.html(tradingview_html, height=820)

# Session State for Tracking Alerts
if 'prev_oi' not in st.session_state:
    st.session_state.prev_oi = {k: 0 for k in INDEX_MAP.keys()}

# --- 3. MASTER ENGINE (Live Price & OI) ---

def run_screener():
    results = []
    for name, cfg in INDEX_MAP.items():
        try:
            # DHAN LIVE LTP CALL
            resp = dhan.get_ltp_data(name, cfg['exch'], cfg['id'])
            spot = resp['data']['last_price'] if resp.get('status') == 'success' else 0.0
            
            # OI LOGIC (Placeholder for now - Can be linked to Option Chain API)
            oi_change = -12500  # - అంటే Bullish Writing
            
            # Calculations
            atm = round(spot / cfg['step']) * cfg['step']
            opt_type = "CE" if oi_change < 0 else "PE"
            best_strike = atm - cfg['step'] if opt_type == "CE" else atm + cfg['step']
            trend = "Bullish 📈" if oi_change < 0 else "Bearish 📉"
            color = "#2ecc71" if oi_change < 0 else "#e74c3c"

            # Telegram Alert on Significant OI Change
            if abs(oi_change - st.session_state.prev_oi[name]) > 10000:
                msg = f"🔔 *ALGO ALERT: {name}*\nTrend: {trend}\nBest Strike: {best_strike} {opt_type}\nLTP: {spot}"
                send_telegram(msg)
                st.session_state.prev_oi[name] = oi_change

            results.append({
                "Index": name, "Spot": spot, "Best Strike": f"{best_strike} {opt_type}",
                "Trend": trend, "Color": color, "OI": oi_change
            })
        except:
            results.append({"Index": name, "Spot": "Error", "Trend": "N/A", "Color": "#333", "OI": 0})
    return results

# --- 4. UI DISPLAY ---

st.title("🛡️ Venu Algo-Intelligence Terminal")

# SCREENER SECTION
st.subheader("📊 Live Market Screener")
if st.button("🔄 SCAN LIVE MARKET"):
    data_list = run_screener()
    cols = st.columns(3)
    for i, data in enumerate(data_list):
        with cols[i]:
            st.markdown(f"""
                <div style="background-color: {data['Color']}; padding: 25px; border-radius: 15px; color: white; text-align: center; border: 2px solid white;">
                    <h2 style="margin: 0;">{data['Index']}</h2>
                    <h1 style="margin: 10px;">{data['Spot']}</h1>
                    <hr>
                    <h3 style="margin: 5px;">{data['Trend']}</h3>
                    <p style="font-size: 20px;"><b>🎯 {data['Best Strike']}</b></p>
                </div>
            """, unsafe_allow_html=True)

st.divider()

# CHART & TRADE SECTION
col_left, col_right = st.columns([1, 2.5])

with col_left:
    st.subheader("⚡ Quick Trade")
    t_idx = st.selectbox("Select Index", list(INDEX_MAP.keys()))
    t_side = st.radio("Side", ["BUY CALL", "BUY PUT"])
    t_qty = st.number_input("Lots", min_value=1, value=1)
    if st.button("🚀 FIRE ORDER"):
        st.warning(f"Order Fired for {t_idx} {t_side}!")

with col_right:
    st.subheader("📈 Live Technical Analysis")
    chart_choice = st.selectbox("Select Chart", list(INDEX_MAP.keys()), index=0)
    # Correct Symbol Mapping to avoid Apple Chart
    display_tradingview_chart(INDEX_MAP[chart_choice]['tv'])
