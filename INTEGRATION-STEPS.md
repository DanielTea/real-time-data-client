# Integration Steps - Adding Multi-Broker Support

## Overview

This guide explains how to integrate the broker abstraction layer with your existing `alpaca-trading-server.py`.

## Files Created

The following files have been created in your workspace:

```
brokers/
├── __init__.py           # Package initialization
├── base.py               # BaseBroker abstract class (interface)
├── alpaca_broker.py      # Alpaca implementation
├── bybit_broker.py       # Bybit implementation
├── binance_broker.py     # Binance implementation
└── factory.py            # Broker factory

broker_adapter.py         # Adapter module for easy integration
requirements-brokers.txt  # Dependencies
BROKER-INTEGRATION.md     # User documentation
```

## Integration Steps

### Step 1: Install Dependencies

```bash
# Activate your virtual environment first
source .venv/bin/activate

# Install new broker dependencies
uv pip install requests

# Optional: Install official broker SDKs for better performance
# uv pip install pybit python-binance
```

### Step 2: Modify alpaca-trading-server.py

You need to make the following changes to integrate broker support:

#### A. Add Imports (at top of file)

```python
# Add after existing imports
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from broker_adapter import (
    initialize_broker,
    get_current_broker,
    get_broker_info,
    get_supported_brokers
)
```

#### B. Update Global Variables

Replace:

```python
trading_client = None
stock_data_client = None
crypto_data_client = None
news_client = None
```

With:

```python
# Broker instance (replaces individual clients)
broker = None

# Keep these for AI
anthropic_client = None
openai_client = None
ai_model = 'claude'
```

#### C. Add Broker Info Endpoint

```python
@app.route('/api/brokers', methods=['GET'])
def get_brokers():
    """Get information about supported brokers"""
    return jsonify({
        'brokers': get_broker_info(),
        'supported': get_supported_brokers()
    })
```

#### D. Update Initialize Endpoint

Replace the existing `/api/initialize` route with:

```python
@app.route('/api/initialize', methods=['POST'])
def initialize():
    """Initialize with broker and API keys"""
    global broker, anthropic_client, openai_client, ai_model, conversation_history

    data = request.json

    # Get broker configuration
    broker_type = data.get('broker', 'alpaca')  # Default to Alpaca

    # Get broker API keys based on broker type
    if broker_type == 'alpaca':
        broker_key = data.get('alpaca_key')
        broker_secret = data.get('alpaca_secret')
    elif broker_type == 'bybit':
        broker_key = data.get('bybit_key')
        broker_secret = data.get('bybit_secret')
    elif broker_type == 'binance':
        broker_key = data.get('binance_key')
        broker_secret = data.get('binance_secret')
    else:
        return jsonify({"error": f"Unsupported broker: {broker_type}"}), 400

    # Get AI keys and settings
    claude_key = data.get('claude_key')
    deepseek_key = data.get('deepseek_key')
    selected_model = data.get('ai_model', 'claude')
    paper_mode = data.get('paper_mode', True)

    # Initialize broker
    try:
        broker = initialize_broker(
            broker_type=broker_type,
            api_key=broker_key,
            api_secret=broker_secret,
            paper_mode=paper_mode
        )

        # Initialize AI clients (same as before)
        ai_model = selected_model
        if ai_model == 'claude' and claude_key:
            anthropic_client = Anthropic(api_key=claude_key)
        elif ai_model == 'deepseek' and deepseek_key:
            openai_client = OpenAI(
                api_key=deepseek_key,
                base_url="https://api.deepseek.com/v1"
            )

        conversation_history = []

        return jsonify({
            "success": True,
            "message": f"Initialized with {broker.get_broker_name()} broker",
            "broker": broker.get_broker_name(),
            "paper_mode": paper_mode,
            "ai_model": ai_model
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

#### E. Update Tool Functions to Use Broker

For each tool function, replace direct API calls with broker methods:

**Example - get_account tool:**

Old:

```python
def execute_tool(tool_name, arguments):
    global trading_client, stock_data_client, crypto_data_client

    if tool_name == "get_account":
        account = trading_client.get_account()
        return {
            "cash": float(account.cash),
            "equity": float(account.equity),
            ...
        }
