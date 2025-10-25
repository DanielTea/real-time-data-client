# Multi-Broker Integration Guide

## Overview

The application now supports multiple trading brokers, allowing you to switch between different platforms based on your trading needs. Each broker has different capabilities, fee structures, and leverage options.

## Supported Brokers

### 1. **Alpaca** (Default)

-   **Type**: US-based broker
-   **Assets**: Stocks, Crypto, Options
-   **Leverage**:
    -   Stocks: Up to 2x (margin accounts)
    -   Crypto: 1x (spot only)
-   **Short Selling**: ✅ Yes
-   **Paper Trading**: ✅ Yes (Built-in paper trading mode)
-   **Best For**: US stocks, options trading, regulated environment
-   **Website**: https://alpaca.markets
-   **API Docs**: https://alpaca.markets/docs/

**Setup**:

1. Create account at https://alpaca.markets
2. Generate API keys from dashboard
3. For paper trading, use paper trading keys (recommended to start)

---

### 2. **Bybit**

-   **Type**: Crypto derivatives exchange
-   **Assets**: Crypto Perpetual Futures
-   **Leverage**: Up to 100x on futures
-   **Short Selling**: ✅ Yes
-   **Paper Trading**: ✅ Yes (Testnet available)
-   **Best For**: Crypto futures trading with high leverage
-   **Website**: https://www.bybit.com
-   **API Docs**: https://bybit-exchange.github.io/docs/

**Key Features**:

-   24/7 crypto markets
-   Perpetual futures (no expiration)
-   Isolated and cross-margin modes
-   Advanced order types
-   High liquidity

**Setup**:

1. Create account at https://www.bybit.com
2. For **paper trading** (recommended):
    - Visit https://testnet.bybit.com
    - Create testnet account
    - Generate API keys from testnet dashboard
3. For **live trading**:
    - Generate API keys from main account
    - Enable "Contract Trading" permissions

**Important Notes**:

-   Bybit does NOT support stocks - crypto only
-   Uses USDT as collateral
-   Symbols format: `BTCUSDT`, `ETHUSDT` (no slashes)
-   Leverage is applied per position

---

### 3. **Binance**

-   **Type**: Largest crypto exchange
-   **Assets**: Crypto Spot & Futures
-   **Leverage**: Up to 125x on futures
-   **Short Selling**: ✅ Yes
-   **Paper Trading**: ✅ Yes (Testnet available)
-   **Best For**: Crypto trading with maximum leverage, high liquidity
-   **Website**: https://www.binance.com
-   **API Docs**: https://binance-docs.github.io/apidocs/

**Key Features**:

-   Largest crypto exchange by volume
-   Highest leverage (125x)
-   Extensive coin selection
-   Advanced trading features
-   Competitive fees

**Setup**:

1. Create account at https://www.binance.com
2. For **paper trading** (recommended):
    - Use Binance Futures Testnet: https://testnet.binancefuture.com
    - Create testnet account (separate from main account)
    - Generate testnet API keys
3. For **live trading**:
    - Complete KYC verification
    - Generate API keys with futures trading enabled
    - Set up 2FA for security

**Important Notes**:

-   Binance does NOT support stocks - crypto only
-   Different APIs for spot vs futures (this app uses futures)
-   Symbols format: `BTCUSDT`, `ETHUSDT` (no slashes)
-   Requires careful risk management due to high leverage

---

## Broker Comparison Table

| Feature                 | Alpaca      | Bybit    | Binance  |
| ----------------------- | ----------- | -------- | -------- |
| **Stocks**              | ✅ Yes      | ❌ No    | ❌ No    |
| **Crypto Spot**         | ✅ Yes      | ✅ Yes   | ✅ Yes   |
| **Crypto Futures**      | ❌ No       | ✅ Yes   | ✅ Yes   |
| **Options**             | ✅ Yes      | ❌ No    | ❌ No    |
| **Max Crypto Leverage** | 1x          | 100x     | 125x     |
| **Max Stock Leverage**  | 2x          | N/A      | N/A      |
| **Paper Trading**       | ✅ Yes      | ✅ Yes   | ✅ Yes   |
| **24/7 Trading**        | Crypto only | ✅ Yes   | ✅ Yes   |
| **Short Selling**       | ✅ Yes      | ✅ Yes   | ✅ Yes   |
| **US Customers**        | ✅ Yes      | ⚠️ Check | ⚠️ Check |

