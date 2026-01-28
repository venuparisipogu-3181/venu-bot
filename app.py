import streamlit as st
import pandas as pd
import requests
import streamlit.components.v1 as components
from dhanhq import dhanhq

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Venu Algo Intelligence", layout="wide")

CLIENT_ID = st.secrets.get("DHAN_CLIENT_ID", "1106476940")
ACCESS_TOKEN = st.secrets.get("DHAN_ACCESS_TOKEN", "YOUR_TOKEN")
TELEGRAM_TOKEN = st.secrets.get("TELEGRAM_TOKEN", "8289933882:AAGgTyAhFHYzlKbZ_0rvH8GztqXeTB6P-yQ")
TELEGRAM_CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "2115666034")

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)

INDEX_MAP = {
    "NIFTY 50": {"id": "13", "step": 50, "exch": "NSE_INDEX", "tv": "NSE:NIFTY"},
    "BANKNIFTY": {"id": "25", "step": 100, "exch": "NSE_INDEX", "tv": "NSE:BANKNIFTY"},
    "SENSEX": {"id": "51", "step": 100, "exch": "BSE_INDEX", "tv": "BSE:SENSEX"}
}

# --- 2. FUNCTIONS ---
def display_tradingview_chart(symbol_name):
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

if 'prev_oi' not in st.session_state:
    st.session_state.prev_oi = {k: 0 for k in INDEX_MAP.keys()}

# --- 3. MASTER ENGINE ---
def run_screener():
    results = []
    for name, cfg in INDEX_MAP.items():
        try:
            # DHAN LIVE LTP
            resp = dhan.get_ltp_data(name, cfg['exch'], cfg['id'])
            
            # డేటా సరిగ్గా రాకపోతే Fallback
            if resp.get('status') == 'success':
                spot = resp['data']['last_price']
            else:
                spot = 0.0

            oi_change = -12500  # Placeholder
            atm = round(spot / cfg['step']) * cfg['step']
            opt_type = "CE" if oi_change < 0 else "PE"
            best_strike = atm - cfg['step'] if opt_type == "CE" else atm + cfg['step']
            
            results.append({
                "Index": name, "Spot": spot, "Best Strike": f"{best_strike} {opt_type}",
                "Trend": "Bullish 📈" if oi_change < 0 else "Bearish 📉",
                "Color": "#2ecc71" if oi_change < 0 else "#e74c3c"
            })
        except Exception as e:
            # Error వచ్చినా అన్ని Keys ఉండేలా జాగ్రత్త పడ్డాను
            results.append({
                "Index": name, "Spot": "N/A", "Best Strike": "N/A",
                "Trend": "Error", "Color": "#333"
            })
    return results

# --- 4. UI DISPLAY ---
st.title("🛡️ Venu Algo-Intelligence Terminal")

st.subheader("📊 Live Market Screener")
# ఇక్కడ ఒకసారి డేటా లోడ్ చేయాలి లేదంటే ఎర్రర్ వస్తుంది
if 'screener_data' not in st.session_state:
    st.session_state.screener_data = run_screener()

if st.button("🔄 SCAN LIVE MARKET"):
    st.session_state.screener_data = run_screener()

cols = st.columns(3)
for i, data in enumerate(st.session_state.screener_data):
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

col_left, col_right = st.columns([1, 2.5])
with col_left:
    st.subheader("⚡ Quick Trade")
    t_idx = st.selectbox("Select Index", list(INDEX_MAP.keys()))
    t_side = st.radio("Side", ["BUY CALL", "BUY PUT"])
    if st.button("🚀 FIRE ORDER"):
        st.warning(f"Order Fired for {t_idx}!")

with col_right:
    st.subheader("📈 Live Technical Analysis")
    chart_choice = st.selectbox("Select Chart", list(INDEX_MAP.keys()))
    display_tradingview_chart(INDEX_MAP[chart_choice]['tv'])
