# Quick Start - Multi-Broker Trading

Get started with multi-broker support in 5 minutes!

## 🚀 Quick Setup

### Step 1: Install Dependencies (1 minute)

```bash
cd /Users/danieltremer/.cursor/worktrees/real-time-data-client/XcOrc

# Activate virtual environment
source .venv/bin/activate

# Install required package
uv pip install requests
```

### Step 2: Choose Your Broker (2 minutes)

#### Option A: Continue with Alpaca (No Changes Needed)

If you're happy with Alpaca, you don't need to do anything! The system defaults to Alpaca.

#### Option B: Try Bybit for High Leverage Crypto

1. Go to https://testnet.bybit.com
2. Create a free testnet account (no KYC needed)
3. Click "API Keys" → "Create New Key"
4. Copy your API Key and Secret

#### Option C: Try Binance for Maximum Leverage

1. Go to https://testnet.binancefuture.com
2. Create a free testnet account
3. Generate API keys
4. Copy your API Key and Secret

### Step 3: Configure in Settings (1 minute)

1. Start your application
2. Go to **Settings** page
3. In "Trading Broker Configuration":
    - Select your broker from dropdown
    - Enter API key and secret
    - Make sure "Paper Trading Mode" is ON
4. Click **Save Settings**

### Step 4: Start Trading! (1 minute)

Go to the Trading Chat and try these commands:

**With Alpaca:**

```
"Buy $10 of Bitcoin"
"Show my account balance"
```

**With Bybit (leverage enabled):**

```
"Buy $10 of Bitcoin with 5x leverage"
"What's my current position?"
"Close my BTC position"
```

**With Binance (max leverage):**

```
"Open a 10x long on BTC with $20"
"Short $50 of ETH at 5x leverage"
"Show my positions"
```

## ⚡ Quick Commands Reference

### Account Management

-   "Show my account balance"
-   "What positions do I have?"
-   "What's my buying power?"

### Crypto Trading (Any Broker)

-   "Buy $50 of Bitcoin"
-   "Sell all my ETH"
-   "What's the current price of SOL?"

### Leverage Trading (Bybit/Binance Only)

-   "Buy $100 of BTC with 10x leverage"
-   "Short $200 of ETH at 5x leverage"
-   "Open a 20x long on Bitcoin with $50"

### Stock Trading (Alpaca Only)

-   "Buy 5 shares of AAPL"
-   "Sell my TSLA position"
-   "Show me NVDA's price"

### Position Management

-   "Close my BTC position"
-   "Close 50% of my ETH"
-   "Cancel all my orders"

## 🎯 Broker Quick Comparison

| When to Use              | Broker  | Leverage | Assets                  |
| ------------------------ | ------- | -------- | ----------------------- |
| **Stocks & Options**     | Alpaca  | 2x       | Stocks, Crypto, Options |
| **High Leverage Crypto** | Bybit   | **100x** | Crypto Futures          |
| **Maximum Leverage**     | Binance | **125x** | Crypto Futures          |

## ⚠️ Important Notes

### Always Start with Paper Trading!

-   Alpaca: Use paper trading API keys
-   Bybit: Use testnet.bybit.com
-   Binance: Use testnet.binancefuture.com

### Leverage Warning

-   Start with low leverage (2-5x)
-   High leverage (50x+) is extremely risky
-   You can lose your entire position quickly
-   Practice in paper mode first!

### Symbol Formats

Don't worry about symbol formats - the app auto-converts:

-   You say: "Buy Bitcoin"
-   Alpaca uses: BTC/USD
-   Bybit uses: BTCUSDT
-   Binance uses: BTCUSDT

## 🐛 Troubleshooting

### "Broker not initialized"

→ Go to Settings and enter your broker API keys

### "This broker doesn't support stocks"

→ Bybit and Binance only support crypto. Use Alpaca for stocks.

### "Invalid symbol"

→ Just say "Bitcoin" or "BTC" - the app will convert it

### API Permission Error

→ Make sure your API keys have trading permissions enabled

## 📚 Learn More

-   **Full Guide**: [BROKER-INTEGRATION.md](./BROKER-INTEGRATION.md)
-   **Integration Steps**: [INTEGRATION-STEPS.md](./INTEGRATION-STEPS.md)
-   **Implementation Details**: [IMPLEMENTATION-SUMMARY.md](./IMPLEMENTATION-SUMMARY.md)

## 🎓 Example Trading Session

Here's a complete example using Bybit with leverage:

```
You: "What's my account balance?"
AI: "You have $10,000 USDT available in your Bybit testnet account."

You: "Buy $100 of Bitcoin with 10x leverage"
AI: "Opened a 10x leveraged long position on BTCUSDT for $100..."

You: "What's my current position?"
AI: "You have 1 open position: BTCUSDT - Long, $100 notional, 10x leverage..."

You: "If Bitcoin goes up 5%, what's my profit?"
AI: "With 10x leverage, a 5% price increase would give you ~$50 profit (50% return on your $100)."

You: "Close my BTC position"
AI: "Successfully closed BTCUSDT position. Realized P&L: +$27.50"
```

## ✅ Quick Checklist

Before trading:

-   [ ] Installed `requests` dependency
-   [ ] Selected broker in Settings
-   [ ] Entered API keys
-   [ ] Paper trading mode is ON
-   [ ] Saved settings
-   [ ] Tested with small amount

## 🚀 Ready to Trade!

You're all set! Start with small amounts in paper mode and work your way up.

**Remember**:

-   📝 Paper trading is FREE and SAFE
-   🎯 Start with LOW leverage (2-5x)
-   📊 Test thoroughly before going live
-   💰 Never risk more than you can afford to lose

Happy trading! 🎉
