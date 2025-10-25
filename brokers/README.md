# Brokers Module

This directory contains the broker abstraction layer for multi-broker trading support.

## Architecture

The broker abstraction uses an **Abstract Factory Pattern** to provide a unified interface for different trading brokers.

### Structure

```
brokers/
├── __init__.py           # Package exports
├── base.py               # BaseBroker abstract class (interface)
├── alpaca_broker.py      # Alpaca implementation
├── bybit_broker.py       # Bybit implementation
├── binance_broker.py     # Binance implementation
├── factory.py            # BrokerFactory for creating instances
└── README.md             # This file
```

## Usage

### Basic Usage

```python
from brokers.factory import BrokerFactory

# Create a broker instance
broker = BrokerFactory.create_broker(
    broker_type='bybit',      # 'alpaca', 'bybit', or 'binance'
    api_key='your_api_key',
    api_secret='your_api_secret',
    paper_mode=True           # Use testnet/paper trading
)

# Get account info
account = broker.get_account()
print(f"Balance: ${account['cash']}")

# Get positions
positions = broker.get_positions()
for pos in positions:
    print(f"{pos['symbol']}: {pos['qty']} @ ${pos['avg_entry_price']}")

# Place crypto order with leverage (Bybit/Binance)
order = broker.place_crypto_order(
    symbol='BTC/USD',
    side='buy',
    notional=100,
    leverage=10  # 10x leverage
)
```

### Get Broker Info

```python
from brokers.factory import BrokerFactory

# Get all supported brokers
supported = BrokerFactory.get_supported_brokers()
# ['alpaca', 'bybit', 'binance']

# Get broker capabilities
info = BrokerFactory.get_broker_info()
# {
#   'alpaca': {'supports_stocks': True, 'max_crypto_leverage': 1, ...},
#   'bybit': {'supports_stocks': False, 'max_crypto_leverage': 100, ...},
#   ...
# }
```

### Check Broker Capabilities

```python
# Check what the current broker supports
if broker.supports_crypto_leverage():
    max_lev = broker.get_max_leverage('crypto')
    print(f"Max leverage: {max_lev}x")

if broker.supports_options():
    print("Options trading supported")

if broker.supports_short_selling():
    print("Short selling supported")
```

## Base Interface (BaseBroker)

All broker implementations must implement these methods:

### Account & Positions

-   `get_account()` - Get account balance and info
-   `get_positions()` - Get all open positions
-   `close_position(symbol, qty?, percentage?)` - Close a position

### Crypto Trading

-   `get_crypto_price(symbol)` - Get current crypto price
-   `place_crypto_order(symbol, side, qty?, notional?, leverage?)` - Place crypto order

### Stock Trading

-   `get_stock_quote(symbol)` - Get stock quote (bid/ask)
-   `place_stock_order(...)` - Place stock order
-   `get_stock_bars(...)` - Get historical price data

### Order Management

-   `get_orders(status)` - Get orders (open/closed/all)
-   `cancel_order(order_id)` - Cancel specific order
-   `cancel_all_orders()` - Cancel all pending orders

### Market Info

-   `get_market_status()` - Check if market is open

### Capabilities (Optional)

-   `supports_options()` - Returns True if broker supports options
-   `supports_crypto_leverage()` - Returns True if broker supports leverage
-   `supports_short_selling()` - Returns True if broker supports shorting
-   `get_max_leverage(asset_class)` - Returns max leverage for asset class
-   `normalize_symbol(symbol, asset_class)` - Normalize symbol format

## Broker Implementations

### AlpacaBroker

**Capabilities**:

-   ✅ Stocks
-   ✅ Crypto (spot)
-   ✅ Options
-   ✅ Short selling
-   ✅ Paper trading (built-in)
-   Leverage: 2x stocks, 1x crypto

**Symbol Format**:

-   Stocks: `AAPL`, `TSLA`
-   Crypto: `BTC/USD`, `ETH/USD` (with slash)

**Notes**:

-   Uses official `alpaca-py` SDK
-   Same library as Alpaca MCP server
-   Regulated US broker

### BybitBroker

**Capabilities**:

-   ❌ Stocks
-   ✅ Crypto (perpetual futures)
-   ❌ Options
-   ✅ Short selling
-   ✅ Paper trading (testnet)
-   Leverage: Up to 100x crypto

**Symbol Format**:

-   Crypto: `BTCUSDT`, `ETHUSDT` (no slash, USDT suffix)

**Notes**:

-   24/7 crypto markets
-   Perpetual futures (no expiration)
-   High leverage available
-   Uses REST API (no official SDK required)

### BinanceBroker

**Capabilities**:

-   ❌ Stocks
-   ✅ Crypto (spot & futures)
-   ❌ Options
-   ✅ Short selling
-   ✅ Paper trading (testnet)
-   Leverage: Up to 125x crypto

