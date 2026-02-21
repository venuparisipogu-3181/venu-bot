from dhanhq import dhanhq
from dhanhq.marketfeed import DhanFeed
import threading

class DhanLiveFeed:

    def __init__(self, client_id, access_token, tokens):
        self.client_id = client_id
        self.access_token = access_token
        self.tokens = tokens
        self.data_store = {}

    def on_message(self, message):
        for tick in message:
            token = tick['security_id']
            self.data_store[token] = {
                "ltp": tick.get("last_price", 0),
                "oi": tick.get("oi", 0)
            }

    def start(self):
        feed = DhanFeed(self.client_id, self.access_token, self.tokens)
        feed.on_message = self.on_message
        threading.Thread(target=feed.run_forever, daemon=True).start()
