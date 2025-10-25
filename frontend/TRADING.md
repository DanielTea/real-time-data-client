# Trading Chat Feature

## Overview

The Trading Chat is an AI-powered interface that allows you to execute cryptocurrency trades using natural language commands. It combines:

- **Alpaca Trading API** for executing real trades
- **Claude AI (Anthropic)** for natural language understanding
- **Tool-augmented AI** for smart trade execution

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      React Frontend                          │
│                   (TradingChat.tsx)                          │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP REST API
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  Python Trading Server                       │
│                   (trading-server.py)                        │
│  ┌──────────────────┐        ┌──────────────────┐          │
│  │  Flask REST API  │        │  Tool Processor  │          │
│  └──────────────────┘        └──────────────────┘          │
└───────┬─────────────────────────────┬───────────────────────┘
        │                             │
        ▼                             ▼
┌──────────────────┐          ┌──────────────────┐
│  Claude AI API   │          │  Alpaca API      │
│  (Anthropic)     │          │  (Trading)       │
└──────────────────┘          └──────────────────┘
```

## Setup

### 1. Install Python Dependencies

```bash
# From project root
source .venv/bin/activate
uv pip install -r requirements-trading.txt
```

### 2. Get API Keys

#### Alpaca API Keys

1. Sign up at [Alpaca Markets](https://alpaca.markets/)
2. Navigate to **Paper Trading** section (free, no real money)
3. Generate API keys (Key + Secret)
4. Copy both keys

#### Claude API Key

1. Sign up at [Anthropic Console](https://console.anthropic.com/)
2. Navigate to API Keys
3. Create a new API key
4. Copy the key

### 3. Configure in Frontend

1. Start the frontend: `pnpm dev`
2. Navigate to **⚙️ Settings**
3. Scroll to **🔐 Trading API Configuration**
4. Enter your API keys:
    - Alpaca API Key
    - Alpaca Secret Key
    - Anthropic (Claude) API Key
5. Enable **Paper Trading Mode** (recommended)
6. Click **💾 Save API Keys**

## Usage

### Start the Trading Server

From project root:

```bash
# Option 1: Use the startup script
./start-trading.sh

# Option 2: Manual start
source .venv/bin/activate
python trading-server.py
```

The server will start on `http://localhost:5001`

### Access Trading Chat