---

## How to Switch Brokers

### In the Frontend (UI):

1. Open the application
2. Navigate to **Settings** page
3. In the **Trading Broker Configuration** section:
    - Select broker from dropdown
    - Enter API key and secret for selected broker
    - Toggle **Paper Trading Mode** (recommended to start)
4. Click **Save Settings**
5. The trading chat will now use the selected broker

### Configuration Details:

Each broker requires:

-   **API Key**: Public identifier for your account
-   **API Secret**: Private key for authentication (keep secure!)
-   **Paper Mode**: Toggle for testnet/paper trading

---

## Symbol Formats

Different brokers use different symbol formats. The app automatically normalizes them:

### Alpaca:

-   Crypto: `BTC/USD`, `ETH/USD`, `SOL/USD` (with slash)
-   Stocks: `AAPL`, `TSLA`, `NVDA` (standard)

### Bybit:

-   Crypto: `BTCUSDT`, `ETHUSDT`, `SOLUSDT` (no slash, USDT suffix)

### Binance:

-   Crypto: `BTCUSDT`, `ETHUSDT`, `SOLUSDT` (no slash, USDT suffix)

**Note**: You can use any format when trading - the app will convert it automatically for the broker!

---

## Leverage Trading

### What is Leverage?

Leverage allows you to control larger positions with less capital. For example:

-   **10x leverage**: $100 controls $1,000 worth of assets
-   **100x leverage**: $100 controls $10,000 worth of assets

**⚠️ WARNING**: Leverage amplifies both gains AND losses!

### Using Leverage:

**With Bybit or Binance** (crypto futures):

```
"Buy $100 of Bitcoin with 10x leverage"
"Open a 50x leveraged long position on ETH with $200"
"Short Bitcoin at 20x leverage with $500"
```

**With Alpaca** (stocks - margin):

```
"Buy $1000 of AAPL on margin" (2x leverage)
```

### Risk Management:

1. **Start Small**: Use paper trading first
2. **Low Leverage**: Start with 2-5x, not 100x
3. **Stop Losses**: Always set stop losses
4. **Position Sizing**: Never risk more than 1-2% per trade
5. **Understand Liquidation**: High leverage = quick liquidation risk

---

## Architecture

### Broker Abstraction Layer

The app uses a broker abstraction layer to provide a unified interface:

```
brokers/
├── base.py              # BaseBroker abstract class
├── alpaca_broker.py     # Alpaca implementation
├── bybit_broker.py      # Bybit implementation
├── binance_broker.py    # Binance implementation
├── factory.py           # Broker factory
└── __init__.py
```

### How It Works:

1. **BaseBroker** defines the interface all brokers must implement
2. Each broker (Alpaca, Bybit, Binance) implements this interface
3. **BrokerFactory** creates the correct broker based on settings
4. Trading tools use the broker abstraction, not direct APIs

This means:

-   ✅ Easy to add new brokers
-   ✅ Consistent tool behavior across brokers
-   ✅ Symbol format conversion handled automatically
-   ✅ Broker-specific features exposed when available

---

## API Endpoints

### New Endpoints:

**GET /api/brokers**

-   Returns list of supported brokers and their capabilities
-   Response:

```json
{
  "alpaca": {
    "name": "Alpaca",
    "supports_stocks": true,
    "supports_crypto": true,
    "max_crypto_leverage": 1,
    ...
  },
  ...
}
```

**POST /api/initialize**

-   Now accepts `broker_type` parameter
-   Request:

```json
{
    "broker_type": "bybit",
    "broker_key": "your_api_key",
    "broker_secret": "your_api_secret",
    "paper_mode": true,
    "claude_key": "...",
    "ai_model": "claude"
}
```

---

## Trading Examples by Broker

### Alpaca (Stocks + Crypto):

```
"Buy 10 shares of AAPL"
"Buy $100 of Bitcoin"
"Sell 5 shares of TSLA"
"Buy AAPL call option at $150 strike"
"Show my stock positions"
```

### Bybit (Crypto Futures):

```
"Buy $100 of Bitcoin with 10x leverage"
"Short ETH with $500 at 20x leverage"
"Close my BTC position"
"What's the current price of SOL?"
"Show my crypto positions"
```

