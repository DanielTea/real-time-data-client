# Trading Server Ports Reference

## Quick Fix for Connection Errors

If you see errors like "Cannot connect to trading server at http://localhost:5002", the multi-broker trading server is not running.

### ✅ Quick Start (Recommended)

```bash
./start-all.sh
```

This starts all services including the multi-broker trading server on port 5002.

### 🚀 Start Only the Trading Server

```bash
./start-multi-broker-server.sh
```

Or manually:

```bash
source .venv/bin/activate
python multi-broker-trading-server.py
```

## Port Configuration

### Current Setup (Multi-Broker)
- **Frontend**: http://localhost:5173
- **WebSocket Server**: ws://localhost:8080 (Polymarket data)
- **Multi-Broker Trading Server**: http://localhost:5002 ⭐ (Current)

### Legacy Setup
- **Old Alpaca Server**: http://localhost:5001 (Deprecated)

## Server Comparison

| Feature | Multi-Broker Server (5002) | Legacy Alpaca (5001) |
|---------|---------------------------|---------------------|
| **Brokers** | Alpaca, Bybit, Binance | Alpaca only |
| **Leverage** | ✅ Up to 125x (Binance) | ❌ No leverage |
| **Stocks** | ✅ (Alpaca) | ✅ |
| **Crypto** | ✅ All brokers | ✅ Alpaca spot only |
| **Status** | ✅ **Active (Recommended)** | ⚠️ Legacy |

## Troubleshooting

### Check if server is running

```bash
lsof -ti:5002
```

If nothing returns, the server is not running.

### Check server health

```bash
curl http://localhost:5002/api/health
```

Should return: `{"status":"healthy","broker":"None","initialized":false}`

### Kill stuck processes

```bash
# Kill old Alpaca server
lsof -ti:5001 | xargs kill -9

# Kill multi-broker server
lsof -ti:5002 | xargs kill -9

# Restart
./start-multi-broker-server.sh
```

### View server logs

```bash
# If started with start-all.sh
tail -f logs/trading-*.log

# If started manually
# Look at terminal output
```

## Configuration

Frontend is pre-configured to use port 5002. No changes needed!

The following files reference port 5002:
- `frontend/src/pages/TradingChat.tsx`
- `frontend/src/pages/AutoTrading.tsx`
- `multi-broker-trading-server.py`
- `start-multi-broker-server.sh`
- `start-all.sh`

## Next Steps

1. ✅ Server is running on port 5002
2. 🔄 Refresh your frontend browser
3. ⚙️ Go to **Settings** to configure broker credentials
4. 💬 Start trading in **Trading Chat** or **Auto-Trading** pages

---

**Note**: The `start-all.sh` script has been updated to automatically start the multi-broker server on port 5002 instead of the legacy Alpaca server.