1. Open the frontend (http://localhost:5173)
2. Click **💬 Trading Chat** in the sidebar
3. The chat will initialize automatically
4. Start trading with natural language!

## Example Commands

### Account Information

```
"show my account balance"
"what's my portfolio value?"
"how much cash do I have?"
"what's my buying power?"
```

### Buying Crypto

```
"buy $100 of Bitcoin"
"buy 0.5 ETH"
"purchase $50 worth of Dogecoin"
"buy some BTC"
```

### Selling Crypto

```
"sell all my Bitcoin"
"sell 0.1 ETH"
"sell $25 of DOGE"
"liquidate all my positions"
```

### Price Quotes

```
"what's the current BTC price?"
"how much is Ethereum?"
"what's DOGE trading at?"
```

### Position Management

```
"show all my positions"
"what crypto do I own?"
"what's my portfolio?"
```

## API Endpoints

### `POST /api/initialize`

Initialize trading clients with API keys

**Request:**

```json
{
    "alpaca_key": "string",
    "alpaca_secret": "string",
    "claude_key": "string",
    "paper_mode": true
}
```

**Response:**

```json
{
    "status": "initialized"
}
```

### `POST /api/chat`

Process a chat message and execute trading commands

**Request:**

```json
{
    "message": "buy $100 of BTC",
    "history": [
        { "role": "user", "content": "previous message" },
        { "role": "assistant", "content": "previous response" }
    ]
}
```

**Response:**

```json
{
  "response": "I've executed your order...",
  "conversation_history": [...]
}
```

### `GET /api/account`

Get account information

**Response:**

```json
{
    "status": "ACTIVE",
    "cash": 100000.0,
    "portfolio_value": 100000.0,
    "buying_power": 100000.0,
    "equity": 100000.0
}
```

### `GET /api/positions`

Get all current positions

**Response:**

```json
[
    {
        "symbol": "BTCUSD",
        "qty": 0.5,
        "market_value": 25000.0,
        "current_price": 50000.0,
        "unrealized_pl": 500.0,
        "unrealized_plpc": 0.02
    }
]
```

## Claude Tool Functions

The server provides these tools to Claude for trade execution:

### `get_account_info()`

Retrieves current account balance, portfolio value, and buying power

### `get_positions()`

Lists all current positions in the portfolio

### `buy_crypto(symbol, qty?, notional?)`

Executes a market buy order for cryptocurrency

- `symbol`: Crypto symbol (BTC, ETH, DOGE, etc.)
- `qty`: Number of coins (optional if notional provided)
- `notional`: Dollar amount (optional if qty provided)

### `sell_crypto(symbol, qty?, notional?)`

Executes a market sell order for cryptocurrency

- Same parameters as buy_crypto

### `get_crypto_price(symbol)`

Gets the current price of a cryptocurrency

- `symbol`: Crypto symbol (BTC, ETH, DOGE, etc.)

## Component Structure

### TradingChat.tsx

Main component for the trading chat interface.

**State:**

- `messages`: Array of chat messages
- `input`: Current input text
- `isLoading`: Loading state
- `isInitialized`: Whether clients are initialized
- `accountInfo`: Current account information

**Key Functions:**

- `initializeServer()`: Initialize trading clients with API keys
- `fetchAccountInfo()`: Fetch current account info from server
- `handleSendMessage()`: Send message to Claude and execute trades
- `handleKeyPress()`: Handle Enter key for sending messages

## Security Considerations

### API Key Storage

- Keys stored in browser's `localStorage`
- Never sent to any third-party servers
- Only used for local API calls

### Paper Trading

- Default mode is PAPER TRADING (no real money)
- Switch controlled in Settings
- Clear visual indicator in chat

### Request Validation

- All requests validated on server side
- Tool execution logged for audit
- Claude acts as smart middleware

## Troubleshooting

### "Cannot connect to trading server"

**Solution:** Make sure the trading server is running:

```bash
./start-trading.sh
```

### "Please configure your API keys"

**Solution:**

1. Go to Settings
2. Enter all three API keys
3. Save settings

### "Failed to initialize"

**Solution:**

- Check API keys are valid
- Ensure Alpaca account is active
- Verify Claude API key has credits

### Trades not executing

**Solution:**

- Check account has sufficient buying power
- Verify crypto symbol is correct (BTC, ETH, etc.)
- Ensure market is open (crypto trades 24/7)

## Development

### Adding New Trading Tools

1. **Define tool in `TRADING_TOOLS`** (trading-server.py):

```python
{
    "name": "get_order_history",
    "description": "Get recent order history",
    "input_schema": {
        "type": "object",
        "properties": {
            "limit": {"type": "number"}
        }
    }
}
```

2. **Implement tool function**:

```python
def get_order_history(limit=10):
    orders = alpaca_trading_client.get_orders(limit=limit)
    return [order.dict() for order in orders]
```

3. **Add to tool processor**:

```python
def process_tool_call(tool_name, tool_input):
    if tool_name == "get_order_history":
        return get_order_history(tool_input.get("limit", 10))
    # ... other tools
```

### Testing

Test the server directly with curl:

```bash
# Initialize
curl -X POST http://localhost:5001/api/initialize \
  -H "Content-Type: application/json" \
  -d '{"alpaca_key":"xxx","alpaca_secret":"xxx","claude_key":"xxx"}'

# Get account
curl http://localhost:5001/api/account

# Send chat message
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"what is my account balance?"}'
```

## Future Enhancements

- [ ] Stock trading support (in addition to crypto)
- [ ] Options trading integration
- [ ] Advanced order types (limit, stop-loss)
- [ ] Portfolio analytics and charts
- [ ] Trading history visualization
- [ ] Multi-account support
- [ ] Risk management tools
- [ ] Backtesting capabilities

## Resources

- [Alpaca API Docs](https://docs.alpaca.markets/)
- [Claude API Docs](https://docs.anthropic.com/)
- [Alpaca Python SDK](https://github.com/alpacahq/alpaca-py)
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python)

## Support

For issues:

1. Check server logs: `python trading-server.py` output
2. Check browser console: DevTools → Console
3. Verify API keys in Settings
4. Ensure trading server is running
5. Review troubleshooting section above