**Symbol Format**:

-   Crypto: `BTCUSDT`, `ETHUSDT` (no slash, USDT suffix)

**Notes**:

-   Largest crypto exchange
-   Highest leverage (125x)
-   24/7 crypto markets
-   Uses REST API (no official SDK required)

## Symbol Normalization

Each broker has different symbol formats. The `normalize_symbol()` method handles conversion:

```python
# Alpaca
broker.normalize_symbol('BTC/USD', 'crypto')    # -> 'BTC/USD'
broker.normalize_symbol('BTCUSDT', 'crypto')    # -> 'BTC/USD'

# Bybit
broker.normalize_symbol('BTC/USD', 'crypto')    # -> 'BTCUSDT'
broker.normalize_symbol('BTC', 'crypto')        # -> 'BTCUSDT'

# Binance
broker.normalize_symbol('BTC/USD', 'crypto')    # -> 'BTCUSDT'
broker.normalize_symbol('BTC', 'crypto')        # -> 'BTCUSDT'
```

## Error Handling

Brokers raise standard exceptions:

```python
try:
    order = broker.place_stock_order('AAPL', 'buy', qty=10)
except NotImplementedError:
    # Broker doesn't support stocks (Bybit/Binance)
    print("This broker doesn't support stock trading")
except Exception as e:
    # API error, authentication error, etc.
    print(f"Error: {e}")
```

## Adding a New Broker

To add a new broker:

1. **Create new file** `new_broker.py` in this directory

2. **Implement BaseBroker**:

```python
from .base import BaseBroker

class NewBroker(BaseBroker):
    def __init__(self, api_key, api_secret, paper_mode):
        super().__init__(api_key, api_secret, paper_mode)
        # Initialize API client

    def get_broker_name(self):
        return "NewBroker"

    def get_account(self):
        # Implement account info retrieval
        pass

    # Implement all other required methods...
```

3. **Add to factory** in `factory.py`:

```python
from .new_broker import NewBroker

class BrokerFactory:
    SUPPORTED_BROKERS = {
        'alpaca': AlpacaBroker,
        'bybit': BybitBroker,
        'binance': BinanceBroker,
        'newbroker': NewBroker,  # Add here
    }
```

4. **Update broker info** in `factory.py`:

```python
def get_broker_info(cls):
    return {
        # ... existing brokers ...
        'newbroker': {
            'name': 'New Broker',
            'description': '...',
            'supports_stocks': True,
            'max_crypto_leverage': 10,
            # ...
        }
    }
```

5. **Update frontend** Settings.tsx to add UI option

6. **Test** with paper trading first!

## Testing

### Unit Tests (Recommended)

```python
import unittest
from brokers.factory import BrokerFactory

class TestBrokers(unittest.TestCase):
    def test_alpaca_creation(self):
        broker = BrokerFactory.create_broker('alpaca', 'key', 'secret', True)
        self.assertEqual(broker.get_broker_name(), 'Alpaca')

    def test_bybit_creation(self):
        broker = BrokerFactory.create_broker('bybit', 'key', 'secret', True)
        self.assertTrue(broker.supports_crypto_leverage())
        self.assertEqual(broker.get_max_leverage('crypto'), 100)
```

### Integration Tests

Test with actual testnet accounts:

```python
# Test Bybit testnet
broker = BrokerFactory.create_broker(
    'bybit',
    api_key='testnet_key',
    api_secret='testnet_secret',
    paper_mode=True
)

# Should not raise errors
account = broker.get_account()
assert 'cash' in account
assert 'equity' in account
```

## Best Practices

1. **Always use paper trading first**
2. **Validate API keys before live trading**
3. **Handle NotImplementedError for unsupported features**
4. **Use try-except for all broker calls**
5. **Check broker capabilities before using features**
6. **Normalize symbols for consistency**

## Security

-   Never commit API keys to git
-   Use environment variables for production keys
-   Enable IP restrictions on broker dashboards
-   Use read/trade permissions only (not withdrawals)
-   Start with paper trading to verify security

## Dependencies

### Required

-   `requests` - HTTP client for API calls

### Optional (for better performance)

-   `pybit` - Official Bybit SDK
-   `python-binance` - Official Binance SDK

Install:

```bash
uv pip install requests
# Optional:
# uv pip install pybit python-binance
```

## Documentation

-   [BROKER-INTEGRATION.md](../BROKER-INTEGRATION.md) - User guide
-   [INTEGRATION-STEPS.md](../INTEGRATION-STEPS.md) - Integration guide
-   [base.py](./base.py) - Full BaseBroker interface documentation

## Support

For issues:

1. Check broker's official API documentation
2. Verify API keys and permissions
3. Test in paper trading mode
4. Check application logs
5. Validate symbol formats

## License

Same as parent project.