```

New:

```python
def execute_tool(tool_name, arguments):
    global broker

    if not broker:
        return {"error": "Broker not initialized. Please configure broker in Settings."}

    if tool_name == "get_account":
        return broker.get_account()
```

**Example - get_all_positions:**

Old:

```python
elif tool_name == "get_all_positions":
    positions = trading_client.get_all_positions()
    return [{"symbol": p.symbol, ...} for p in positions]
```

New:

```python
elif tool_name == "get_all_positions":
    return broker.get_positions()
```

**Example - place_crypto_order:**

Old:

```python
elif tool_name == "place_crypto_order":
    symbol = arguments["symbol"]
    side = arguments["side"]
    # ... create Alpaca-specific request
    order = trading_client.submit_order(request)
```

New:

```python
elif tool_name == "place_crypto_order":
    symbol = arguments["symbol"]
    side = arguments["side"]
    qty = arguments.get("qty")
    notional = arguments.get("notional")
    leverage = arguments.get("leverage", 1)  # New! Support leverage

    return broker.place_crypto_order(
        symbol=symbol,
        side=side,
        qty=qty,
        notional=notional,
        leverage=leverage
    )
```

### Step 3: Update Tool Definitions

Add leverage support to crypto tools:

```python
{
    "name": "place_crypto_order",
    "description": "Place a crypto order (market order). Supports leverage on Bybit/Binance.",
    "input_schema": {
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "Crypto symbol (e.g., BTC/USD for Alpaca, BTCUSDT for Bybit/Binance)"
            },
            "side": {
                "type": "string",
                "enum": ["buy", "sell"],
                "description": "Order side"
            },
            "qty": {
                "type": "number",
                "description": "Quantity to buy/sell (optional if notional provided)"
            },
            "notional": {
                "type": "number",
                "description": "Dollar amount to trade (optional if qty provided)"
            },
            "leverage": {
                "type": "integer",
                "description": "Leverage multiplier (1-100 for Bybit, 1-125 for Binance, 1 for Alpaca)"
            }
        },
        "required": ["symbol", "side"]
    }
}
```

### Step 4: Update Frontend

The frontend Settings.tsx has already been updated with:

-   Broker selection dropdown
-   Broker-specific API key fields
-   Conditional rendering based on selected broker

Make sure to update the `/api/chat` endpoint to send broker info:

```typescript
// In TradingChat.tsx or wherever you call /api/initialize
const initializeTrading = async () => {
    const broker = localStorage.getItem("broker") || "alpaca";
    const brokerKey = localStorage.getItem(`${broker}_key`);
    const brokerSecret = localStorage.getItem(`${broker}_secret`);

    const response = await fetch("http://localhost:5002/api/initialize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            broker: broker,
            [`${broker}_key`]: brokerKey,
            [`${broker}_secret`]: brokerSecret,
            paper_mode: localStorage.getItem("paper_mode") === "true",
            // ... AI keys ...
        }),
    });
};
```

### Step 5: Test the Integration

1. **Test Alpaca (existing broker):**

```bash
# Start server
python alpaca-trading-server.py

# In frontend, select Alpaca, save settings, test commands
```

2. **Test Bybit (new broker with leverage):**

```bash
# Get Bybit testnet API keys from https://testnet.bybit.com
# In Settings: Select Bybit, enter testnet keys, enable paper mode
# Test: "Buy $10 of Bitcoin with 10x leverage"
```

3. **Test Binance (new broker with leverage):**

```bash
# Get Binance testnet API keys from https://testnet.binancefuture.com
# In Settings: Select Binance, enter testnet keys, enable paper mode
# Test: "Buy $10 of BTC at 5x leverage"
```

## Quick Migration Guide

### Minimal Changes Approach

If you want to minimize changes to your existing code, you can:

1. Keep all your existing tool functions AS IS for Alpaca
2. Add broker adapter as a wrapper
3. Only modify the initialize endpoint and add broker selection

The broker abstraction layer already wraps the Alpaca API you're using, so existing code will work with minimal changes.

### Key Mapping

| Old (Alpaca-specific)                           | New (Broker Abstraction)          |
| ----------------------------------------------- | --------------------------------- |
| `trading_client.get_account()`                  | `broker.get_account()`            |
| `trading_client.get_all_positions()`            | `broker.get_positions()`          |
| `trading_client.submit_order(req)`              | `broker.place_crypto_order(...)`  |
| `stock_data_client.get_stock_quote(req)`        | `broker.get_stock_quote(symbol)`  |
| `crypto_data_client.get_crypto_latest_bar(req)` | `broker.get_crypto_price(symbol)` |

## Error Handling

Add broker-specific error handling:

```python
def execute_tool(tool_name, arguments):
    global broker

    if not broker:
        return {"error": "Broker not initialized. Please go to Settings and configure your broker."}

    try:
        # Existing tool logic using broker methods
        if tool_name == "place_stock_order":
            # Check if broker supports stocks
            if not broker.supports_stocks():
                return {
                    "error": f"{broker.get_broker_name()} does not support stock trading. "
                            "Please use Alpaca for stocks or trade crypto instead."
                }
            return broker.place_stock_order(...)

    except NotImplementedError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Broker error: {str(e)}"}