### Binance (Crypto Futures):

```
"Open a 50x long on Bitcoin with $200"
"Short $1000 of Ethereum at 25x leverage"
"Close 50% of my BTC position"
"Buy $500 worth of SOL at 10x leverage"
```

---

## Troubleshooting

### "Broker not initialized" Error:

-   Go to Settings and save your broker credentials
-   Make sure API keys are correct
-   Check that paper mode matches your API key type

### "Symbol not found" Error:

-   Check symbol format for your broker
-   Bybit/Binance: Use `BTCUSDT` not `BTC/USD`
-   Alpaca: Use `BTC/USD` for crypto, `AAPL` for stocks

### "Insufficient balance" Error:

-   Check your account balance
-   Remember leverage doesn't create more buying power for free
-   For testnet, you may need to claim testnet funds

### API Permission Errors:

-   Verify API keys have trading permissions enabled
-   For Bybit/Binance, ensure futures trading is enabled
-   Check that API keys match paper/live mode setting

### Stock Trading on Crypto Brokers:

-   Bybit and Binance do NOT support stocks
-   Use Alpaca for stock trading
-   Switch broker in Settings if you need stocks

---

## Security Best Practices

1. **API Keys**:

    - Never share your API keys
    - Use paper trading keys to start
    - Set IP restrictions in broker dashboard
    - Enable read/trade permissions only (not withdrawals)

2. **Paper Trading First**:

    - Always test with paper trading
    - Understand the broker before going live
    - Practice with leverage in paper mode

3. **Environment**:
    - Store API keys in environment variables
    - Don't commit keys to git
    - Use different keys for dev/prod

---

## Migration Guide

### Switching from Alpaca to Bybit:

1. Create Bybit testnet account
2. Generate testnet API keys
3. In Settings:
    - Select "Bybit" as broker
    - Enter Bybit API keys
    - Keep paper mode ON
4. Update your commands:
    - Crypto symbols: `BTC/USD` → `BTCUSDT`
    - Add leverage if desired: "Buy $100 BTC at 10x"
    - Stock trading not available

### Switching from Bybit to Binance:

-   Similar setup process
-   Symbols stay the same (`BTCUSDT` format)
-   Higher max leverage (125x vs 100x)
-   Different fee structure

---

## Adding New Brokers (For Developers)

To add a new broker:

1. Create new file in `brokers/` directory: `new_broker.py`
2. Implement `BaseBroker` interface
3. Add to `BrokerFactory.SUPPORTED_BROKERS`
4. Update frontend dropdown in `Settings.tsx`
5. Add credentials storage in Settings
6. Update this documentation

See `brokers/base.py` for required methods.

---

## FAQ

**Q: Which broker should I use?**
A:

-   Want stocks + crypto? → Alpaca
-   Want high leverage crypto? → Bybit or Binance
-   Want options trading? → Alpaca

**Q: Is paper trading safe?**
A: Yes! Paper trading uses testnet/demo accounts with fake money. No real funds at risk.

**Q: Can I use multiple brokers?**
A: Not simultaneously in one instance. You can switch brokers in Settings.

**Q: What about fees?**
A: Each broker has different fee structures. Check their websites:

-   Alpaca: Commission-free stocks/crypto
-   Bybit: Maker/taker fees on futures
-   Binance: Competitive trading fees

**Q: Do I need KYC?**
A:

-   Paper trading: Usually no
-   Live trading: Yes for all brokers

**Q: Which broker has the best API?**
A: All three have excellent APIs. Alpaca is most beginner-friendly.

---

## Resources

### Alpaca:

-   Documentation: https://alpaca.markets/docs/
-   Paper Trading: https://app.alpaca.markets/paper/dashboard/overview

### Bybit:

-   Documentation: https://bybit-exchange.github.io/docs/
-   Testnet: https://testnet.bybit.com/
-   API Management: https://testnet.bybit.com/app/user/api-management

### Binance:

-   Documentation: https://binance-docs.github.io/apidocs/
-   Futures Testnet: https://testnet.binancefuture.com/
-   Trading Guide: https://www.binance.com/en/support/faq/futures

---

## Support

For issues or questions:

1. Check broker's official documentation
2. Verify API keys and permissions
3. Test in paper trading mode first
4. Check application logs for errors

**Remember**: Always start with paper trading and low leverage!
