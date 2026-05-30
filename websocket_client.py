# websocket_client.py  –  v11 fixed
import json
import threading
import time

import websocket
import config

# ─── SHARED STATE ────────────────────────────────────────────────────────────
_otc_prices: dict      = {}
_otc_last_update: dict = {}
_ws_connected:    bool = False
_ssid_expired:    bool = False
_reconnect_callback    = None
_current_ssid:    str  = ""

PING_INTERVAL  = 20
RECONNECT_WAIT = 5

_id_to_symbol = {v: k for k, v in config.PO_OTC_ASSET_IDS.items()}

# ─── PUBLIC API ──────────────────────────────────────────────────────────────

def get_otc_price(symbol: str):
    price = _otc_prices.get(symbol)
    if price is None:
        return None
    if time.time() - _otc_last_update.get(symbol, 0) > 60:
        return None
    return price

def is_connected() -> bool:
    return _ws_connected

def is_ssid_expired() -> bool:
    return _ssid_expired

def all_otc_prices() -> dict:
    now = time.time()
    return {s: p for s, p in _otc_prices.items()
            if now - _otc_last_update.get(s, 0) < 60}

# ─── HANDLERS ────────────────────────────────────────────────────────────────

def _on_open(ws):
    global _ws_connected
    _ws_connected = True
    print("[PO WS] Connected — sending handshake")
    ws.send("40")

def _on_message(ws, message):
    global _ssid_expired

    if message == "2":
        ws.send("3")
        return

    if message.startswith("40"):
        # Socket connected — authenticate
        print("[PO WS] Socket ready — authenticating")
        auth = json.dumps(["auth", {
            "ssid":     _current_ssid,
            "language": "en",
            "is_demo":  1
        }])
        ws.send(f"42{auth}")
        return

    if message.startswith("42"):
        try:
            data = json.loads(message[2:])
            event   = data[0] if isinstance(data, list) else ""
            payload = data[1] if len(data) > 1 else {}

            if event == "successauth":
                print("[PO WS] Auth OK — subscribing to OTC assets")
                for symbol, asset_id in config.PO_OTC_ASSET_IDS.items():
                    sub = json.dumps(["subscribeQuotes", {
                        "asset": asset_id, "period": 0
                    }])
                    ws.send(f"42{sub}")
                    time.sleep(0.05)

            elif event in ("failauth", "NotAuthorized", "error"):
                print(f"[PO WS] Auth FAILED: {payload}")
                _ssid_expired = True
                if _reconnect_callback:
                    _reconnect_callback()
                ws.close()

            elif event in ("price", "tick", "quote", "quotes"):
                _store_price(payload)

            elif isinstance(payload, dict) and "asset" in payload:
                _store_price(payload)

        except Exception as e:
            pass

def _store_price(payload):
    try:
        asset_id = payload.get("asset") or payload.get("id")
        price    = (payload.get("price") or payload.get("close")
                    or payload.get("value") or payload.get("ask"))
        if asset_id is None or price is None:
            return
        symbol = _id_to_symbol.get(int(asset_id))
        if symbol is None:
            return
        _otc_prices[symbol]      = float(price)
        _otc_last_update[symbol] = time.time()
    except Exception:
        pass

def _on_error(ws, error):
    print(f"[PO WS] Error: {error}")

def _on_close(ws, code, msg):
    global _ws_connected
    _ws_connected = False
    print(f"[PO WS] Closed: {code} {msg}")

# ─── CONNECTION MANAGER ──────────────────────────────────────────────────────

def start_websocket(ssid: str, on_expired_callback) -> None:
    global _reconnect_callback, _ssid_expired, _current_ssid
    _reconnect_callback = on_expired_callback
    _current_ssid       = ssid

    urls_to_try = [
        "wss://pocketoption.com/socket.io/?EIO=4&transport=websocket",
        "wss://api.po.market/socket.io/?EIO=4&transport=websocket",
        "wss://pocketoption.com/socket.io/?EIO=3&transport=websocket",
    ]

    def run():
        global _ssid_expired
        url_index = 0
        while True:
            if _ssid_expired:
                print("[PO WS] SSID expired — waiting for /newssid")
                time.sleep(30)
                continue

            url = urls_to_try[url_index % len(urls_to_try)]
            print(f"[PO WS] Trying: {url}")
            try:
                ws = websocket.WebSocketApp(
                    url,
                    on_open=_on_open,
                    on_message=_on_message,
                    on_error=_on_error,
                    on_close=_on_close,
                    header={
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
                        ),
                        "Origin": "https://pocketoption.com",
                    },
                    cookie=f"ssid={ssid}",
                )
                ws.run_forever(ping_interval=PING_INTERVAL, ping_timeout=10)
            except Exception as e:
                print(f"[PO WS] Exception: {e}")

            if not _ssid_expired:
                url_index += 1
                print(f"[PO WS] Reconnecting in {RECONNECT_WAIT}s (trying next URL) …")
                time.sleep(RECONNECT_WAIT)

    threading.Thread(target=run, daemon=True).start()
    print("[PO WS] Background thread started.")

def reset_ssid(new_ssid: str) -> None:
    global _ssid_expired, _current_ssid
    _ssid_expired  = False
    _current_ssid  = new_ssid
    print("[PO WS] SSID reset — reconnecting …")
    start_websocket(new_ssid, _reconnect_callback)
