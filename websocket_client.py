# websocket_client.py  –  v11 final
#
# IMPORTANT — SSID FORMAT:
# The SSID must be the COMPLETE auth string from the browser WebSocket tab.
# Correct format:
#   42["auth",{"session":"abc123","isDemo":1,"uid":12345678,"platform":1}]
#
# Wrong format (just the session value):
#   abc123xyz
#
# How to get the correct SSID:
#   1. Open pocketoption.com in Chrome
#   2. Press F12 → Network tab → filter by WS
#   3. Click the WebSocket connection
#   4. Look in Messages for a message starting with 42["auth",
#   5. Copy that ENTIRE message including the 42["auth",{...}] part
#   6. Paste it as your PO_SSID environment variable on Railway

import json
import threading
import time

import websocket
import config

# ─── SHARED STATE ─────────────────────────────────────────────────────────────
_otc_prices:       dict = {}
_otc_last_update:  dict = {}
_ws_connected:     bool = False
_ssid_expired:     bool = False
_reconnect_callback      = None
_current_ssid:     str  = ""

PING_INTERVAL  = 20
RECONNECT_WAIT = 5

_id_to_symbol = {v: k for k, v in config.PO_OTC_ASSET_IDS.items()}

WS_URLS = [
    "wss://pocketoption.com/socket.io/?EIO=4&transport=websocket",
    "wss://api.po.market/socket.io/?EIO=4&transport=websocket",
    "wss://pocketoption.com/socket.io/?EIO=3&transport=websocket",
]

# ─── PUBLIC API ───────────────────────────────────────────────────────────────

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

# ─── SSID PARSER ──────────────────────────────────────────────────────────────

def _parse_ssid(raw_ssid: str) -> tuple:
    """
    Parse SSID into (session_str, auth_message_str).

    Accepts two formats:
      1. Complete auth string:
         42["auth",{"session":"abc","isDemo":1,"uid":123,"platform":1}]
      2. Raw session value only:
         abc123xyz  (will be wrapped into correct format automatically)

    Returns (session_value, full_auth_message)
    """
    raw = raw_ssid.strip()

    # Format 1: already a complete auth message
    if raw.startswith('42["auth"') or raw.startswith("42['auth'"):
        try:
            inner = json.loads(raw[2:])   # strip leading "42"
            session = inner[1].get("session", "")
            return session, raw
        except Exception:
            pass

    # Format 2: JSON object only (no 42 prefix)
    if raw.startswith('{"session"') or raw.startswith("{'session'"):
        try:
            obj = json.loads(raw)
            session = obj.get("session", raw)
            auth_msg = json.dumps(["auth", obj])
            return session, f"42{auth_msg}"
        except Exception:
            pass

    # Format 3: raw session string — wrap it
    auth_payload = {
        "session":  raw,
        "isDemo":   1,
        "uid":      0,
        "platform": 1,
    }
    auth_msg = json.dumps(["auth", auth_payload])
    return raw, f"42{auth_msg}"

# ─── HANDLERS ─────────────────────────────────────────────────────────────────

def _on_open(ws):
    global _ws_connected
    _ws_connected = True
    print("[PO WS] Connected — sending socket.io handshake")
    ws.send("40")

def _on_message(ws, message):
    global _ssid_expired

    # Keep-alive ping
    if message == "2":
        ws.send("3")
        return

    # Socket.io connected — send auth
    if message.startswith("40"):
        print("[PO WS] Socket ready — sending auth")
        _, auth_msg = _parse_ssid(_current_ssid)
        print(f"[PO WS] Auth payload: {auth_msg[:80]}…")
        ws.send(auth_msg)
        return

    if message.startswith("42"):
        try:
            data    = json.loads(message[2:])
            event   = data[0] if isinstance(data, list) else ""
            payload = data[1] if len(data) > 1 else {}

            # Auth success — subscribe to all OTC assets
            if event == "successauth":
                print("[PO WS] ✅ Auth successful — subscribing to OTC assets")
                for symbol, asset_id in config.PO_OTC_ASSET_IDS.items():
                    sub = f'42{json.dumps(["subscribeQuotes", {"asset": asset_id, "period": 0}])}'
                    ws.send(sub)
                    time.sleep(0.05)
                print(f"[PO WS] Subscribed to {len(config.PO_OTC_ASSET_IDS)} OTC assets")

            # Auth failure
            elif event in ("failauth", "NotAuthorized", "error"):
                print(f"[PO WS] ❌ Auth FAILED — SSID expired or wrong format: {payload}")
                _ssid_expired = True
                if _reconnect_callback:
                    _reconnect_callback()
                ws.close()

            # Price tick
            elif event in ("price", "tick", "quote", "quotes", "updateStream"):
                _store_price(payload)

            # Direct price object
            elif isinstance(payload, dict) and "asset" in payload:
                _store_price(payload)

        except Exception:
            pass

def _store_price(payload):
    try:
        asset_id = (payload.get("asset") or payload.get("id")
                    or payload.get("asset_id"))
        price    = (payload.get("price") or payload.get("close")
                    or payload.get("value") or payload.get("ask")
                    or payload.get("bid"))
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
    print(f"[PO WS] Closed — code={code}")

# ─── CONNECTION MANAGER ───────────────────────────────────────────────────────

def start_websocket(ssid: str, on_expired_callback) -> None:
    global _reconnect_callback, _ssid_expired, _current_ssid
    _reconnect_callback = on_expired_callback
    _current_ssid       = ssid
    _ssid_expired       = False

    session_val, auth_preview = _parse_ssid(ssid)
    print(f"[PO WS] SSID parsed. Auth preview: {auth_preview[:80]}…")

    def run():
        global _ssid_expired
        url_index = 0
        while True:
            if _ssid_expired:
                print("[PO WS] SSID expired — waiting for /newssid command")
                time.sleep(30)
                continue

            url = WS_URLS[url_index % len(WS_URLS)]
            print(f"[PO WS] Connecting to: {url}")
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
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/120.0.0.0 Safari/537.36"
                        ),
                        "Origin": "https://pocketoption.com",
                        "Referer": "https://pocketoption.com/",
                    },
                )
                ws.run_forever(
                    ping_interval=PING_INTERVAL,
                    ping_timeout=10,
                )
            except Exception as e:
                print(f"[PO WS] Exception: {e}")

            if not _ssid_expired:
                url_index += 1
                print(f"[PO WS] Reconnecting in {RECONNECT_WAIT}s …")
                time.sleep(RECONNECT_WAIT)

    threading.Thread(target=run, daemon=True).start()
    print("[PO WS] Background thread started.")


def reset_ssid(new_ssid: str) -> None:
    global _ssid_expired, _current_ssid
    _ssid_expired = False
    _current_ssid = new_ssid
    print("[PO WS] SSID updated — reconnecting …")
    start_websocket(new_ssid, _reconnect_callback)
