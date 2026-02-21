import streamlit as st
import pandas as pd
import numpy as np
from dhan_client import DhanLiveFeed
from oi_logic import *
import time

# ===== CONFIG =====
CLIENT_ID = "YOUR_CLIENT_ID"
ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"

# Replace with real tokens
TOKENS = [111,222,333,444,555,666,777,888,999,1010]

# ===== START FEED =====
feed = DhanLiveFeed(CLIENT_ID, ACCESS_TOKEN, TOKENS)
feed.start()

previous_oi = {}

st.set_page_config(layout="wide")
st.title("LIVE NIFTY INSTITUTIONAL OI DASHBOARD")

while True:

    if len(feed.data_store) > 0:

        rows = []
        total_call = 0
        total_put = 0

        for token, values in feed.data_store.items():

            current_oi = values["oi"]

            if token not in previous_oi:
                previous_oi[token] = current_oi

            oi_change = calculate_oi_change(current_oi, previous_oi[token])
            previous_oi[token] = current_oi

            # Example logic (replace with real strike mapping)
            strike = token
            call_change = np.random.randint(-5000000, 5000000)
            put_change = np.random.randint(-5000000, 5000000)

            diff = call_change - put_change
            strength = tag_strength(diff)

            total_call += call_change
            total_put += put_change

            rows.append({
                "Strike": strike,
                "Call OI Change": call_change,
                "Put OI Change": put_change,
                "Difference": diff,
                "Strength": strength
            })

        df = pd.DataFrame(rows)

        pcr = calculate_pcr(total_call, total_put)

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Call Change", total_call)
        col2.metric("Total Put Change", total_put)
        col3.metric("PCR", pcr)

        st.subheader("Strike Wise OI Change")
        st.dataframe(df, use_container_width=True)

        st.subheader("Three Strike Range Analysis")
        three_df = three_strike_analysis(df)
        st.dataframe(three_df, use_container_width=True)

    time.sleep(2)
    st.experimental_rerun()
