# Binance Quick Start Guide

Get started trading with Binance Futures (up to 125x leverage!) in 5 minutes.

## 🚀 Why Binance?

- **Maximum Leverage**: Up to 125x on crypto futures
- **Largest Exchange**: Highest liquidity and lowest spreads
- **24/7 Trading**: Crypto markets never close
- **Free Paper Trading**: Test with fake money on testnet

## 📝 Setup Steps

### Step 1: Get API Keys (Paper Trading)

**For Paper Trading (Recommended):**

1. Go to https://testnet.binancefuture.com/
2. Click "Generate HMAC_SHA256 Key" (no account needed!)
3. Copy your API Key and Secret Key
4. Save them somewhere safe

**For Live Trading (After Testing):**

1. Go to https://www.binance.com
2. Complete KYC verification
3. Go to API Management
4. Create new API key with "Futures Trading" enabled
5. Set up 2FA for security

### Step 2: Configure in App

1. Start the multi-broker server:
   ```bash
   cd /Users/danieltremer/.cursor/worktrees/real-time-data-client/XcOrc
   ./start-multi-broker-server.sh
   ```

2. Open the frontend (http://localhost:3000)

3. Go to **Settings** page

4. Select **Binance** from broker dropdown

5. Enter your API Key and Secret

6. Toggle **Paper Trading Mode** ON (for testnet)

7. Click **Save Settings**

### Step 3: Start Trading!

Go to **Trading Chat** and try:

```
"Buy $10 of Bitcoin with 5x leverage"
"What's my account balance?"
"Show my positions"
"Short $50 of ETH at 10x leverage"
"Close my BTC position"
```

## 💡 Trading Examples

### Basic Orders

```
"Buy $100 of Bitcoin"
"Sell all my ETH"
"What's the current price of SOL?"
```

### Leverage Trading

```
"Buy $50 of BTC with 10x leverage"
"Open a 20x long on Ethereum with $100"
"Short $200 of Bitcoin at 15x leverage"
"Buy $300 worth of SOL at 5x leverage"
```

### Position Management

```
"Show my positions"
"What's my unrealized profit?"
"Close 50% of my BTC position"
"Close all my positions"
```

### Risk Management

```
"Set a stop loss at $40000 for my BTC position"
"What's my liquidation price?"
"Reduce my leverage to 5x"
```

## ⚠️ Important Notes

### Leverage Explained

- **5x leverage**: $100 controls $500 worth of crypto
- **10x leverage**: $100 controls $1,000 worth of crypto
- **20x leverage**: $100 controls $2,000 worth of crypto
- **100x leverage**: $100 controls $10,000 worth of crypto

**WARNING**: Higher leverage = Higher risk of liquidation!

### Liquidation Risk

If the price moves against you:
- **5x leverage**: Liquidated at ~20% loss
- **10x leverage**: Liquidated at ~10% loss
- **20x leverage**: Liquidated at ~5% loss
- **100x leverage**: Liquidated at ~1% loss

**Always use stop losses!**

### Symbol Formats

Binance uses symbols without slashes:
- Bitcoin: `BTCUSDT` (not `BTC/USD`)
- Ethereum: `ETHUSDT` (not `ETH/USD`)
- Solana: `SOLUSDT` (not `SOL/USD`)

Don't worry - the app automatically converts them!

### Paper Trading Balance

Binance testnet gives you **10,000 USDT** to practice with.

If you run out:
1. Go to https://testnet.binancefuture.com/
2. Click "Get Test Funds"
3. Your balance will be topped up

## 🎯 Recommended Strategy for Beginners

### Start Conservative

1. **Use paper trading first** (at least 1 week)
2. **Start with low leverage** (2-5x, not 100x!)
3. **Small positions** ($10-50 per trade)
4. **Always set stop losses** (-5% to -10%)
5. **Take profits** (+10%, +20%, +30%)

### Example Conservative Trade

```
"Buy $20 of Bitcoin with 3x leverage"
AI: "Opened 3x long position on BTCUSDT..."

"If BTC drops 5%, close my position"
AI: "Setting stop loss at -5%..."

(Wait for price to move up)

"Close 50% of my BTC position"
AI: "Taking partial profit, closed 50%..."
```

### Scaling Up

Only after consistent profits in paper trading:
1. Increase position sizes gradually
2. Try higher leverage (10-20x) on high-conviction trades
3. Diversify across multiple coins
4. Use technical analysis

## 🔧 Troubleshooting

### "Broker not initialized"
→ Go to Settings and save your Binance API keys

### "Insufficient balance"
→ Check your USDT balance
→ For testnet, get more test funds from Binance

### "Invalid symbol"
→ Use correct format: `BTCUSDT` not `BTC`
→ Or just say "Bitcoin" - the app converts it

### "Order would trigger immediate liquidation"
→ Your leverage is too high for your balance
→ Use lower leverage or larger margin

### API Permission Error
→ Make sure API key has "Futures Trading" enabled
→ Check that you're using testnet keys for paper mode

## 📊 Binance vs Alpaca vs Bybit

| Feature | Binance | Bybit | Alpaca |
|---------|---------|-------|--------|
| **Max Leverage** | 125x | 100x | 1x (spot) |
| **Stocks** | ❌ No | ❌ No | ✅ Yes |
| **Crypto** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Options** | ❌ No | ❌ No | ✅ Yes |
| **Paper Trading** | ✅ Testnet | ✅ Testnet | ✅ Built-in |
| **Best For** | Max leverage | High leverage | Stocks/Options |

## 🎓 Learning Path

### Week 1: Paper Trading Basics
- Practice opening/closing positions
- Test different leverage levels (2x, 5x, 10x)
- Learn symbol formats
- Practice with $10-20 positions

### Week 2: Risk Management
- Always use stop losses
- Practice taking partial profits
- Test position sizing
- Track your win rate

### Week 3: Advanced Strategies
- Try higher leverage on high-conviction trades
- Short selling (bearish bets)
- Multiple positions simultaneously
- Technical analysis integration

### Week 4: Preparation for Live
- Consistent profitability in paper trading
- Understand liquidation risks
- Developed risk management discipline
- Ready to start live with small amounts

## ⚡ Quick Commands Reference

### Account
- "Show my account balance"
- "What's my buying power?"
- "How much margin am I using?"

### Trading
- "Buy $X of [coin] with [Y]x leverage"
- "Short $X of [coin] at [Y]x leverage"
- "Close my [coin] position"
- "Close [X]% of my [coin]"

### Analysis
- "What's the current price of [coin]?"
- "Show me [coin]'s technical indicators"
- "Get the latest crypto news"

### Positions
- "Show my positions"
- "What's my P&L?"
- "Which positions are profitable?"
- "Show my liquidation prices"

## 🚨 Safety Reminders

1. **Never risk more than you can afford to lose**
2. **Start with paper trading**
3. **Use low leverage (2-5x) until experienced**
4. **Always use stop losses**
5. **Don't chase losses**
6. **Take profits regularly**
7. **Understand liquidation before trading live**

## 📚 Resources

- **Binance Testnet**: https://testnet.binancefuture.com/
- **Binance API Docs**: https://binance-docs.github.io/apidocs/
- **Futures Trading Guide**: https://www.binance.com/en/support/faq/futures
- **App Documentation**: [BROKER-INTEGRATION.md](./BROKER-INTEGRATION.md)

## 🎉 Ready to Trade!

You're all set! Remember:

✅ Paper trading is FREE and SAFE
✅ Start with LOW leverage (2-5x)
✅ Always use STOP LOSSES
✅ Take PROFITS regularly
✅ Learn before you earn!

Happy trading! 🚀📈

