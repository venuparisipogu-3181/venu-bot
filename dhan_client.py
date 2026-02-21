# dhan_client.py - PRODUCTION DhanHQ WebSocket
from dhanhq import dhanhq
import threading
import time
import json
import websocket  # pip install websocket-client

class DhanLiveFeed:
    def __init__(self, client_id, access_token):
        self.client_id = client_id
        self.access_token = access_token
        self.data_store = {}
        self.ws = None
        self.tokens = []

    def on_message(self, ws, message):
        # Binary → JSON parse (Dhan v2 format)
        try:
            data = json.loads(message)
            for tick in data.get('tickers', []):
                token = tick['security_id']
                self.data_store[token] = {
                    "ltp": tick.get('ltp', 0),
                    "oi": tick.get('oi', 0),
                    "timestamp": time.time()
                }
        except:
            pass  # Ignore parse errors

    def on_open(self, ws):
        # DhanHQ auth packet
        auth_packet = {
            "method": "subscribe",
            "data": {
                "tickers": self.tokens,
                "feedType": "Full"  # LTP + OI + Volume
            }
        }
        ws.send(json.dumps(auth_packet))

    def start(self, tokens):
        self.tokens = tokens
        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(
            "wss://api-feed.dhan.co",  # Dhan WS endpoint
            on_message=self.on_message,
            on_open=self.on_open
        )
        thread = threading.Thread(target=self.ws.run_forever)
        thread.daemon = True
        thread.start()