```

## Checking Broker Capabilities

```python
# Check what a broker supports
if broker:
    supports_options = broker.supports_options()
    supports_leverage = broker.supports_crypto_leverage()
    max_leverage = broker.get_max_leverage('crypto')
    broker_name = broker.get_broker_name()
```

## Symbol Format Handling

The broker abstraction automatically normalizes symbols:

```python
# User says: "Buy Bitcoin"
# Your code passes: "BTC/USD" or "BTC" or "BTCUSDT"
# Broker normalizes:
#   - Alpaca: BTC/USD
#   - Bybit: BTCUSDT
#   - Binance: BTCUSDT
```

## Complete Example: Tool Execution

```python
def execute_tool(tool_name, arguments):
    """Execute a trading tool using the broker abstraction"""
    global broker

    if not broker:
        return {"error": "Broker not initialized"}

    try:
        if tool_name == "get_account":
            return broker.get_account()

        elif tool_name == "get_all_positions":
            return broker.get_positions()

        elif tool_name == "close_position":
            return broker.close_position(
                symbol=arguments["symbol"],
                qty=arguments.get("qty"),
                percentage=arguments.get("percentage")
            )

        elif tool_name == "get_crypto_latest_bar":
            return broker.get_crypto_price(arguments["symbol"])

        elif tool_name == "place_crypto_order":
            return broker.place_crypto_order(
                symbol=arguments["symbol"],
                side=arguments["side"],
                qty=arguments.get("qty"),
                notional=arguments.get("notional"),
                leverage=arguments.get("leverage", 1)
            )

        elif tool_name == "place_stock_order":
            # Check broker capability first
            if hasattr(broker, 'supports_stocks') and not broker.supports_stocks():
                return {
                    "error": f"{broker.get_broker_name()} doesn't support stocks. Use crypto or switch to Alpaca."
                }

            return broker.place_stock_order(
                symbol=arguments["symbol"],
                side=arguments["side"],
                qty=arguments.get("qty"),
                notional=arguments.get("notional"),
                order_type=arguments.get("order_type", "market"),
                limit_price=arguments.get("limit_price"),
                stop_price=arguments.get("stop_price"),
                time_in_force=arguments.get("time_in_force", "day")
            )

        # ... other tools ...

    except NotImplementedError as e:
        return {"error": f"Feature not supported by {broker.get_broker_name()}: {str(e)}"}
    except Exception as e:
        logging.error(f"Tool execution error: {e}")
        return {"error": str(e)}
```

## Testing Checklist

-   [ ] Server starts without errors
-   [ ] Can initialize with Alpaca (existing functionality works)
-   [ ] Can switch to Bybit in Settings
-   [ ] Can place crypto order with leverage on Bybit
-   [ ] Can switch to Binance in Settings
-   [ ] Can place crypto order with leverage on Binance
-   [ ] Error messages when trying stocks on Bybit/Binance
-   [ ] Symbol format conversion works automatically
-   [ ] Account balance shows correctly for each broker
-   [ ] Positions display correctly for each broker

## Need Help?

See [BROKER-INTEGRATION.md](BROKER-INTEGRATION.md) for:

-   Detailed broker comparison
-   Setup instructions for each broker
-   Leverage trading examples
-   Troubleshooting guide
-   API links and resources
