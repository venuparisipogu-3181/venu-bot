# dhan_client.py - Fixed WebSocket Live Feed
from dhanhq import DhanContext, MarketFeed
import threading
import time

class DhanLiveFeed:
    def __init__(self, client_id, access_token, tokens):
        self.context = DhanContext(client_id, access_token)
        self.tokens = tokens  # list of security_ids (int)
        self.data_store = {}
        self.feed = None

    def on_data(self, message):
        # Parse binary response: security_id from header bytes 5-8 (int32 little-endian)
        if len(message) >= 8:
            sec_id_bytes = message[4:8]
            security_id = int.from_bytes(sec_id_bytes, 'little')
            if security_id in self.tokens:
                # LTP: bytes 9-12 float32 little-endian (Ticker/Quote/Full)
                ltp_bytes = message[8:12]
                ltp = float(int.from_bytes(ltp_bytes, 'little'))
                # OI: for Quote/Full, bytes after LTP (simplified; check Dhan docs for exact offset)
                oi_start = 32 if len(message) > 40 else 0  # OI in Quote packet ~bytes 9-12 after header
                oi = int.from_bytes(message[oi_start:oi_start+4], 'little') if oi_start else 0
                self.data_store[security_id] = {"ltp": ltp, "oi": oi}

    def start(self):
        self.feed = MarketFeed(self.context, self.tokens, "v2")  # v2 required!
        self.feed.on_data = self.on_data  # Fixed callback name per GitHub
        thread = threading.Thread(target=self.feed.run_forever, daemon=True)
        thread.start()
