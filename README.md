# Forex Crypto Signal Bot

RSI-based trading signal bot for Telegram monitoring 48 instruments across
crypto, forex, indices, commodities, and stocks.

---

## Files

| File | Purpose |
|------|---------|
| `requirements.txt` | Python dependencies |
| `config.py` | Pairs, flags, RSI settings, scan intervals |
| `signal_generator.py` | RSI calculation, price history, signal formatting |
| `main.py` | API fetching, Telegram commands, auto-scan loop |

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ Yes | From @BotFather |
| `TELEGRAM_CHAT_ID` | ✅ Yes | Your chat or channel ID |
| `ALPHA_VANTAGE_KEY` | ⚠️ Recommended | Free key from alphavantage.co |

---

## Local Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in your values
python main.py
```

**.env** example:
```
TELEGRAM_BOT_TOKEN=7123456789:AAFxxxx
TELEGRAM_CHAT_ID=-100123456789
ALPHA_VANTAGE_KEY=YOUR_KEY_HERE
```

---

## Railway Deployment

1. Push files to a GitHub repo.
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub**.
3. Select your repo.
4. In **Variables** tab add the three env vars above.
5. Railway auto-detects Python and runs `python main.py`.
6. Bot sends a startup message to your Telegram on first deploy.

No `Procfile` needed — Railway will use `python main.py` by default.

---

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome & command list |
| `/status` | API health, signal count |
| `/signal BTCUSDT` | Manual signal for any pair |
| `/pairs` | All monitored instruments |
| `/scan` | Force immediate full scan |
| `/autosignal` | Toggle auto signals ON/OFF |
| `/stats` | Runtime statistics |
| `/time` | Nigeria (WAT) time |
| `/confidence 65` | Set min confidence % |
| `/duration 5` | Set trade duration (minutes) |

---

## How It Works

1. Every 10–12 minutes the bot scans all 48 pairs.
2. Prices are fetched live from **Binance** (crypto) and **Alpha Vantage** (everything else).
3. Each price is stored in a rolling 100-point history per symbol.
4. Once 15+ points exist, RSI-14 is calculated.
5. RSI < 30 → **BUY** signal. RSI > 70 → **SELL** signal.
6. Signals below the confidence threshold are silently skipped.
7. Same pair cannot signal again within 10 minutes (cooldown).