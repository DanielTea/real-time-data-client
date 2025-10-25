# Polymarket Real-Time Data Client

A real-time WebSocket client for monitoring Polymarket probability changes with a React frontend dashboard, plus AI-powered multi-asset trading (crypto & stocks).

> 🚀 **New here?** See [USAGE.md](USAGE.md) for super simple getting started guide!  
> 📚 **Quick reference?** See [QUICK-REFERENCE.md](QUICK-REFERENCE.md) for all commands and tips!  
> 🔄 **Multi-broker trading?** See [QUICK-START-BROKERS.md](QUICK-START-BROKERS.md) for 5-minute setup!  
> 📖 **Full broker guide?** See [BROKER-INTEGRATION.md](BROKER-INTEGRATION.md) for comprehensive documentation!

## Features

### Polymarket Real-Time Monitoring

-   **Real-time probability monitoring**: Track all probability changes across Polymarket markets
-   **Delta visualization**: See probability changes with color-coded indicators (green/red)
-   **Dynamic category filtering**: Filter buttons generated automatically from actual market data with counts
-   **Keyword search**: Search markets by title, outcome, or description (searches all text fields)
-   **Automatic market cleanup**: Closed markets are automatically removed from the UI
-   **Modern UI**: Clean, responsive React interface with Tailwind CSS and sidebar navigation
-   **Multi-page navigation**: Dashboard, Analytics, Settings, and About pages
-   **Analytics dashboard**: Statistical insights with market breakdowns and trends
-   **WebSocket streaming**: Live updates without page refresh
-   **Local caching**: IndexedDB-based market data cache - no need to re-stream markets on reload
-   **Clickable markets**: Click any card to open the market on Polymarket in a new tab
-   **Market persistence**: Cached markets are restored on app restart
-   **Market descriptions**: Automatically fetched from Polymarket Gamma API and included in JSON view
-   **API-sourced categories**: Categories fetched directly from Polymarket API for accurate classification
-   **Human-readable timestamps**: Both Unix timestamp and formatted time included in market data
-   **Transaction separation**: Transaction-specific data organized in `lastTransaction` object

### 🆕 AI-Powered Multi-Broker Trading with Leverage Support

-   **🔄 Multi-Broker Support**: Switch between Alpaca, Bybit, and Binance brokers in Settings
    -   **Alpaca**: Stocks, Crypto, Options (US-based, regulated)
    -   **Bybit**: Crypto Futures with up to 100x leverage
    -   **Binance**: Crypto Futures with up to 125x leverage
