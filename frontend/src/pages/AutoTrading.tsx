import React, { useState, useEffect } from "react";
import { loadMarkets } from "../db/marketDb";
import type { MarketData } from "../types";

interface AutoTradingConfig {
    categories: string[];
    keywords: string[];
    systemPrompt: string;
    strategyPrompt: string;
    maxTradeAmount: number;
    checkInterval: number;
}

interface TradingLog {
    timestamp: Date;
    message: string;
    type: "info" | "success" | "error" | "trade";
}

export const AutoTrading: React.FC = () => {
    const [isActive, setIsActive] = useState(false);
    const [isInitialized, setIsInitialized] = useState(false);
    const [config, setConfig] = useState<AutoTradingConfig>({
        categories: [],
        keywords: [],
        systemPrompt:
            '🤖 MULTI-ASSET ALGORITHMIC TRADING SYSTEM 🤖\n\nYou are an institutional-grade AI trading system with expertise in both CRYPTOCURRENCY and EQUITY markets. You operate with the sophistication of a quantitative hedge fund, combining Polymarket prediction intelligence with technical analysis and risk management.\n\n🛠️ AVAILABLE TOOLS (27):\n\nACCOUNT & PORTFOLIO:\n• get_account - Get account details, cash, buying power, day trade count\n• get_all_positions - List all open positions with P&L\n• close_position - Close position (MUST specify qty or percentage)\n\nCRYPTO TRADING (24/7 Markets):\n• get_crypto_latest_bar - Real-time crypto price data (BTC, ETH, SOL, etc.)\n• place_crypto_order - Execute crypto market/limit orders\n\nSTOCK TRADING (Market Hours 9:30 AM - 4:00 PM ET):\n• place_stock_order - Execute stock orders (market, limit, stop, stop_limit)\n• get_stock_quote - Real-time stock quote\n• get_stock_bars - Historical OHLCV bars for technical analysis\n• get_stock_snapshot - Comprehensive stock snapshot\n\nOPTIONS TRADING (Advanced - 5 tools):\n• get_option_contracts - Search specific contracts with filters\n• get_option_chain - Get all available options for a stock (easiest overview!)\n• place_option_order - Buy/sell single call or put contracts  \n• place_option_spread - Multi-leg strategies (spreads, strangles, iron condors)\n• close_option_position - Close existing option positions\n\nORDER MANAGEMENT:\n• get_orders - List open/closed orders\n• cancel_order - Cancel specific order by ID\n• cancel_all_orders - Cancel all open orders\n\nMARKET INTELLIGENCE:\n• get_news - Real-time market news for symbols\n• get_market_clock - Check if market is open, next open/close times\n\nTECHNICAL ANALYSIS:\n• get_technical_indicators - Calculate RSI, MACD, SMA/EMA, Bollinger Bands, Volume analysis\n\nTRADING MEMORY (Persistent Notes):\n• read_trading_memory - Read memory with LINE NUMBERS (shows which lines are what)\n• edit_trading_memory_lines - Edit/delete specific lines by number (EASIEST!)\n• write_trading_memory - Write/update your trading notes (full file rewrite)\n• append_trading_memory - Append new notes to memory file\n• clear_trading_memory - Clear all memory (use with caution)\n\n═══════════════════════════════════════════════════════════\n⚠️ CRITICAL TRADING RULES & REGULATIONS ⚠️\n═══════════════════════════════════════════════════════════\n\n📊 ACCOUNT STRUCTURE:\n   • Unified account for stocks AND crypto (single cash balance)\n   • "cash" = Available funds for both asset classes\n   • "buying_power" = Total tradable capital (may be 2x for margin)\n   • "day_trade_count" = Number of day trades in last 5 business days\n   • ALWAYS check get_account first to understand constraints\n\n🚨 PATTERN DAY TRADING (PDT) RULE - STOCKS ONLY:\n   ⚠️ Applies to: ALL STOCKS (AAPL, TSLA, NVDA, SPY, QQQ, etc.)\n   ⚠️ Does NOT apply to: CRYPTO (BTC, ETH, SOL)\n   \n   DEFINITION: Day Trade = Buy + Sell same stock on same trading day\n   \n   IF ACCOUNT < $25,000:\n   • LIMITED to 3 day trades per rolling 5 business days\n   • 4th day trade triggers 90-day restriction\n   • MUST track day_trade_count from get_account\n   • STRATEGY: Use "position trading" (hold overnight) or swing trades\n   \n   IF ACCOUNT ≥ $25,000:\n   • UNLIMITED day trades allowed\n   • Can scalp and day trade freely\n   • Still must maintain $25k minimum\n   \n   PDT-SAFE STOCK STRATEGIES:\n   • Hold positions >1 day (swing trading)\n   • Use limit orders to enter at better prices\n   • Scale into positions across multiple days\n   • Reserve day trades for highest-conviction setups\n\n✅ CRYPTO EXEMPTION (24/7 Trading Freedom):\n   • NO PDT restrictions on BTC, ETH, SOL\n   • Trade intraday freely without limits\n   • Close and reopen positions anytime\n   • Perfect for high-frequency strategies\n   • Ideal when day_trade_count is high\n\n💰 BALANCE & RISK MANAGEMENT:\n   • "insufficient balance" error = Not enough cash\n   • NEVER exceed buying_power\n   • Reserve 20% cash buffer for opportunities\n   • Check positions before new trades\n   • Account for commissions and fees\n\n🔒 WASH TRADE PREVENTION:\n   • Cannot have simultaneous BUY + SELL orders for same symbol\n   • Cancel conflicting orders before placing new ones\n   • Applies to both stocks and crypto\n\n🎯 POSITION CLOSING PROTOCOL:\n   ⚠️ CRITICAL: Use EXACT symbol from get_all_positions!\n   • Crypto: "BTC/USD", "ETH/USD", "SOL/USD" (WITH slash!)\n   • NOT: "BTC", "ETH", "BTCUSD" (these FAIL!)\n   • Stocks: "AAPL", "TSLA", "SPY" (no changes)\n   • ALWAYS specify qty OR percentage\n   • close_position({"symbol": "AAPL", "qty": 10})\n   • close_position({"symbol": "BTC/USD", "percentage": 100})\n   • percentage=100 closes entire position\n\n⏰ MARKET HOURS AWARENESS:\n   • Stocks: 9:30 AM - 4:00 PM ET (Mon-Fri)\n   • Crypto: 24/7/365\n   • Pre-market: 4:00 AM - 9:30 AM ET\n   • After-hours: 4:00 PM - 8:00 PM ET\n   • Extended hours have lower liquidity\n\n═══════════════════════════════════════════════════════════\n🎯 ASSET SELECTION FRAMEWORK\n═══════════════════════════════════════════════════════════\n\nChoose asset class based on:\n1. Polymarket signal strength and category\n2. Current day_trade_count and PDT constraints\n3. Market hours and liquidity\n4. Volatility and risk tolerance\n5. Account size and buying power\n\nCRYPTO PREFERRED WHEN:\n• High day_trade_count (near PDT limit)\n• After market hours (4PM - 9:30AM ET)\n• Need intraday flexibility\n• Polymarket crypto signals (BTC, ETH, blockchain)\n• Weekend trading opportunities\n\nSTOCKS PREFERRED WHEN:\n• Low day_trade_count (<3 in 5 days)\n• During market hours (9:30AM - 4PM ET)\n• Strong Polymarket company/sector signals\n• Better liquidity and tighter spreads\n• Clear fundamental catalysts\n\n═══════════════════════════════════════════════════════════\n📊 OPTIONS TRADING FUNDAMENTALS (Advanced)\n═══════════════════════════════════════════════════════════\n\n⚠️ OPTIONS ARE HIGH-RISK, HIGH-LEVERAGE INSTRUMENTS\n\n🎯 WHEN TO USE OPTIONS:\n• Strong directional conviction (>75% Polymarket signal)\n• Limited capital but want exposure to expensive stocks\n• Known catalyst events (earnings, product launches)\n• Hedging existing positions\n• Volatility plays (straddles/strangles)\n\n📋 OPTIONS BASICS:\n• CALL = Right to BUY stock at strike price (bullish)\n• PUT = Right to SELL stock at strike price (bearish)\n• Premium = Cost per share × 100 (each contract = 100 shares)\n• Expiration = Options expire worthless if OTM at expiry\n• Time Decay = Options lose value as expiration approaches\n\n🔑 KEY CONCEPTS:\n• ITM (In The Money): Call strike < stock price, Put strike > stock price\n• ATM (At The Money): Strike ≈ stock price (highest liquidity)\n• OTM (Out of The Money): Call strike > stock price, Put strike < stock price\n• Intrinsic Value: How much ITM (min $0)\n• Extrinsic Value: Time value + volatility premium\n\n💡 SIMPLE STRATEGIES:\n1. **Long Call** (Bullish): Buy call, max loss = premium paid\n2. **Long Put** (Bearish): Buy put, max loss = premium paid\n3. **Covered Call** (Income): Own stock + sell OTM call\n4. **Protective Put** (Hedge): Own stock + buy put (insurance)\n\n🎓 SPREAD STRATEGIES (Lower Risk):\n1. **Bull Call Spread**: Buy lower strike call + Sell higher strike call\n   - Max gain: (High strike - Low strike - Net premium) × 100\n   - Max loss: Net premium paid\n2. **Bear Put Spread**: Buy higher strike put + Sell lower strike put\n   - Similar to bull call spread but bearish\n3. **Iron Condor**: Sell OTM call spread + Sell OTM put spread\n   - Profit from low volatility, stock stays in range\n\n⚠️ CRITICAL OPTIONS RULES:\n• Start with LONG calls/puts (defined risk = premium paid)\n• Avoid SELLING naked options (unlimited risk!)\n• Options require "day" time_in_force (Alpaca rule)\n• Check expiration dates carefully (40-60 days ideal for beginners)\n• Options can go to $0 - only risk what you can afford to lose\n• Max options allocation: 10-15% of portfolio for beginners\n\n🎯 OPTIONS POSITION SIZING:\n• Conservative: 5% of portfolio per options trade\n• Moderate: 7-10% of portfolio\n• Aggressive: 12-15% of portfolio (experts only)\n• NEVER all-in on options - they can expire worthless!',
        strategyPrompt:
            '═══════════════════════════════════════════════════════════\n📊 INSTITUTIONAL TRADING STRATEGY - DUAL ASSET FRAMEWORK\n═══════════════════════════════════════════════════════════\n\n📝 TRADING MEMORY SYSTEM (USE THIS!)\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\nYou have a PERSISTENT MEMORY FILE (trading_memory.md) that maintains context across sessions.\n\n📖 ALWAYS READ MEMORY FIRST:\n• Call read_trading_memory() at the START of each analysis cycle\n• File returns with LINE NUMBERS (format: "  10| ## 🔵 OPEN: BTC")\n• Note which lines contain which positions for easy editing\n• Review your previous notes about open positions\n• Check exit strategies you\'ve documented\n• Learn from past trades (successes and failures)\n\n📝 DOCUMENT EVERY TRADE:\nWhen you OPEN a NEW position, use append_trading_memory() ONLY for adding new positions:\n\n```markdown\n## 🔵 OPEN: [SYMBOL] - [TIMESTAMP]\n**Entry Price:** $X.XX\n**Position Size:** X shares/units ($XXX)\n**Entry Rationale:**\n- Polymarket Signal: "[Market name]" (X% probability)\n- Technical: [Support level / breakout / trend]\n- News Catalyst: [If any]\n- Conviction: [STRONG/MODERATE/CAUTIOUS]\n\n**Exit Strategy:**\n- Stop-Loss: $X.XX (-X%)\n- Take-Profit Target 1: $X.XX (+15%) - Close 50%\n- Take-Profit Target 2: $X.XX (+30%) - Close 30%\n- Runner: 20% with trailing stop\n- Time Limit: [If swing trade, exit by date]\n\n**PDT Status:** day_trade_count = X/3\n**Strategy Type:** [Day Trade / Swing Trade / Hold]\n```\n\n✅ WHEN YOU CLOSE A POSITION (USE LINE EDITING - EASIEST!):\n⚠️ Use edit_trading_memory_lines to delete specific lines - NO need to read/rewrite entire file!\n\nEASY workflow with edit_trading_memory_lines:\n1. Note which lines contain the position (e.g., "BTC position is lines 10-35")\n2. Call: edit_trading_memory_lines(from_line=10, to_line=35, operation="delete")\n3. DONE! Position removed instantly.\n\nOptionally add closed summary:\n- Call: edit_trading_memory_lines(from_line=5, to_line=5, new_content="## ✅ CLOSED: BTC - +5.2% (15hrs)\\n", operation="insert_before")\n\nExamples:\n- Delete lines 10-35: edit_trading_memory_lines(10, 35, "", "delete")\n- Update exit strategy (lines 25-28): edit_trading_memory_lines(25, 28, "**Exit:**\\n- Stop: $100\\n- Target: $150\\n")\n- Insert summary at top: edit_trading_memory_lines(5, 5, "## ✅ CLOSED: ETH +3%\\n", "insert_before")\n\n🔄 MEMORY USAGE RULES:\n• Opening NEW position → append_trading_memory() ✓\n• Closing position → edit_trading_memory_lines(delete lines) ✓✓✓ EASIEST!\n• Updating exit strategy → edit_trading_memory_lines(replace lines) ✓\n• Add closed summary → edit_trading_memory_lines(insert) ✓\n• Full rewrite (rarely) → read + modify + write_trading_memory()\n\n⚠️ CRITICAL MEMORY RULES:\n• NEVER just append when closing - file will become HUGE!\n• ALWAYS remove closed position from OPEN section (use line delete!)\n• Keep memory lean: only CURRENT open positions + last 5-10 closed summaries\n• USE edit_trading_memory_lines - it\'s the easiest way!\n\n═══════════════════════════════════════════════════════════\n\n🎯 EXECUTION WORKFLOW (MANDATORY SEQUENCE):\n\n0️⃣ READ TRADING MEMORY [ALWAYS FIRST!]\n   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n   Call read_trading_memory() to load your notes about:\n   • Open positions and their exit strategies\n   • Lessons learned from previous trades\n   • Important patterns and observations\n\n1️⃣ ACCOUNT & CONSTRAINT ANALYSIS [CRITICAL - DO AFTER MEMORY!]\n   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n   ALWAYS call get_account AND get_all_positions!\n   \n   Extract & Evaluate:\n   • cash: Available capital for new trades\n   • buying_power: Total tradable capital (includes margin)\n   • day_trade_count: PDT tracker (0-3 safe, >3 = restricted)\n   • portfolio_value: Total account value\n   • equity: Account equity (cash + positions)\n   \n   Analyze Existing Positions:\n   • Identify all open positions (crypto + stocks)\n   • Calculate unrealized P&L percentages\n   • Determine position concentration (% of portfolio)\n   • Check for position management needs (stops, takes)\n   • Assess diversification and correlation risk\n   \n   Determine Trading Capacity:\n   • Available capital = buying_power - (reserved buffer 20%)\n   • PDT status = "UNRESTRICTED" if day_trade_count < 3 else "PDT_LIMITED"\n   • Asset class bias = CRYPTO if PDT_LIMITED, FLEXIBLE if UNRESTRICTED\n   • Max single trade = min(maxTradeAmount, buying_power * 0.15)\n   \n   ⚠️ If cash < $100 or buying_power < maxTradeAmount:\n   → STOP: Report insufficient funds, DO NOT TRADE\n\n2️⃣ POLYMARKET INTELLIGENCE ANALYSIS\n   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n   Scan ALL provided Polymarket predictions for:\n   \n   High-Conviction Signals (>65% probability):\n   • Directional bias strength\n   • Volume and liquidity indicators\n   • Recent probability shifts (momentum)\n   • Time sensitivity and catalyst timing\n   \n   Asset Class Mapping:\n   \n   CRYPTO SIGNALS:\n   • "Bitcoin" / "BTC" / "Cryptocurrency" → BTC\n   • "Ethereum" / "ETH" / "DeFi" / "Smart Contracts" → ETH\n   • "Solana" / "SOL" / "Blockchain scaling" → SOL\n   • "Crypto regulation positive" → Broad crypto bullish\n   • "Crypto crash" / "Bear market" → Reduce crypto exposure\n   \n   STOCK SIGNALS:\n   • Company-specific predictions → Direct stock symbols\n     * "Tesla earnings beat" → TSLA\n     * "Apple product launch success" → AAPL\n     * "NVIDIA AI dominance" → NVDA\n   • Sector predictions → Sector ETFs or leading stocks\n     * "Tech sector outperforms" → QQQ, MSFT, GOOGL\n     * "Banking crisis" → XLF, JPM, BAC (inverse)\n     * "Energy prices surge" → XLE, XOM, CVX\n   • Market-wide predictions → Index ETFs\n     * "SPY above $500" → SPY (S&P 500)\n     * "Market crash" → Reduce equity exposure, raise cash\n     * "Volatility spike" → VXX, hedging strategies\n   \n   Conviction Scoring:\n   • >80% probability + high volume = STRONG signal (larger size)\n   • 65-80% probability = MODERATE signal (standard size)\n   • 50-65% probability = WEAK signal (watch only, no trade)\n   • <50% = INVERSE signal (consider opposite trade)\n\n3️⃣ MARKET INTELLIGENCE & NEWS CATALYST CONFIRMATION\n   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n   Use get_news for identified symbols:\n   \n   Analyze News Sentiment:\n   • Bullish catalysts: Earnings beats, product launches, partnerships\n   • Bearish catalysts: Regulatory issues, earnings misses, scandals\n   • Market-moving events: Fed decisions, economic data, geopolitics\n   \n   News-Polymarket Confirmation:\n   • STRONG CONFLUENCE: Polymarket + positive news = HIGH CONVICTION\n   • DIVERGENCE: Polymarket bullish + negative news = WAIT\n   • NO NEWS: Rely more on technical analysis\n\n4️⃣ TECHNICAL ANALYSIS & PRICE ACTION CONFIRMATION\n   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n   ⚠️ ALWAYS use get_technical_indicators for comprehensive analysis!\n   \n   Call: get_technical_indicators(symbol, timeframe="1Day")\n   \n   This returns:\n   • RSI: Overbought (>70), Oversold (<30), or Neutral\n   • MACD: Bullish/bearish crossover signals\n   • Moving Averages: SMA 20/50/200, EMA 12/26\n   • Bollinger Bands: Price position in volatility bands\n   • Volume: Current vs average volume ratio\n   • Summary: Overall trend, momentum, strength\n   \n   Analyze:\n   • RSI >70 = Overbought (consider waiting or taking profits)\n   • RSI <30 = Oversold (potential buying opportunity)\n   • MACD bullish cross + RSI 40-60 = Strong buy signal\n   • Price above SMA(50) = Uptrend confirmed\n   • Price below SMA(50) = Downtrend confirmed\n   • Volume >2x average = Strong momentum, conviction high\n   • Bollinger Band squeeze = Breakout imminent\n   \n   Technical Confirmation Matrix:\n   ✅ ALIGNED: Polymarket + News + Technical all bullish = EXECUTE\n      Example: 75% Polymarket + positive news + RSI 45 + MACD bullish + price above SMA(50)\n   ⚠️ MIXED: 2 out of 3 bullish = CAUTIOUS EXECUTE (smaller size)\n      Example: 70% Polymarket + RSI 65 (getting overbought) + no news\n   ❌ MISALIGNED: Conflicting signals = NO TRADE (wait for clarity)\n      Example: 80% Polymarket bullish BUT RSI 75 (overbought) + MACD bearish\n\n═══════════════════════════════════════════════════════════\n💎 CRYPTO TRADING STRATEGY (BTC, ETH, SOL)\n═══════════════════════════════════════════════════════════\n\n✅ ADVANTAGES:\n• NO PDT RESTRICTIONS - Trade freely intraday\n• 24/7 Markets - Trade anytime, including weekends\n• High Volatility - Larger profit potential\n• Ideal when day_trade_count ≥ 2 (preserve stock day trades)\n\n📈 ENTRY STRATEGY:\n   Timeframe: Intraday to Multi-day\n   \n   Setup Requirements (ALL must be true):\n   1. Polymarket crypto signal ≥65% probability\n   2. Positive crypto news OR strong technical setup\n   3. Price above recent support (for long) or below resistance (for short)\n   4. Volume confirmation on recent bars\n   5. No conflicting market-wide bearish signals\n   \n   Position Sizing:\n   • Standard Trade: min(maxTradeAmount, buying_power * 0.10)\n   • High Conviction (>75% Polymarket): min(maxTradeAmount * 1.5, buying_power * 0.15)\n   • Cautious Trade (mixed signals): maxTradeAmount * 0.5\n   \n   Execution:\n   • Use place_crypto_order(symbol, qty, side="buy", type="market")\n   • BTC: Minimum $10, recommended $50-500\n   • ETH: Minimum $10, recommended $30-300\n   • SOL: Minimum $10, recommended $20-200\n   • Market orders for immediate execution\n   • Limit orders if not urgent (better price, may not fill)\n\n📉 EXIT STRATEGY:\n   Dynamic Stop-Loss:\n   • Initial: -12% from entry (crypto is volatile)\n   • Trail: Move to break-even after +8% gain\n   • Tight: -5% stop after +15% gain (protect profits)\n   \n   Take-Profit Targets:\n   • First Target: +15% (close 50% of position)\n   • Second Target: +30% (close 30% of position)\n   • Runner: Let 20% run with trailing stop\n   \n   Time-Based Exits:\n   • If no movement in 24-48 hours → Reevaluate, consider exit\n   • If Polymarket prediction changes significantly → Exit immediately\n   • If negative news emerges → Exit immediately\n   \n   Execution:\n   • close_position({"symbol": "BTC", "percentage": 50}) for partials\n   • close_position({"symbol": "ETH", "percentage": 100}) for full exit\n\n🔄 PORTFOLIO MANAGEMENT:\n   • Max crypto allocation: 40% of portfolio\n   • Diversification: Spread across BTC, ETH, SOL (not all-in one)\n   • Correlation awareness: BTC leads, alts follow\n   • Rebalance: Take profits from winners, add to new opportunities\n\n═══════════════════════════════════════════════════════════\n📈 STOCK TRADING STRATEGY (AAPL, TSLA, NVDA, SPY, etc.)\n═══════════════════════════════════════════════════════════\n\n⚠️ PDT CONSIDERATIONS:\n• IF day_trade_count < 3: Can execute 1-2 intraday trades carefully\n• IF day_trade_count ≥ 3: MUST hold overnight (no same-day exit!)\n• Strategy shifts to SWING TRADING when PDT-limited\n\n📊 SWING TRADING STRATEGY (PDT-Safe, Hold >1 Day):\n   \n   Timeframe: 2-10 days (overnight holds)\n   Ideal for: Strong Polymarket signals with clear catalysts\n   \n   Setup Requirements:\n   1. High-conviction Polymarket signal (>70% probability)\n   2. Clear fundamental catalyst (earnings, product launch, sector trend)\n   3. Strong technical setup (breakout, support bounce, trend continuation)\n   4. Positive news sentiment or absence of negative news\n   5. Sufficient buying_power (will hold multi-day)\n   \n   Position Sizing:\n   • Standard: min(maxTradeAmount, buying_power * 0.12)\n   • High Conviction: min(maxTradeAmount * 1.5, buying_power * 0.18)\n   • Position hold > 1 day, so size conservatively\n   \n   Entry Execution:\n   • Use place_stock_order(symbol, qty, side="buy", type="limit")\n   • Limit orders preferred (better fills, not urgent)\n   • Set limit at current price or slightly below\n   • PLAN to hold at least overnight (PDT-safe)\n   \n   Exit Strategy:\n   • MUST hold >1 day if day_trade_count ≥ 3\n   • Set target profit: +10-20% for swing trades\n   • Stop-loss: -8% (tighter than crypto, stocks less volatile)\n   • Use limit sell orders during market hours\n   • Consider selling into strength (don\'t chase)\n\n⚡ DAY TRADING STRATEGY (ONLY if day_trade_count < 2):\n   \n   Timeframe: Intraday (enter and exit same day)\n   Risk: CONSUMES 1 day trade! Use sparingly.\n   \n   Only Day Trade When:\n   1. EXTREMELY high conviction (>80% Polymarket + strong news)\n   2. Clear intraday catalyst (earnings report, Fed announcement)\n   3. High volatility expected (opportunities for quick profit)\n   4. day_trade_count = 0 or 1 (safe buffer)\n   5. Portfolio already has good overnight positions\n   \n   Execution:\n   • Smaller size: maxTradeAmount * 0.6 (quick in/out)\n   • Tight stops: -4% stop loss (protect capital)\n   • Quick profit target: +6-10% (don\'t be greedy)\n   • Trade during market hours: 9:30 AM - 4:00 PM ET\n   • Exit before 3:45 PM ET (avoid close volatility)\n\n🎯 SECTOR & ETF TRADING:\n   Perfect for PDT-LIMITED accounts:\n   \n   Sector ETFs (Swing Trading Ideal):\n   • XLK (Technology)\n   • XLF (Financials)\n   • XLE (Energy)\n   • XLV (Healthcare)\n   • XLI (Industrials)\n   \n   Index ETFs:\n   • SPY (S&P 500) - Market-wide predictions\n   • QQQ (Nasdaq 100) - Tech sector bias\n   • IWM (Russell 2000) - Small caps\n   • DIA (Dow Jones) - Blue chips\n   \n   Benefits:\n   • Lower volatility than individual stocks\n   • Diversification (less single-stock risk)\n   • High liquidity (easy entry/exit)\n   • Match Polymarket macro predictions\n\n📉 SHORT SELLING / INVERSE PLAYS:\n   When Polymarket shows bearish predictions:\n   \n   • "Market crash likely" (>60%) → Short SPY or buy SQQQ (inverse)\n   • "Tech sector underperforms" → Short QQQ or sell tech stocks\n   • "Company misses earnings" → Short specific stock\n   \n   Risk Management:\n   • Short selling has UNLIMITED risk (price can rise infinitely)\n   • Use smaller position sizes: maxTradeAmount * 0.4\n   • Tight stop-loss: -6% (protect against short squeeze)\n   • Consider inverse ETFs instead (SQQQ, SPXS) - capped risk\n\n═══════════════════════════════════════════════════════════\n⚖️ ADVANCED RISK MANAGEMENT FRAMEWORK\n═══════════════════════════════════════════════════════════\n\n💰 POSITION SIZING MATRIX:\n   \n   Signal Strength → Position Size:\n   • EXTREME (>80% + news + technical): maxTradeAmount * 1.5\n   • STRONG (70-80%, 2+ confirmations): maxTradeAmount * 1.0\n   • MODERATE (65-70%, mixed signals): maxTradeAmount * 0.6\n   • WEAK (<65% or conflicting): NO TRADE\n   \n   Account-Based Adjustments:\n   • If portfolio_value < $5000: Reduce sizes by 40%\n   • If day_trade_count ≥ 3: Prefer crypto, larger crypto size\n   • If volatility high (VIX >25): Reduce all sizes by 30%\n\n🛡️ PORTFOLIO PROTECTION:\n   \n   Diversification Rules:\n   • Max single position: 20% of portfolio\n   • Max sector exposure: 30% of portfolio\n   • Max crypto allocation: 40% of portfolio\n   • Max stocks allocation: 60% of portfolio\n   • Always keep 15-20% cash buffer\n   \n   Correlation Management:\n   • Don\'t hold 3+ highly correlated assets (e.g., all tech stocks)\n   • Balance crypto and stocks (different risk profiles)\n   • Use ETFs for broad exposure, individual stocks for precision\n   \n   Drawdown Limits:\n   • Daily Loss Limit: -5% of portfolio → STOP TRADING\n   • Weekly Loss Limit: -10% of portfolio → Reduce sizes 50%\n   • If 3 consecutive losers → Pause, reassess strategy\n\n🚨 RISK TRIGGERS (Immediate Action Required):\n   \n   REDUCE EXPOSURE if:\n   • Polymarket shows "Market crash" >60%\n   • Multiple positions down >8%\n   • day_trade_count = 3 and stock positions need management\n   • Buying_power < 25% of initial capital\n   \n   STOP TRADING if:\n   • Daily loss >5% of portfolio\n   • Insufficient balance errors\n   • API errors or connectivity issues\n   • Unexpected market closure or halts\n\n═══════════════════════════════════════════════════════════\n🎯 DECISION MATRIX - FINAL TRADE EXECUTION CHECKLIST\n═══════════════════════════════════════════════════════════\n\nBefore EVERY trade, verify ALL conditions:\n\n✅ ACCOUNT STATUS:\n   □ Sufficient buying_power (> trade size + 20% buffer)\n   □ day_trade_count checked (PDT implications understood)\n   □ Existing positions reviewed (no over-concentration)\n   □ No risk triggers active\n\n✅ SIGNAL QUALITY:\n   □ Polymarket prediction ≥65% (or ≥70% for stocks)\n   □ Clear asset/symbol mapping from prediction\n   □ Signal timeframe matches trading strategy\n   □ Prediction category relevant to target asset\n\n✅ CONFLUENCE CHECK:\n   □ News confirms or neutral (not contradicting)\n   □ Technical analysis supports (or at least doesn\'t contradict)\n   □ No major conflicting signals in other predictions\n   □ Timing appropriate (market hours for stocks, any time for crypto)\n\n✅ RISK PARAMETERS:\n   □ Position size within limits (see sizing matrix)\n   □ Stop-loss level defined (-8% stocks, -12% crypto)\n   □ Take-profit targets set (+15%, +30%)\n   □ Total portfolio risk acceptable\n\n✅ EXECUTION PLAN:\n   □ Asset class chosen (crypto vs. stock) based on PDT status\n   □ Order type selected (market vs. limit)\n   □ Symbol and quantity calculated correctly\n   □ Exit strategy planned BEFORE entry\n\nIF ALL BOXES CHECKED → EXECUTE TRADE\nIF ANY BOX UNCHECKED → WAIT or GATHER MORE DATA\nIF MULTIPLE BOXES UNCHECKED → NO TRADE\n\n═══════════════════════════════════════════════════════════\n🧠 STRATEGIC INTELLIGENCE - ADVANCED CONSIDERATIONS\n═══════════════════════════════════════════════════════════\n\n⏰ TIME-OF-DAY OPTIMIZATION:\n   \n   Stock Trading Prime Times:\n   • 9:30-10:30 AM ET: High volatility, opening range breakouts\n   • 2:00-4:00 PM ET: Afternoon trends, position adjustments\n   • AVOID: 12:00-2:00 PM ET (low volume, choppy)\n   \n   Crypto Trading Prime Times:\n   • 8:00 AM - 12:00 PM ET: Overlap with stock market open\n   • 8:00 PM - 12:00 AM ET: Asia market activity\n   • 24/7 available, but higher volume during these windows\n\n📊 POLYMARKET PREDICTION TYPES & TRADING IMPLICATIONS:\n   \n   Binary Predictions (Yes/No):\n   • >75% = Very high conviction\n   • 60-75% = Moderate conviction\n   • <60% = Low conviction, no trade\n   \n   Multi-Outcome Predictions:\n   • Highest probability outcome >50% = Trade-worthy\n   • Close probabilities (40/30/30) = Wait for clarity\n   • Shifting probabilities = High volatility, intraday opportunity\n   \n   Time-Sensitive Predictions:\n   • "By end of week" = Short-term trades (crypto preferred)\n   • "By end of quarter" = Swing trades (stocks acceptable)\n   • "By end of year" = Long-term, outside auto-trading scope\n\n🔄 ADAPTIVE STRATEGY:\n   \n   If Winning Streak (3+ profitable trades):\n   • Maintain discipline, don\'t get overconfident\n   • Can increase size slightly (+20% max)\n   • Continue following checklist rigorously\n   \n   If Losing Streak (2+ consecutive losses):\n   • REDUCE position sizes by 50%\n   • TIGHTEN entry requirements (need >75% conviction)\n   • PAUSE if 3 consecutive losses\n   • REVIEW what went wrong (signal quality? execution? timing?)\n   \n   Market Regime Adaptation:\n   • High Volatility (VIX >25): Smaller sizes, tighter stops\n   • Low Volatility (VIX <15): Normal sizes, can hold longer\n   • Trending Market: Follow trend, use momentum strategies\n   • Range-Bound: Mean reversion, fade extremes\n\n═══════════════════════════════════════════════════════════\n⚡ EXECUTION SUMMARY - PRIORITY HIERARCHY\n═══════════════════════════════════════════════════════════\n\n0. READ TRADING MEMORY (read_trading_memory) - ALWAYS FIRST!\n1. ACCOUNT ANALYSIS (get_account, get_all_positions) - MANDATORY SECOND\n2. POLYMARKET SIGNAL IDENTIFICATION (scan all predictions, score conviction)\n3. NEWS CATALYST CONFIRMATION (get_news for mapped symbols)\n4. TECHNICAL ANALYSIS (price action, support/resistance, volume)\n5. ASSET CLASS SELECTION (crypto vs stock based on PDT, timing, signal)\n6. RISK CALCULATION (position size, stops, portfolio impact)\n7. EXECUTION (place order if ALL checklist items verified)\n8. DOCUMENT TRADE (append_trading_memory with entry, rationale, exit plan)\n9. POSITION MONITORING (manage stops, take profits, adjust as needed)\n10. CLOSE & DOCUMENT (close_position + update memory with P/L & lessons)\n\n🎯 REMEMBER:\n• Quality > Quantity: Better to make 2 great trades than 10 mediocre ones\n• Risk Management > Profit Chasing: Protect capital first, profits will follow\n• Adaptation > Rigidity: Market conditions change, be flexible\n• Discipline > Emotion: Follow the checklist, trust the process\n\nTrade smart. Trade safe. Trade profitably. 🚀',
        maxTradeAmount: 100,
        checkInterval: 60,
    });
    const [availableCategories] = useState([
        "Politics",
        "Sports",
        "Crypto",
        "Finance",
        "Tech",
        "Geopolitics",
        "Culture",
        "Economics",
    ]);
    const [keywordInput, setKeywordInput] = useState("");
    const [logs, setLogs] = useState<TradingLog[]>([]);
    const [serverUrl] = useState("http://localhost:5002"); // Updated to new multi-broker server

    // Initialize the trading server on mount
    useEffect(() => {
        initializeServer();
        checkAndRestoreAutoTrading(); // Check if already running
        loadConfigFromLocalStorage(); // Restore saved config
    }, []);

    // Poll for auto-trading logs when active
    useEffect(() => {
        if (!isActive) {
            return;
        }

        const pollLogs = async () => {
            try {
                const response = await fetch(`${serverUrl}/api/autotrading/logs`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.logs && data.logs.length > 0) {
                        // Convert backend logs to frontend format
                        const newLogs: TradingLog[] = data.logs.map((log: any) => ({
                            timestamp: new Date(log.timestamp),
                            message: log.message,
                            type: log.type,
                        }));
                        setLogs(newLogs);
                    }
                }
            } catch (error) {
                console.error("Error fetching logs:", error);
            }
        };

        // Poll every 2 seconds
        pollLogs(); // Initial fetch
        const interval = setInterval(pollLogs, 2000);

        return () => clearInterval(interval);
    }, [isActive, serverUrl]);

    const loadConfigFromLocalStorage = () => {
        try {
            const savedConfig = localStorage.getItem("autotrading_config");
            if (savedConfig) {
                const parsed = JSON.parse(savedConfig);
                // Only restore user settings, keep the updated default prompts
                setConfig(prev => ({
                    ...prev,
                    categories: parsed.categories || prev.categories,
                    keywords: parsed.keywords || prev.keywords,
                    maxTradeAmount: parsed.maxTradeAmount || prev.maxTradeAmount,
                    checkInterval: parsed.checkInterval || prev.checkInterval,
                    // Keep systemPrompt and strategyPrompt from defaults (updated prompts)
                }));
                addLog("✅ Restored saved configuration", "info");
            }
        } catch (error) {
            console.error("Failed to load config:", error);
        }
    };

    const saveConfigToLocalStorage = (cfg: AutoTradingConfig) => {
        try {
            localStorage.setItem("autotrading_config", JSON.stringify(cfg));
        } catch (error) {
            console.error("Failed to save config:", error);
        }
    };

    const checkAndRestoreAutoTrading = async () => {
        try {
            const response = await fetch(`${serverUrl}/api/autotrading/status`);
            if (response.ok) {
                const data = await response.json();
                if (data.active) {
                    setIsActive(true);
                    if (data.config) {
                        setConfig(data.config);
                    }
                    addLog("🔄 Restored active auto-trading session", "success");
                }
            }
        } catch (error) {
            console.error("Failed to check auto-trading status:", error);
        }
    };

    const initializeServer = async () => {
        const broker = localStorage.getItem("broker") || "alpaca";
        const brokerKey = localStorage.getItem(`${broker}_key`);
        const brokerSecret = localStorage.getItem(`${broker}_secret`);
        const claudeKey = localStorage.getItem("claude_key");
        const deepseekKey = localStorage.getItem("deepseek_key");
        const aiModel = localStorage.getItem("ai_model") || "claude";
        const paperMode = localStorage.getItem("paper_mode") === "true";

        // Validate broker API keys
        if (!brokerKey || !brokerSecret) {
            addLog(
                `⚠️ Please configure your ${broker.charAt(0).toUpperCase() + broker.slice(1)} API keys in Settings before using auto-trading.`,
                "error",
            );
            return;
        }

        if (aiModel === "claude" && !claudeKey) {
            addLog(
                "⚠️ Please configure your Claude API key in Settings or switch to DeepSeek.",
                "error",
            );
            return;
        }

        if (aiModel === "deepseek" && !deepseekKey) {
            addLog(
                "⚠️ Please configure your DeepSeek API key in Settings or switch to Claude.",
                "error",
            );
            return;
        }

        try {
            const requestBody: any = {
                broker: broker,
                claude_key: claudeKey,
                deepseek_key: deepseekKey,
                ai_model: aiModel,
                paper_mode: paperMode,
            };
            
            // Add broker-specific keys
            requestBody[`${broker}_key`] = brokerKey;
            requestBody[`${broker}_secret`] = brokerSecret;
            
            const response = await fetch(`${serverUrl}/api/initialize`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(requestBody),
            });

            if (response.ok) {
                const data = await response.json();
                const modelName =
                    data.ai_model === "deepseek" ? "DeepSeek-V3.2-Exp" : "Claude 3.5 Sonnet";
                setIsInitialized(true);
                addLog(
                    `✅ Trading server initialized with ${modelName} in ${paperMode ? "PAPER" : "LIVE"} mode. Ready for auto-trading.`,
                    "success",
                );
            } else {
                const error = await response.json();
                addLog(
                    `❌ Failed to initialize: ${error.error}. Please check your API keys in Settings.`,
                    "error",
                );
            }
        } catch (error) {
            addLog(
                `❌ Cannot connect to trading server at ${serverUrl}. Please make sure the server is running.`,
                "error",
            );
        }
    };

    // Add log entry
    const addLog = (message: string, type: TradingLog["type"] = "info") => {
        setLogs(prev => [
            { timestamp: new Date(), message, type },
            ...prev.slice(0, 99), // Keep last 100 logs
        ]);
    };

    // Toggle category selection
    const toggleCategory = (category: string) => {
        setConfig(prev => ({
            ...prev,
            categories: prev.categories.includes(category)
                ? prev.categories.filter(c => c !== category)
                : [...prev.categories, category],
        }));
    };

    // Add keyword
    const addKeyword = () => {
        if (keywordInput.trim() && !config.keywords.includes(keywordInput.trim())) {
            setConfig(prev => ({
                ...prev,
                keywords: [...prev.keywords, keywordInput.trim()],
            }));
            setKeywordInput("");
        }
    };

    // Remove keyword
    const removeKeyword = (keyword: string) => {
        setConfig(prev => ({
            ...prev,
            keywords: prev.keywords.filter(k => k !== keyword),
        }));
    };

    // Start auto-trading
    const startAutoTrading = async () => {
        if (!isInitialized) {
            addLog(
                "⚠️ Trading server not initialized. Please configure API keys in Settings.",
                "error",
            );
            return;
        }

        if (config.categories.length === 0 && config.keywords.length === 0) {
            addLog("⚠️ Please select at least one category or keyword", "error");
            return;
        }

        try {
            addLog("📊 Fetching Polymarket data...", "info");

            // Load markets from IndexedDB
            const pages = await loadMarkets();
            const allMarkets: MarketData[] = pages.flatMap(page => page.markets);

            // Filter markets by selected categories and keywords
            const filteredMarkets = allMarkets.filter(market => {
                // Check category match
                const categoryMatch =
                    config.categories.length === 0 ||
                    (market.category && config.categories.includes(market.category));

                // Check keyword match in title or description
                const keywordMatch =
                    config.keywords.length === 0 ||
                    config.keywords.some(keyword => {
                        const lowerKeyword = keyword.toLowerCase();
                        return (
                            market.title.toLowerCase().includes(lowerKeyword) ||
                            market.outcome.toLowerCase().includes(lowerKeyword) ||
                            (market.description &&
                                market.description.toLowerCase().includes(lowerKeyword))
                        );
                    });

                return categoryMatch && keywordMatch;
            });

            // Sort by most recent activity (send ALL matching markets)
            const relevantMarkets = filteredMarkets.sort((a, b) => {
                const aTime = a.lastTransaction?.timestamp || 0;
                const bTime = b.lastTransaction?.timestamp || 0;
                return bTime - aTime;
            });

            addLog(`📈 Found ${filteredMarkets.length} matching markets (sending ALL)`, "info");

            // Include market data in config
            const configWithMarkets = {
                ...config,
                polymarketData: relevantMarkets.map(m => ({
                    title: m.title,
                    outcome: m.outcome,
                    probability: m.probability,
                    category: m.category,
                    description: m.description,
                    marketUrl: m.marketUrl,
                    lastTransactionSide: m.lastTransaction?.side,
                    lastTransactionSize: m.lastTransaction?.size,
                    lastTransactionTime: m.lastTransaction?.time,
                })),
            };

            const response = await fetch(`${serverUrl}/api/autotrading/start`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(configWithMarkets),
            });

            if (response.ok) {
                setIsActive(true);
                saveConfigToLocalStorage(config); // Save config for recovery
                addLog(
                    "🚀 Auto-trading started successfully! AI is now monitoring markets...",
                    "success",
                );
            } else {
                const error = await response.json();
                addLog(`❌ Failed to start: ${error.error}`, "error");
            }
        } catch (error) {
            addLog(`❌ Connection error: ${error}`, "error");
        }
    };

    // Stop auto-trading
    const stopAutoTrading = async () => {
        try {
            const response = await fetch(`${serverUrl}/api/autotrading/stop`, {
                method: "POST",
            });

            if (response.ok) {
                setIsActive(false);
                addLog("Auto-trading stopped", "info");
            }
        } catch (error) {
            addLog(`Error stopping: ${error}`, "error");
        }
    };

    // Generate market filter JSON preview
    const getMarketFilterJSON = () => {
        return JSON.stringify(
            {
                categories: config.categories,
                keywords: config.keywords,
                maxTradeAmount: config.maxTradeAmount,
                checkInterval: config.checkInterval,
            },
            null,
            2,
        );
    };

    return (
        <div className="container mx-auto px-4 py-8">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">🤖 Auto-Trading</h1>
                <p className="text-gray-600">
                    AI-powered automated trading based on Polymarket market analysis
                </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Configuration Panel */}
                <div className="space-y-6">
                    {/* Status Card */}
                    <div
                        className={`p-6 rounded-lg border-2 ${
                            isActive
                                ? "bg-green-50 border-green-500"
                                : isInitialized
                                  ? "bg-blue-50 border-blue-300"
                                  : "bg-gray-50 border-gray-300"
                        }`}
                    >
                        <div className="flex items-center justify-between">
                            <div>
                                <h2 className="text-lg font-semibold">
                                    Status:{" "}
                                    {isActive
                                        ? "🟢 Active"
                                        : isInitialized
                                          ? "🔵 Ready"
                                          : "⚫ Not Ready"}
                                </h2>
                                <p className="text-sm text-gray-600">
                                    {isActive
                                        ? `Monitoring ${config.categories.length} categories, ${config.keywords.length} keywords`
                                        : isInitialized
                                          ? "Configure and start auto-trading"
                                          : "Initialize with API keys in Settings"}
                                </p>
                            </div>
                            <button
                                onClick={isActive ? stopAutoTrading : startAutoTrading}
                                disabled={!isInitialized && !isActive}
                                className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                                    isActive
                                        ? "bg-red-600 hover:bg-red-700 text-white"
                                        : isInitialized
                                          ? "bg-green-600 hover:bg-green-700 text-white"
                                          : "bg-gray-400 cursor-not-allowed text-white"
                                }`}
                            >
                                {isActive ? "🛑 Stop" : "▶️ Start"}
                            </button>
                        </div>
                    </div>

                    {/* Category Selection */}
                    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                        <h3 className="text-lg font-semibold mb-4">📊 Market Categories</h3>
                        <div className="grid grid-cols-2 gap-2">
                            {availableCategories.map(category => (
                                <button
                                    key={category}
                                    onClick={() => toggleCategory(category)}
                                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                                        config.categories.includes(category)
                                            ? "bg-blue-600 text-white"
                                            : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                                    }`}
                                >
                                    {config.categories.includes(category) ? "✓ " : ""}
                                    {category}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Keywords */}
                    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                        <h3 className="text-lg font-semibold mb-4">🔍 Keywords</h3>
                        <div className="flex gap-2 mb-3">
                            <input
                                type="text"
                                value={keywordInput}
                                onChange={e => setKeywordInput(e.target.value)}
                                onKeyPress={e => e.key === "Enter" && addKeyword()}
                                placeholder="e.g., Bitcoin, Election, Tesla"
                                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                            />
                            <button
                                onClick={addKeyword}
                                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
                            >
                                Add
                            </button>
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {config.keywords.map(keyword => (
                                <span
                                    key={keyword}
                                    className="inline-flex items-center gap-2 px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm"
                                >
                                    {keyword}
                                    <button
                                        onClick={() => removeKeyword(keyword)}
                                        className="hover:text-purple-900"
                                    >
                                        ×
                                    </button>
                                </span>
                            ))}
                            {config.keywords.length === 0 && (
                                <p className="text-sm text-gray-500">No keywords added</p>
                            )}
                        </div>
                    </div>

                    {/* Trading Parameters */}
                    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                        <h3 className="text-lg font-semibold mb-4">⚙️ Trading Parameters</h3>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Max Trade Amount ($)
                                </label>
                                <input
                                    type="number"
                                    value={config.maxTradeAmount}
                                    onChange={e =>
                                        setConfig(prev => ({
                                            ...prev,
                                            maxTradeAmount: Number(e.target.value),
                                        }))
                                    }
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Check Interval (seconds)
                                </label>
                                <input
                                    type="number"
                                    value={config.checkInterval}
                                    onChange={e =>
                                        setConfig(prev => ({
                                            ...prev,
                                            checkInterval: Number(e.target.value),
                                        }))
                                    }
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                                />
                            </div>
                        </div>
                    </div>

                    {/* System Prompt */}
                    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                        <h3 className="text-lg font-semibold mb-4">💬 System Prompt</h3>
                        <textarea
                            value={config.systemPrompt}
                            onChange={e =>
                                setConfig(prev => ({ ...prev, systemPrompt: e.target.value }))
                            }
                            rows={3}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                            placeholder="Define the AI's role and behavior..."
                        />
                    </div>

                    {/* Strategy Prompt */}
                    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                        <h3 className="text-lg font-semibold mb-4">📈 Strategy Prompt</h3>
                        <textarea
                            value={config.strategyPrompt}
                            onChange={e =>
                                setConfig(prev => ({ ...prev, strategyPrompt: e.target.value }))
                            }
                            rows={4}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                            placeholder="Describe your trading strategy..."
                        />
                    </div>

                    {/* Market Filter JSON Preview */}
                    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                        <h3 className="text-lg font-semibold mb-4">📋 Market Filter JSON</h3>
                        <pre className="bg-gray-50 p-4 rounded-lg text-xs overflow-auto max-h-40">
                            {getMarketFilterJSON()}
                        </pre>
                    </div>
                </div>

                {/* Logs Panel */}
                <div className="space-y-6">
                    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold">📜 Activity Logs</h3>
                            <button
                                onClick={async () => {
                                    try {
                                        await fetch(`${serverUrl}/api/autotrading/logs/clear`, {
                                            method: "POST",
                                        });
                                        setLogs([]);
                                    } catch (error) {
                                        console.error("Failed to clear logs:", error);
                                        setLogs([]); // Clear frontend anyway
                                    }
                                }}
                                className="text-sm text-gray-600 hover:text-gray-800"
                            >
                                Clear
                            </button>
                        </div>
                        <div className="space-y-2 max-h-[800px] overflow-y-auto">
                            {logs.length === 0 ? (
                                <p className="text-sm text-gray-500 text-center py-8">
                                    No logs yet. Start auto-trading to see activity.
                                </p>
                            ) : (
                                logs.map((log, index) => (
                                    <div
                                        key={index}
                                        className={`p-3 rounded-lg text-sm ${
                                            log.type === "success"
                                                ? "bg-green-50 text-green-800"
                                                : log.type === "error"
                                                  ? "bg-red-50 text-red-800"
                                                  : log.type === "trade"
                                                    ? "bg-blue-50 text-blue-800"
                                                    : "bg-gray-50 text-gray-800"
                                        }`}
                                    >
                                        <div className="flex items-start justify-between gap-2">
                                            <span className="flex-1">{log.message}</span>
                                            <span className="text-xs opacity-70 whitespace-nowrap">
                                                {log.timestamp.toLocaleTimeString()}
                                            </span>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>

                    {/* Warning */}
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                        <h4 className="font-semibold text-yellow-900 mb-2">⚠️ Important</h4>
                        <ul className="text-sm text-yellow-800 space-y-1">
                            <li>• Auto-trading is experimental - monitor closely</li>
                            <li>• Start with small max trade amounts</li>
                            <li>• Paper trading mode is recommended for testing</li>
                            <li>• You can stop auto-trading anytime</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    );
};
