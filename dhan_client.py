# dhan_client.py - Streamlit Cloud కి perfect demo
import threading
import time
import random

class DhanLiveFeed:
    def __init__(self, client_id, access_token, tokens):
        self.tokens = tokens
        self.data_store = {}
        self.thread = None

    def on_message(self, message):
        # Nifty ATM ±5 strikes realistic data
        for i, token in enumerate(self.tokens):
            strike = 25750 + (i // 2) * 50
            self.data_store[token] = {
                "ltp": 250.50 + random.uniform(-2, 2),
                "oi": 1500000 + random.randint(-500000, 500000)
            }

    def start(self):
        def simulate():
            while True:
                self.on_message("live")
                time.sleep(2)
        self.thread = threading.Thread(target=simulate, daemon=True)
        self.thread.start()
