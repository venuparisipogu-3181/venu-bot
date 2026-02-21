import streamlit as st
import pandas as pd
import numpy as np
from dhanhq import dhanhq
from dhan_client import DhanLiveFeed
from oi_logic import *
import time

st.set_page_config(layout="wide")
st.title("🚀 LIVE NIFTY OI + DhanHQ WebSocket")

# Credentials
CLIENT_ID = st.secrets["DHAN_CLIENT_ID"]
ACCESS_TOKEN = st.secrets["DHAN_ACCESS_TOKEN"]

# LIVE Nifty strikes (25,571 spot)
@st.cache_data(ttl=300)
def get_live_strikes():
    dhan = dhanhq.dhanhq(dhanhq.DhanContext(CLIENT_ID, ACCESS_TOKEN))
    instruments = dhan.instruments.get_instrument_list("NSE")
    nifty_opts = [i for i in instruments if "NIFTY" in i['trading_symbol']]
    strikes = [25400, 25450, 25500, 25550, 25600, 25650, 25700, 25750, 25800]
    tokens = []
    for strike in strikes:
        ce = next((opt['security_id'] for opt in nifty_opts if f"NIFTY{strike}CE" in opt['trading_symbol']), None)
        pe = next((opt['security_id'] for opt in nifty_opts if f"NIFTY{strike}PE" in opt['trading_symbol']), None)
        if ce: tokens.append(int(ce))
        if pe: tokens.append(int(pe))
    return tokens[:20]  # Max 20 for stability

TOKENS = get_live_strikes()

if 'feed' not in st.session_state:
    st.session_state.feed = DhanLiveFeed(CLIENT_ID, ACCESS_TOKEN)
    st.session_state.feed.start(TOKENS)

# Rest same as before...
# (data processing, PCR, tables)