-   **📊 Leverage Trading**: Trade crypto with high leverage on Bybit/Binance (crypto futures)
-   **✅ Same Library**: Uses `alpaca-py` directly - the exact library the [official Alpaca MCP server](https://github.com/alpacahq/alpaca-mcp-server) uses internally
-   **✅ Multi-Turn Conversations**: Implements MCP SDK conversation pattern - AI can use multiple tools in sequence
-   **✅ Polymarket Integration**: AI analyzes real Polymarket prediction markets to inform trading decisions
-   **💎 Crypto Trading**: BTC, ETH, SOL with NO Pattern Day Trading restrictions (24/7 markets)
-   **📈 Stock Trading**: Full equity trading with intelligent PDT (Pattern Day Trading) rule management (Alpaca only)
-   **🤖 Dual Strategy Framework**: Sophisticated strategies for both crypto (intraday) and stocks (swing/day trading)
-   **Natural language trading**: Execute trades using plain English commands via Claude AI or DeepSeek

#### 📊 **Comprehensive Trading Capabilities (27 Tools)**

**Account & Portfolio (3 tools)**

-   `get_account` - View cash, equity, buying power, shorting status
-   `get_all_positions` - List all positions (crypto, stocks, options)
-   `close_position` - Close positions by quantity or percentage

**Crypto Trading (2 tools)**

-   `get_crypto_latest_bar` - Real-time crypto prices (BTC, ETH, SOL, etc.)
-   `place_crypto_order` - Buy/sell crypto (market orders, notional or qty)

**Stock Trading (4 tools)**

-   `place_stock_order` - Market, limit, stop, stop-limit orders (long/short)
-   `get_stock_quote` - Real-time bid/ask quotes
-   `get_stock_bars` - Historical OHLCV data for technical analysis (1Min to 1Day)
-   `get_stock_snapshot` - Complete stock snapshot (latest trade, quote, bars, daily performance)

**Options Trading (5 tools - Advanced)**

-   `get_option_contracts` - Search specific option contracts with detailed filters (strike, expiration, type)
-   `get_option_chain` - Get all available options for a stock (easiest way to see what's tradeable!)
-   `place_option_order` - Buy/sell single call or put contracts (long positions, defined risk)
-   `place_option_spread` - Execute multi-leg strategies (spreads, strangles, iron condors)
-   `close_option_position` - Close existing option positions (auto-determines buy/sell side)

**Order Management (3 tools)**

-   `get_orders` - View open, closed, or all orders
-   `cancel_order` - Cancel specific order by ID
-   `cancel_all_orders` - Cancel all pending orders

**Market Intelligence (2 tools)**

-   `get_news` - Latest market news for specific stocks or general market
-   `get_market_clock` - Check if market is open, next open/close times (critical for stock trading hours)

**Technical Analysis (1 tool)**

-   `get_technical_indicators` - Comprehensive technical analysis with RSI, MACD, SMA/EMA (20/50/200), Bollinger Bands, and volume analysis. Returns interpreted signals and trend analysis.
    -   **Data Sources**: Yahoo Finance (stocks) + Alpaca (crypto) = **Free & Unlimited!**
    -   Works for all stocks (AAPL, TSLA, NVDA, etc.) and crypto (BTC/USD, ETH/USD, SOL/USD)

**Trading Memory (5 tools)**

-   `read_trading_memory` - Read memory with line numbers (shows which lines contain which positions)
-   `edit_trading_memory_lines` - Edit/delete specific line ranges by number (easiest way to manage memory!)
-   `write_trading_memory` - Write/update trading notes (full rewrite)
-   `append_trading_memory` - Append new entries to memory file
-   `clear_trading_memory` - Clear all memory (use with caution)

#### 🎯 **Key Features**

-   **🤖 Auto-Trading**: AI-powered automated trading based on Polymarket market analysis (both crypto & stocks)
-   **📊 Technical Analysis**: Full RSI, MACD, Bollinger Bands for stocks (via Yahoo Finance) & crypto (via Alpaca) - **100% Free!**
-   **📝 Trading Memory**: Persistent AI memory system that tracks open positions, exit strategies, and learns from past trades
-   **📰 Verbose News Logging**: Detailed display of news articles with headlines, summaries, and related symbols in auto-trading logs
-   **🎯 Symbol Format Validation**: Explicit warnings for crypto symbol format (e.g., "BTC/USD" not "BTC") to prevent close_position errors
-   **💎 Crypto Trading (24/7)**: BTC, ETH, SOL - No PDT restrictions, trade intraday freely
-   **📈 Stock Trading (Smart PDT)**:
    -   **Accounts < $25k**: Intelligent swing trading strategy (holds overnight to avoid PDT violations)
    -   **Accounts ≥ $25k**: Unlimited day trading capability
    -   Auto-tracks day trade count and adapts strategy accordingly
-   **📊 Options Trading (Advanced)**:
    -   Single-leg options (long calls/puts with defined risk)
    -   Multi-leg spreads (bull/bear spreads, straddles, strangles, iron condors)
    -   Full options chain analysis
    -   Smart position closing and risk management
-   **📈 Technical Analysis**:
    -   RSI (Relative Strength Index) with overbought/oversold signals
    -   MACD with bullish/bearish crossover detection
    -   Multiple Moving Averages (SMA 20/50/200, EMA 12/26)
    -   Bollinger Bands for volatility analysis
    -   Volume analysis with ratio comparisons
    -   Automated trend detection and signal interpretation
-   **🎯 Dual Strategy Framework**:
    -   **Crypto Strategy**: Aggressive intraday with 24/7 access, perfect when PDT-limited
    -   **Stock Strategy**: Swing trading (2-10 days) or day trading based on PDT status
-   **📊 Polymarket Intelligence**: Maps predictions to tradable assets (crypto, stocks, ETFs, sectors)
-   **Paper trading mode**: Practice trading with paper money (no real funds at risk)
-   **Long & Short**: Full support for long and short positions (stocks & ETFs)
-   **Smart order execution**: AI interprets your commands and executes appropriate trades
-   **Technical analysis**: Historical bars with OHLCV + VWAP data, support/resistance detection
-   **Risk management**: Position sizing, stop-loss, take-profit, portfolio protection rules
-   **Secure API configuration**: Store and manage Alpaca and AI API keys in Settings
-   **Interactive chat interface**: Chat history, typing indicators, and formatted responses
-   **Tool-augmented AI**: AI uses trading tools to interact with Alpaca API
-   **AI Model Choice**: Select between Claude 3.5 Sonnet or DeepSeek (cheaper alternative)

#### 💬 **Example Commands**

**Crypto (Alpaca - Spot)**

-   "Buy $100 of Bitcoin"
-   "Sell all my ETH"
-   "What's the current price of SOL?"

**Crypto with Leverage (Bybit/Binance - Futures)**

-   "Buy $100 of Bitcoin with 10x leverage"
-   "Short ETH with $500 at 20x leverage"
-   "Open a 50x long on BTC with $200"
-   "Close my BTCUSDT position"

**Stocks**

-   "Buy 10 shares of AAPL"
-   "Buy $500 of TSLA stock"
-   "Short 5 shares of NVDA"
-   "Place a limit order to buy 100 SPY at $450"
-   "Set a stop loss at $150 for my AAPL position"
-   "Show me the last 5 days of MSFT price bars"
-   "Get a snapshot of GOOGL with today's performance"
-   "Buy the tech sector ETF QQQ"
-   "What's my day trade count?" (PDT tracking)

**Options**

-   "Show me AAPL call options expiring next month with strike $150-$160"
-   "Buy 1 TSLA put contract at $200 strike expiring in 2 weeks"
-   "What options are available for SPY?"

**Portfolio**

-   "Show my account balance"
-   "What positions do I have?"
-   "Close 50% of my BTC position"
-   "What are my open orders?"
-   "Cancel all my pending orders"

**Market Data**

-   "Get the latest news for AAPL"
-   "What's the market news today?"
-   "Show me the bid/ask spread for MSFT"

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Polymarket    │───▶│  TypeScript      │───▶│   WebSocket     │
│   WebSocket     │    │  Client          │    │   Server        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                          │
                                                          ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Alpaca        │◀───│  Python Trading  │◀───│   React         │
│   Trading API   │    │  Server + Claude │    │   Frontend      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Claude AI API   │
                    └──────────────────┘
```

## Setup

### Prerequisites

-   Node.js 18+
-   Python 3.10+
-   pnpm
-   uv (Python package manager)
-   Polymarket API credentials
-   **Optional for Trading**: Alpaca API keys & Claude API key

### 1. Install Dependencies

```bash
# Install main project dependencies
pnpm install

# Install frontend dependencies
cd frontend
pnpm install
cd ..
```

### 2. Generate API Credentials

```bash
# Create Python environment
uvx venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install py-clob-client python-dotenv

# Generate API credentials
python generate_api_key.py
```

### 3. Configure Environment

Create `keys.env` with your Polymarket credentials:

```env
PRIVATE_KEY=0x73a8432219de966cbdac784d7d026e6ce2bb47239dedd9e64381c1ff24379957
CLOB_API_KEY=001307ad-e84d-041c-015c-8362334df839
CLOB_SECRET=Z1eExXDOPOamA58iqMU0ekWQ3QcPk4_1Oy5uvJXadzU=
CLOB_PASSPHRASE=0c17d5684523c36e96555e74cebc6756928972671b5b22ced2dbd674b0dde001
```

### 4. (Optional) Setup Trading Chat

To use the AI-powered trading chat feature:

```bash
# Create and activate Python virtual environment
source .venv/bin/activate

# Install trading server dependencies
uv pip install -r requirements-trading.txt
```

**Get API Keys:**

-   **Alpaca**: Sign up at [Alpaca Markets](https://alpaca.markets/) and get your API keys (supports paper trading)
-   **AI Model** (choose one):
    -   **Claude**: Get your API key from [Anthropic Console](https://console.anthropic.com/) - $3/M tokens
    -   **DeepSeek**: Get your API key from [DeepSeek Platform](https://platform.deepseek.com/api_keys) - $0.55/M tokens ⚡

Configure the API keys in the frontend Settings page (💡 they're stored securely in your browser).

## Quick Start

> 💡 **Want AI-powered trading?** See [QUICKSTART-TRADING.md](QUICKSTART-TRADING.md) for a 5-minute setup guide!

### 🚀 One-Command Startup (Recommended)

Install everything and start all services with a single command:

```bash
bash start-all.sh
```

### 🧪 Testing Trading Tools

Verify all 18 trading tools are working with live Alpaca endpoints:

```bash
bash verify-tools.sh
```

Or run comprehensive tests:

```bash
source .venv/bin/activate
python test-all-tools.py
```

📊 **Test Results:** See [`TEST-RESULTS.md`](TEST-RESULTS.md) for detailed report showing 100% success rate on all 15 tools.

Or simply:

```bash
./start-all.sh
```

This will:

-   ✅ Check prerequisites (Node.js, Python, pnpm, uv)
-   ✅ Install all dependencies (Node.js + Python)
-   ✅ Start WebSocket server (port 8080)
-   ✅ Start Trading server (port 5000)
-   ✅ Start Frontend (port 5173)
-   ✅ Open browser automatically

To stop all services:

```bash
./stop-all.sh
```

### 📝 Manual Startup (Alternative)

If you prefer to start services individually:

#### Terminal 1: Start the WebSocket Server (Polymarket)

```bash
node websocket-server.js
```

#### Terminal 2: (Optional) Start the Trading Server

```bash
source .venv/bin/activate
python alpaca-trading-server.py
```

This enables the AI trading chat feature. Skip this if you only want Polymarket monitoring.

#### Terminal 3: Start the Frontend

```bash
cd frontend
pnpm dev
```

### Access the Dashboard

Open http://localhost:5173 in your browser to see the real-time dashboard.

## Frontend Navigation

The frontend features a sidebar navigation with multiple pages:

-   **📊 Dashboard** (`/`) - Main page showing all real-time market updates with filtering and search
-   **📄 JSON View** (`/json`) - Real-time market data in JSON format with multi-category selection and keyword filtering
-   **📈 Analytics** (`/analytics`) - Statistical insights including market counts, probability averages, and category breakdowns
-   **💬 Trading Chat** (`/trading`) - 🆕 AI-powered chat interface for crypto & stock trading using natural language
-   **🤖 Auto-Trading** (`/autotrading`) - 🆕 Automated trading based on Polymarket predictions (crypto & stocks with PDT awareness)
-   **⚙️ Settings** (`/settings`) - Configure API keys, WebSocket server, cache, and display preferences
-   **ℹ️ About** (`/about`) - Project information, features list, and technology stack details

---

## Usage

### Polymarket Real-Time Monitoring

#### Start the WebSocket Server

```bash
# Start the bridge server
node websocket-server.js
```

#### Start the Frontend

```bash
# In a new terminal
cd frontend
pnpm dev
```

#### Access the Dashboard

Open http://localhost:5173 in your browser to see the real-time dashboard.

### 💬 Trading Chat (AI-Powered Multi-Asset Trading)

The Trading Chat feature lets you execute cryptocurrency and stock trades using natural language commands powered by Claude AI or DeepSeek.

#### Setup Steps

1. **Configure API Keys** (one-time setup):

    - Navigate to **⚙️ Settings** in the sidebar
    - Enter your **Alpaca API Key** and **Secret Key**
    - **Choose AI Model**: Select between:
        - **Claude 3.5 Sonnet** (Anthropic) - $3/M tokens
        - **DeepSeek-V3.2-Exp** (Reasoning) - $0.55/M tokens ⚡ (Much cheaper!)
    - Enter the corresponding API key:
        - **Claude API Key** (from [Anthropic Console](https://console.anthropic.com/))
        - **DeepSeek API Key** (from [DeepSeek Platform](https://platform.deepseek.com/api_keys))
    - Enable **Paper Trading Mode** (recommended for testing)
    - Click **💾 Save API Keys**

2. **Start the Trading Server**:

    ```bash
    source .venv/bin/activate
    python alpaca-trading-server.py
    ```

    The server will run on `http://localhost:5001`

3. **Open Trading Chat**:
    - Click **💬 Trading Chat** in the sidebar
    - The chat will automatically initialize with your saved API keys

#### Example Commands

Try these natural language commands:

**Crypto (24/7, No PDT)**

```
"buy $100 of Bitcoin"
"buy 0.5 ETH"
"what's the current BTC price?"
"sell all my SOL"
"sell $50 of Ethereum"
```

**Stocks (PDT-Aware)**

```
"buy 10 shares of AAPL"
"buy $500 of TSLA"
"short 5 shares of NVDA"
"what's my day trade count?"
"show me MSFT price bars for last week"
"buy SPY" (S&P 500 ETF)
"buy QQQ" (Nasdaq 100 ETF)
```

**Portfolio Management**

```
"show my account balance"
"what's my portfolio value?"
"show all my positions"
"close 50% of my AAPL position"
"what are my open orders?"
```

#### Features

-   **🤖 AI Model Selection**: Choose between Claude 3.5 Sonnet (Anthropic) or DeepSeek-V3.2-Exp (Reasoning)
-   **💎 Multi-Asset Trading**: Both crypto (BTC, ETH, SOL) and stocks (AAPL, TSLA, NVDA, SPY, QQQ, etc.)
-   **🔐 PDT Protection**: Intelligent handling of Pattern Day Trading rules for accounts <$25k
-   **📊 Account Overview**: Real-time display of portfolio value, cash, buying power, and day trade count
-   **💬 Natural Language**: No need to learn complex trading syntax
-   **🧠 Smart Execution**: AI interprets your intent and executes appropriate trades
-   **📈 Position Tracking**: Check your holdings and performance at any time
-   **💰 Price Quotes**: Get current crypto and stock prices on demand
-   **📝 Paper Trading**: Practice with virtual money before using real funds
-   **🔄 Conversation History**: Full chat history maintained during your session
-   **🛠️ 18 Trading Tools**: Comprehensive toolset for crypto, stocks, options, market data, news, and market status
-   **🎯 Polymarket Integration**: AI analyzes prediction markets to inform trading decisions

#### Security Notes

⚠️ **Important**:

-   API keys are stored in your browser's local storage (never on our servers)
-   Paper trading mode is enabled by default for safety
-   Always verify trade details before confirming in production
-   Never share your API keys with anyone
-   The trading server runs locally on your machine

### Viewing Logs

All server logs are saved to `polymarket-logs.txt`. Use the helper script to view them:

```bash
# Show last 50 lines
./view-logs.sh tail

# Follow logs in real-time
./view-logs.sh follow

# Search for specific markets
./view-logs.sh grep "Bitcoin"

# Show only deleted markets
./view-logs.sh deleted

# Show last 10 market check cycles
./view-logs.sh check

# Clear logs
./view-logs.sh clear
```

Or view directly:

```bash
# View entire log file
cat polymarket-logs.txt

# Follow logs in real-time
tail -f polymarket-logs.txt

# Search logs
grep "Deleted market" polymarket-logs.txt
```

## Project Structure

```
real-time-data-client/
├── start-all.sh               # 🆕 🚀 One-command startup (install + start everything)
├── stop-all.sh                # 🆕 🛑 Stop all services
├── start-trading.sh           # Start trading server only
├── src/                        # TypeScript client source
│   ├── client.ts              # WebSocket client
│   ├── model.ts               # Type definitions
│   └── index.ts               # Main entry point
├── examples/                   # Example scripts
│   ├── quick-connection.ts
│   └── all-markets-probability-changes.ts
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── components/        # React components (Sidebar, Layout, MarketCard, etc.)
│   │   ├── pages/             # Page components (Dashboard, JsonView, Analytics, TradingChat, Settings, About)
│   │   ├── hooks/             # Custom hooks
│   │   ├── db/                # IndexedDB caching
│   │   └── types.ts           # TypeScript types
│   ├── TRADING.md             # 🆕 Trading feature documentation
│   └── package.json
├── websocket-server.js         # Polymarket WebSocket bridge server
├── alpaca-trading-server.py          # 🆕 Python trading server (Alpaca + Claude)
├── requirements-trading.txt   # 🆕 Python dependencies for trading
├── logs/                      # 🆕 Service logs directory
├── view-logs.sh               # Log viewer helper script
├── polymarket-logs.txt        # Server logs (auto-generated)
├── generate_api_key.py         # API credential generator
├── keys.env                   # Polymarket environment variables
├── QUICK-REFERENCE.md         # 🆕 Quick reference card
├── QUICKSTART-TRADING.md      # 🆕 Trading quick start guide
├── CHANGES-TRADING-FEATURE.md # 🆕 Implementation summary
└── package.json
```

## API Reference

### WebSocket Messages

The client receives real-time messages with the following structure:

```typescript
interface WebSocketMessage {
    topic: string;
    type: string;
    timestamp: number;
    connection_id: string;
    payload: any;
}
```

### Market Data

```typescript
interface LastTransaction {
    delta?: number; // Probability change from last update
    deltaStr?: string; // Human-readable delta (e.g., "+2.5%")
    side: "BUY" | "SELL"; // Transaction side
    size: number; // Transaction size
    timestamp: number; // Unix timestamp in milliseconds
    time?: string; // Human-readable time (e.g., "10/19/2025, 15:30:45")
}

interface MarketData {
    title: string;
    outcome: string;
    probability: number;
    marketId?: string;
    category?: string;
    active?: boolean;
    marketUrl?: string;
    description?: string; // Fetched from Polymarket API (may be undefined initially)
    lastTransaction: LastTransaction; // Details of the most recent transaction
}
```

## Configuration

### Dynamic Category Filtering

The dashboard **dynamically generates category buttons** based on the actual markets in your data.

**Category Source (Tags API):**

1. **Tags API** - Fetched from Polymarket Gamma API `/markets/{id}/tags` endpoint (primary source)
2. **Payload category** - Category provided in the WebSocket stream (rarely available)
3. **Uncategorized** - Markets without tags (temporary until API fetch completes)

**How it works:**

-   Each market's first tag label is used as the category (e.g., "Politics", "Sports", "Crypto")
-   Tags are fetched asynchronously and markets are updated via `update_metadata` action
-   Background checker (every 30s) also populates missing categories
-   Official Polymarket tags ensure accurate categorization

**Features:**

-   **Auto-generated buttons** - Only shows categories that have markets
-   **Live counts** - Each button displays the number of markets (e.g., "Sports (203)")
-   **Real-time updates** - Category list and counts update as new markets arrive
-   **Sorted by popularity** - Categories ordered by market count (highest first)
-   **"All" category** - Always shown first with total market count

**Common Categories:** Politics, Sports, Crypto, Finance, Tech, Geopolitics, Culture, Earnings, Economy, World, Elections, and more (varies based on active markets).

### Filtering Options

-   **Category filtering**: Filter by Polymarket market categories
-   **Delta threshold**: Show all probability changes (no minimum threshold)
-   **Market types**: All markets (no filtering)
-   **Update frequency**: Real-time WebSocket updates

### Customization

Modify `examples/all-markets-probability-changes.ts` to:

-   Change the delta threshold
-   Filter specific markets
-   Adjust logging format
-   Add custom processing logic

## Troubleshooting

### Common Issues

1. **Port 8080 already in use (EADDRINUSE)**

    ```bash
    # Kill the process using port 8080
    lsof -ti:8080 | xargs kill -9

    # Then restart the WebSocket server
    node websocket-server.js
    ```

2. **WebSocket connection failed**

    - Check if the bridge server is running
    - Verify port 8080 is available
    - Check firewall settings

3. **No market data**

    - Ensure API credentials are valid
    - Check Polymarket API status
    - Verify network connectivity

4. **Frontend not loading**
    - Check if `pnpm dev` is running
    - Verify port 5173 is available
    - Check browser console for errors

### Logs

-   **Client logs**: Check terminal running `node websocket-server.js`
-   **Frontend logs**: Check browser developer console
-   **TypeScript client**: Check terminal output for WebSocket messages

## Development

### Adding New Features

1. **Backend changes**: Modify TypeScript client in `src/`
2. **Frontend changes**: Update React components in `frontend/src/`
3. **Bridge updates**: Modify `websocket-server.js` for new message types

### Testing

```bash
# Test TypeScript client
pnpm exec ts-node examples/all-markets-probability-changes.ts

# Test frontend
cd frontend
pnpm dev
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Additional Documentation

-   🎯 [USAGE.md](USAGE.md) - **Super simple usage guide** (start here if new!)
-   🚀 [QUICK-REFERENCE.md](QUICK-REFERENCE.md) - **Quick reference card** (commands, URLs, tips)
-   📘 [QUICKSTART-TRADING.md](QUICKSTART-TRADING.md) - Quick 5-minute setup for AI trading chat
-   🤖 [AUTO-TRADING-GUIDE.md](AUTO-TRADING-GUIDE.md) - **Comprehensive auto-trading guide** (crypto & stocks, PDT strategies)
-   📝 [TRADING-MEMORY-GUIDE.md](TRADING-MEMORY-GUIDE.md) - **Trading memory system guide** (persistent AI context & position tracking)
-   📗 [frontend/TRADING.md](frontend/TRADING.md) - Detailed trading chat technical documentation
-   📖 [frontend/README.md](frontend/README.md) - Frontend-specific documentation
-   📋 [CHANGES-TRADING-FEATURE.md](CHANGES-TRADING-FEATURE.md) - Complete implementation summary

## Support

For issues and questions:

-   Check the troubleshooting section
-   Review the logs
-   Read the additional documentation above
-   Open an issue on GitHub
