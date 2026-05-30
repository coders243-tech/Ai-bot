# websocket_client.py  –  v11
# Connects to Pocket Option's WebSocket price stream using SSID.
# Receives real-time OTC prices and stores them for the signal engine.
# Handles reconnection and SSID expiry detection automatically.

import json
import threading
import time
from collections import deque
from datetime import datetime, timezone

import websocket  # websocket-client library

import config

# ─── SHARED PRICE STORE ──────────────────────────────────────────────────────
# { symbol: latest_price }
_otc_prices: dict[str, float] = {}

# Track last update time per symbol to detect stale prices
_otc_last_update: dict[str, float] = {}

# Connection state flags
_ws_connected:      bool = False
_ssid_expired:      bool = False
_reconnect_callback = None   # set by main.py to notify Telegram when SSID expires

# ─── POCKET OPTION WebSocket SETTINGS ────────────────────────────────────────
PO_WS_URL    = "wss://api.po.market/socket.io/?EIO=4&transport=websocket"
PING_INTERVAL = 25   # seconds between keep-alive pings
RECONNECT_WAIT = 5   # seconds before reconnect attempt

# ─── REVERSE MAP: asset_id → symbol ──────────────────────────────────────────
_id_to_symbol = {v: k for k, v in config.PO_OTC_ASSET_IDS.items()}


def get_otc_price(symbol: str) -> float | None:
    """
    Return latest OTC price for a symbol.
    Returns None if price is older than 60 seconds (stale).
    """
    price = _otc_prices.get(symbol)
    if price is None:
        return None
    last_update = _otc_last_update.get(symbol, 0)
    if time.time() - last_update > 60:
        return None   # stale price
    return price


def is_connected() -> bool:
    return _ws_connected


def is_ssid_expired() -> bool:
    return _ssid_expired


def all_otc_prices() -> dict:
    """Return all current OTC prices as { symbol: price }."""
    now = time.time()
    return {
        sym: price
        for sym, price in _otc_prices.items()
        if now - _otc_last_update.get(sym, 0) < 60
    }


# ─── WebSocket EVENT HANDLERS ────────────────────────────────────────────────

def _on_open(ws, ssid: str) -> None:
    global _ws_connected
    _ws_connected = True
    print("[PO WebSocket] Connected. Authenticating …")

    # Step 1: Send socket.io handshake
    ws.send("40")

    # Step 2: Authenticate with SSID
    auth_payload = json.dumps({"ssid": ssid, "localization": "en"})
    ws.send(f'42["auth",{auth_payload}]')


def _on_message(ws, message: str, ssid: str) -> None:
    global _ssid_expired

    # socket.io ping/pong
    if message == "2":
        ws.send("3")
        return

    # Strip socket.io prefix
    if message.startswith("42"):
        try:
            data = json.loads(message[2:])
            event = data[0] if isinstance(data, list) else ""
            payload = data[1] if len(data) > 1 else {}

            # Auth success → subscribe to all OTC asset prices
            if event == "successauth":
                print("[PO WebSocket] Auth successful. Subscribing to OTC prices …")
                _subscribe_all(ws)

            # Auth failure → SSID expired or invalid
            elif event in ("failauth", "error"):
                print(f"[PO WebSocket] Auth failed: {payload}")
                _ssid_expired = True
                if _reconnect_callback:
                    _reconnect_callback()
                ws.close()

            # Price tick received
            elif event in ("price", "tick", "quotes"):
                _handle_price_tick(payload)

            # Handle array of quotes
            elif isinstance(payload, dict) and "asset" in payload:
                _handle_price_tick(payload)

        except (json.JSONDecodeError, IndexError, KeyError):
            pass

    # socket.io connection established
    elif message.startswith("0"):
        pass  # handled in on_open


def _subscribe_all(ws) -> None:
    """Subscribe to price stream for every OTC asset."""
    for symbol, asset_id in config.PO_OTC_ASSET_IDS.items():
        payload = json.dumps({"asset": asset_id, "period": 0})
        ws.send(f'42["subscribeQuotes",{payload}]')
        print(f"  [PO WS] Subscribed to {symbol} (id={asset_id})")
        time.sleep(0.05)   # small delay to avoid flooding


def _handle_price_tick(payload: dict) -> None:
    """Parse a price tick and store it."""
    try:
        asset_id = payload.get("asset") or payload.get("id")
        price    = payload.get("price") or payload.get("close") or payload.get("value")

        if asset_id is None or price is None:
            return

        symbol = _id_to_symbol.get(int(asset_id))
        if symbol is None:
            return

        _otc_prices[symbol]      = float(price)
        _otc_last_update[symbol] = time.time()

    except (ValueError, TypeError):
        pass


def _on_error(ws, error) -> None:
    print(f"[PO WebSocket] Error: {error}")


def _on_close(ws, close_status_code, close_msg) -> None:
    global _ws_connected
    _ws_connected = False
    print(f"[PO WebSocket] Connection closed: {close_status_code} {close_msg}")


# ─── CONNECTION MANAGER ──────────────────────────────────────────────────────

def start_websocket(ssid: str, on_ssid_expired_callback) -> None:
    """
    Start the WebSocket connection in a background thread.
    Automatically reconnects on disconnect.
    Calls on_ssid_expired_callback when SSID is detected as invalid/expired.
    """
    global _reconnect_callback, _ssid_expired
    _reconnect_callback = on_ssid_expired_callback

    def run():
        global _ssid_expired
        while True:
            if _ssid_expired:
                print("[PO WebSocket] SSID expired — waiting for new SSID.")
                time.sleep(60)  # wait — main.py will restart with new SSID
                continue

            print(f"[PO WebSocket] Connecting to {PO_WS_URL} …")
            try:
                ws = websocket.WebSocketApp(
                    PO_WS_URL,
                    on_open=lambda w: _on_open(w, ssid),
                    on_message=lambda w, msg: _on_message(w, msg, ssid),
                    on_error=_on_error,
                    on_close=_on_close,
                    header={
                        "User-Agent": "Mozilla/5.0",
                        "Origin": "https://pocketoption.com",
                    },
                )
                ws.run_forever(
                    ping_interval=PING_INTERVAL,
                    ping_timeout=10,
                )
            except Exception as e:
                print(f"[PO WebSocket] Exception: {e}")

            if not _ssid_expired:
                print(f"[PO WebSocket] Reconnecting in {RECONNECT_WAIT}s …")
                time.sleep(RECONNECT_WAIT)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    print("[PO WebSocket] Background thread started.")


def reset_ssid(new_ssid: str) -> None:
    """
    Called by main.py when user provides a new SSID.
    Resets the expired flag so the connection loop retries.
    """
    global _ssid_expired
    _ssid_expired = False
    print(f"[PO WebSocket] SSID updated. Reconnecting …")
    start_websocket(new_ssid, _reconnect_callback)
