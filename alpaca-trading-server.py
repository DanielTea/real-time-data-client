#!/usr/bin/env python3
"""
Alpaca Trading Server
Uses alpaca-py library directly (same as official Alpaca MCP server uses internally)
Implements the same tools/functionality as the official MCP server
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import logging
import threading
import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from anthropic import Anthropic
from openai import OpenAI
import yfinance as yf

# Alpaca imports (same as official MCP server)
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import (
    MarketOrderRequest, LimitOrderRequest, StopOrderRequest, StopLimitOrderRequest,
    GetOrdersRequest, ClosePositionRequest, GetOptionContractsRequest
)
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus
from alpaca.data.historical import CryptoHistoricalDataClient, StockHistoricalDataClient, NewsClient
from alpaca.data.requests import (
    CryptoLatestBarRequest, StockLatestQuoteRequest, StockBarsRequest,
    StockSnapshotRequest, NewsRequest
)
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from datetime import timedelta

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global clients
trading_client = None
crypto_data_client = None
stock_data_client = None
anthropic_client = None
openai_client = None
news_client = None
ai_model = "claude"  # Default to Claude

# Auto-trading state
autotrading_active = False
autotrading_thread = None
autotrading_config = None
autotrading_logs = []
conversation_history = []

def add_autotrading_log(message, log_type="info"):
    """Add a log entry for auto-trading"""
    global autotrading_logs
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "message": message,
        "type": log_type
    }
    autotrading_logs.append(log_entry)
    # Keep last 500 logs (more history for refreshes)
    if len(autotrading_logs) > 500:
        autotrading_logs = autotrading_logs[-500:]
    logger.info(f"Auto-trading: {message}")

# MCP-like tool definitions (same as official Alpaca MCP server)
TOOLS = [
    # Account & Portfolio
    {
        "name": "get_account",
        "description": """Get comprehensive account information including:
        - Account status and restrictions
        - Buying power breakdown (RegT, day trading, non-marginable, effective)
        - Cash details (cash, withdrawable, pending transfers)
        - Equity and portfolio value
        - Position values (long, short, total)
        - Margin details (initial, maintenance, SMA)
        - Pattern Day Trading info (day_trade_count - CRITICAL for PDT rules)
        - Miscellaneous (accrued fees, crypto status, account creation date)
        
        IMPORTANT: Always check day_trade_count to determine PDT status (<3 = can day trade stocks, ≥3 = must swing trade)""",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_all_positions",
        "description": "Get all current positions in the portfolio",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "close_position",
        "description": """Close an existing position. MUST provide either qty OR percentage.
        
        ⚠️ CRITICAL - SYMBOL FORMAT:
        Use the EXACT symbol string from get_all_positions response!
        
        ✅ CORRECT crypto symbols: "BTC/USD", "ETH/USD", "SOL/USD" (WITH the slash!)
        ❌ WRONG: "BTC", "ETH", "BTCUSD", "ETHUSD" (these will fail!)
        
        ✅ CORRECT stock symbols: "AAPL", "TSLA", "SPY"
        
        Always call get_all_positions first, then use the exact "symbol" field from the position object.
        Use percentage=100 to close entire position.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "EXACT symbol from get_all_positions (e.g., 'BTC/USD' NOT 'BTC'!)"},
                "qty": {"type": "number", "description": "Exact quantity to close. Provide either qty OR percentage."},
                "percentage": {"type": "number", "description": "Percentage to close (1-100). Use 100 to close entire position. Provide either qty OR percentage."}
            },
            "required": ["symbol"]
        }
    },
    
    # Crypto Trading
    {
        "name": "get_crypto_latest_bar",
        "description": "Get the latest price bar for a cryptocurrency",
        "input_schema": {
            "type": "object",
            "properties": {"symbol": {"type": "string", "description": "Crypto symbol (e.g., 'BTC', 'ETH', 'SOL')"}},
            "required": ["symbol"]
        }
    },
    {
        "name": "place_crypto_order",
        "description": "Place a market order for cryptocurrency",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Crypto symbol (e.g., 'BTC', 'ETH', 'SOL')"},
                "side": {"type": "string", "enum": ["buy", "sell"], "description": "Order side"},
                "qty": {"type": "number", "description": "Quantity of crypto to trade"},
                "notional": {"type": "number", "description": "Dollar amount to trade"}
            },
            "required": ["symbol", "side"]
        }
    },
    
    # Stock Trading
    {
        "name": "place_stock_order",
        "description": "Place a stock order (market, limit, stop, or stop-limit). Supports long and short positions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Stock symbol (e.g., 'AAPL', 'TSLA')"},
                "side": {"type": "string", "enum": ["buy", "sell"], "description": "buy for long, sell for short"},
                "qty": {"type": "number", "description": "Number of shares"},
                "order_type": {"type": "string", "enum": ["market", "limit", "stop", "stop_limit"], "description": "Order type (default: market)"},
                "limit_price": {"type": "number", "description": "Limit price (required for limit/stop_limit orders)"},
                "stop_price": {"type": "number", "description": "Stop price (required for stop/stop_limit orders)"},
                "time_in_force": {"type": "string", "enum": ["day", "gtc", "ioc", "fok"], "description": "Time in force (default: day)"}
            },
            "required": ["symbol", "side", "qty"]
        }
    },
    {
        "name": "get_stock_quote",
        "description": "Get real-time bid/ask quote for a stock",
        "input_schema": {
            "type": "object",
            "properties": {"symbol": {"type": "string", "description": "Stock symbol (e.g., 'AAPL')"}},
            "required": ["symbol"]
        }
    },
    {
        "name": "get_stock_bars",
        "description": "Get historical price bars for technical analysis (OHLCV data)",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Stock symbol (e.g., 'AAPL')"},
                "timeframe": {"type": "string", "enum": ["1Min", "5Min", "15Min", "1Hour", "1Day"], "description": "Bar timeframe (default: 1Day)"},
                "days": {"type": "number", "description": "Number of days of history (default: 5)"},
                "limit": {"type": "number", "description": "Max number of bars to return (default: 100)"}
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "get_stock_snapshot",
        "description": "Get comprehensive stock snapshot with latest quote, trade, bars, and daily performance",
        "input_schema": {
            "type": "object",
            "properties": {"symbol": {"type": "string", "description": "Stock symbol (e.g., 'AAPL')"}},
            "required": ["symbol"]
        }
    },
    
    # Options Trading
    {
        "name": "get_option_contracts",
        "description": """Search for option contracts by underlying stock with optional filters.
        
        Returns detailed contract information including:
        - Option symbol (e.g., 'AAPL250117C00150000')
        - Strike price, expiration date
        - Type (call/put), style (American/European)
        - Contract size (usually 100 shares per contract)
        
        Use this to find specific contracts for trading based on your criteria.
        For a simpler overview of all available options, use get_option_chain instead.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "underlying_symbol": {"type": "string", "description": "Underlying stock symbol (e.g., 'AAPL')"},
                "expiration_date_gte": {"type": "string", "description": "Min expiration date (YYYY-MM-DD)"},
                "expiration_date_lte": {"type": "string", "description": "Max expiration date (YYYY-MM-DD)"},
                "strike_price_gte": {"type": "number", "description": "Min strike price"},
                "strike_price_lte": {"type": "number", "description": "Max strike price"},
                "type": {"type": "string", "enum": ["call", "put"], "description": "Option type (call or put)"},
                "limit": {"type": "number", "description": "Max results (default: 100)"}
            },
            "required": ["underlying_symbol"]
        }
    },
    {
        "name": "get_option_chain",
        "description": """Get a simplified overview of available options for an underlying stock.
        
        Returns calls and puts organized by expiration date and strike price.
        This is the easiest way to see what options are available for trading.
        
        Example use: "Show me all AAPL options expiring in the next 30 days"
        
        For more detailed filtering, use get_option_contracts instead.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "underlying_symbol": {"type": "string", "description": "Underlying stock symbol (e.g., 'AAPL')"},
                "days_to_expiration": {"type": "number", "description": "Max days until expiration (default: 60)"}
            },
            "required": ["underlying_symbol"]
        }
    },
    {
        "name": "place_option_order",
        "description": """Place a single-leg option order (buy/sell one call or put contract).
        
        ⚠️ IMPORTANT RULES:
        • Options symbols format: 'TICKER{YYMMDD}{C/P}{STRIKE*1000}' 
          Example: 'AAPL250117C00150000' = AAPL Call expiring Jan 17, 2025, $150 strike
        • qty must be a whole number (number of contracts)
        • Each contract typically controls 100 shares
        • time_in_force must be 'day' for options (Alpaca requirement)
        • Cost = premium per share × 100 × qty (e.g., $2.50 premium × 100 × 1 contract = $250)
        
        For multi-leg strategies (spreads, strangles), use place_option_spread instead.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Option symbol (e.g., 'AAPL250117C00150000')"},
                "side": {"type": "string", "enum": ["buy", "sell"], "description": "Order side"},
                "qty": {"type": "number", "description": "Number of contracts (must be whole number)"},
                "order_type": {"type": "string", "enum": ["market", "limit"], "description": "Order type (default: market)"},
                "limit_price": {"type": "number", "description": "Limit price per contract (required for limit orders)"},
                "time_in_force": {"type": "string", "enum": ["day"], "description": "Must be 'day' for options (Alpaca requirement)"}
            },
            "required": ["symbol", "side", "qty"]
        }
    },
    {
        "name": "place_option_spread",
        "description": """Place a multi-leg options order (spreads, strangles, iron condors, etc.).
        
        Common strategies:
        • LONG CALL SPREAD: Buy lower strike call + Sell higher strike call (bullish, limited risk/reward)
        • LONG PUT SPREAD: Buy higher strike put + Sell lower strike put (bearish, limited risk/reward)
        • LONG STRADDLE: Buy call + Buy put at same strike (expect big move either direction)
        • LONG STRANGLE: Buy OTM call + Buy OTM put (cheaper straddle, need bigger move)
        • IRON CONDOR: Sell call spread + Sell put spread (profit from low volatility)
        
        Each leg requires:
        • symbol: Option contract symbol
        • side: "buy" or "sell"
        • ratio_qty: Usually "1" for balanced spreads
        
        Example long call spread:
        Legs: [
          {"symbol": "AAPL250117C00190000", "side": "buy", "ratio_qty": 1},
          {"symbol": "AAPL250117C00210000", "side": "sell", "ratio_qty": 1}
        ]
        
        ⚠️ Advanced strategy - understand risks before trading!""",
        "input_schema": {
            "type": "object",
            "properties": {
                "legs": {
                    "type": "array",
                    "description": "Array of leg objects, each with symbol, side, ratio_qty",
                    "items": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Option symbol"},
                            "side": {"type": "string", "enum": ["buy", "sell"], "description": "buy or sell"},
                            "ratio_qty": {"type": "number", "description": "Quantity ratio (usually 1)"}
                        },
                        "required": ["symbol", "side", "ratio_qty"]
                    }
                },
                "order_type": {"type": "string", "enum": ["market", "limit"], "description": "Order type"},
                "limit_price": {"type": "number", "description": "Total limit price for the spread (required for limit orders)"},
                "qty": {"type": "number", "description": "Number of spread contracts (default: 1)"}
            },
            "required": ["legs", "order_type"]
        }
    },
    {
        "name": "close_option_position",
        "description": """Close an existing option position (opposite side order).
        
        ⚠️ CRITICAL: Use the EXACT symbol from get_all_positions!
        
        This automatically creates the correct closing order:
        • If you're LONG (own contracts): Creates SELL order to close
        • If you're SHORT (sold contracts): Creates BUY order to close
        
        Use percentage=100 to close entire position, or specify qty for partial close.
        
        Note: This is the same as close_position but with options-specific guidance.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "EXACT option symbol from positions (e.g., 'AAPL250117C00150000')"},
                "qty": {"type": "number", "description": "Number of contracts to close (provide qty OR percentage)"},
                "percentage": {"type": "number", "description": "Percentage to close (1-100). Use 100 to close entire position."}
            },
            "required": ["symbol"]
        }
    },
    
    # Technical Analysis
            {
                "name": "get_technical_indicators",
                "description": """Calculate comprehensive technical indicators for a symbol.
                
                DATA SOURCES:
                • Stocks: Yahoo Finance (free, unlimited historical data)
                • Crypto: Alpaca (works great on free tier)
                
                SYMBOL FORMATS:
                • Stocks: 'AAPL', 'TSLA', 'NVDA' (just the ticker)
                • Crypto: 'BTC', 'ETH', 'SOL' (with or without /USD - auto-converts)
                • Alternative: 'BTC/USD', 'ETH/USD' (explicit format also works)
                
                Returns multiple indicators for technical analysis:
                • RSI (Relative Strength Index): 0-100 scale, >70 overbought, <30 oversold
                • MACD (Moving Average Convergence Divergence): Trend-following momentum indicator
                • SMA (Simple Moving Averages): 20, 50, 200-day averages
                • EMA (Exponential Moving Averages): 12, 26-day averages (more weight on recent)
                • Bollinger Bands: Upper, middle, lower bands (volatility indicator)
                • Volume Analysis: Average volume, recent volume trends
                
                Perfect for confirming Polymarket signals with technical analysis.
                
                Example: Strong RSI (>70) + MACD bullish cross + Price above SMA(50) = Strong buy signal
                """,
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Stock ticker (e.g., 'AAPL') or crypto (e.g., 'BTC' or 'BTC/USD')"},
                        "timeframe": {"type": "string", "enum": ["1Min", "5Min", "15Min", "1Hour", "1Day"], "description": "Bar timeframe (default: 1Day)"},
                        "limit": {"type": "number", "description": "Number of bars to analyze (default: 200, max: 500)"}
                    },
                    "required": ["symbol"]
                }
            },
    
    # Order Management
    {
        "name": "get_orders",
        "description": "Get list of orders (open, filled, cancelled, or all)",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["open", "closed", "all"], "description": "Filter by status (default: open)"},
                "limit": {"type": "number", "description": "Max number of orders (default: 50)"}
            },
            "required": []
        }
    },
    {
        "name": "cancel_order",
        "description": "Cancel an open order by its ID",
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string", "description": "Order ID to cancel"}},
            "required": ["order_id"]
        }
    },
    {
        "name": "cancel_all_orders",
        "description": "Cancel all open orders",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    
    # Market News
    {
        "name": "get_news",
        "description": "Get latest market news for stocks or general market news",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbols": {"type": "array", "items": {"type": "string"}, "description": "Stock symbols to get news for (optional)"},
                "limit": {"type": "number", "description": "Number of articles (default: 10)"}
            },
            "required": []
        }
    },
    
    # Market Clock
    {
        "name": "get_market_clock",
        "description": """Get current market status and trading hours.
        Returns:
        - is_open: Boolean indicating if market is currently open
        - timestamp: Current timestamp
        - next_open: Next market open time (ISO format)
        - next_close: Next market close time (ISO format)
        
        CRITICAL: Stock trading only available during market hours (9:30 AM - 4:00 PM ET, Mon-Fri).
        Crypto trading is 24/7/365 and NOT affected by market hours.""",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    
    # Trading Memory / Notes System
    {
        "name": "read_trading_memory",
        "description": """Read your persistent trading memory/notes file with LINE NUMBERS.
        This file contains your notes about:
        - Open positions (entry rationale, exit strategies)
        - Recent closed positions (P/L, lessons learned)
        - Important observations and patterns
        
        ALWAYS read this at the start of each analysis cycle to maintain context.
        
        Returns content with line numbers (format: "  1| content"):
        Example output:
           1| # Trading Memory
           2| 
           3| ## 🔵 OPEN: BTC - 2025-10-25
           4| **Entry Price:** $67,500
          ...
          25| **Exit Strategy:** Stop $65,000
          
        Use these line numbers with edit_trading_memory_lines to edit/delete specific sections.""",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "write_trading_memory",
        "description": """REPLACE the entire trading memory file with new content.
        
        ⚠️ CRITICAL USAGE:
        1. Call read_trading_memory() first to get current content
        2. Modify the content as needed:
           - REMOVE closed position entries (keep file clean!)
           - UPDATE existing position notes
           - ADD new position entries
        3. Call write_trading_memory() with the modified content
        
        Use this for:
        - CLOSING A POSITION: Remove its "OPEN" entry, optionally add brief "CLOSED" summary
        - UPDATING EXIT STRATEGY: Modify existing position notes
        - CLEANING UP: Remove old closed positions (keep last 5-10 only)
        
        DO NOT just append - this will make the file huge! Always edit inline.
        The file is Markdown format. Keep it organized and clean.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "The COMPLETE new content for the memory file (Markdown format)"}
            },
            "required": ["content"]
        }
    },
    {
        "name": "append_trading_memory",
        "description": """Append new content to the END of the memory file.
        
        ⚠️ ONLY use this for:
        - Adding a NEW position (when you first open it)
        - Adding quick observations that don't require editing existing content
        
        DO NOT use this for:
        - Closing positions (use write_trading_memory to REMOVE the entry)
        - Updating existing positions (use write_trading_memory to EDIT)
        
        If you use this too much, the file will become bloated. Prefer write_trading_memory.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Content to append to the END of the memory file"}
            },
            "required": ["content"]
        }
    },
    {
        "name": "edit_trading_memory_lines",
        "description": """Edit or delete specific lines in the trading memory file.
        This is the EASIEST way to manage your memory - no need to read/rewrite entire file!
        
        Use cases:
        1. CLOSE POSITION: Delete the lines for that position's entry
           Example: delete lines 10-35 (entire "## 🔵 OPEN: BTC" section)
        
        2. UPDATE EXIT STRATEGY: Replace specific lines
           Example: replace lines 25-28 (the Exit Strategy section) with new targets
        
        3. ADD CLOSED SUMMARY: Insert new lines at specific position
           Example: insert at line 5 a brief "## ✅ CLOSED: BTC - +5.2% profit"
        
        Parameters:
        - from_line: Starting line number (1-indexed)
        - to_line: Ending line number (inclusive). If same as from_line, affects single line
        - new_content: New text to insert. Use "" (empty string) to DELETE lines
        - operation: "replace" (default), "delete", or "insert_before"
        
        Examples:
        - Delete position: from_line=10, to_line=35, new_content="", operation="delete"
        - Update lines: from_line=25, to_line=28, new_content="**New Exit Strategy:**\\n- Stop: $100\\n- Target: $150"
        - Insert summary: from_line=5, to_line=5, new_content="## ✅ CLOSED: BTC - +5% profit\\n", operation="insert_before"
        """,
        "input_schema": {
            "type": "object",
            "properties": {
                "from_line": {"type": "integer", "description": "Starting line number (1-indexed)"},
                "to_line": {"type": "integer", "description": "Ending line number (inclusive)"},
                "new_content": {"type": "string", "description": "New content. Use empty string to delete."},
                "operation": {
                    "type": "string", 
                    "enum": ["replace", "delete", "insert_before"],
                    "description": "Operation type: replace (default), delete, or insert_before"
                }
            },
            "required": ["from_line", "to_line"]
        }
    },
    {
        "name": "clear_trading_memory",
        "description": """Clear all trading memory (use with extreme caution).
        This erases ALL history and lessons learned.
        Only use after major strategy overhaul or if file is corrupted.
        Generally, you should use edit_trading_memory_lines instead.""",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    }
]

# Technical Indicator Calculation Functions
def calculate_rsi(prices, period=14):
    """Calculate Relative Strength Index"""
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 0
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - 100. / (1. + rs)
    
    for i in range(period, len(prices)):
        delta = deltas[i - 1]
        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta
        
        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period
        rs = up / down if down != 0 else 0
        rsi[i] = 100. - 100. / (1. + rs)
    
    return rsi

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD, Signal line, and Histogram"""
    exp1 = pd.Series(prices).ewm(span=fast, adjust=False).mean()
    exp2 = pd.Series(prices).ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    return macd.values, signal_line.values, histogram.values

def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """Calculate Bollinger Bands"""
    sma = pd.Series(prices).rolling(window=period).mean()
    std = pd.Series(prices).rolling(window=period).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    return upper_band.values, sma.values, lower_band.values

def calculate_sma(prices, period):
    """Calculate Simple Moving Average"""
    return pd.Series(prices).rolling(window=period).mean().values

def calculate_ema(prices, period):
    """Calculate Exponential Moving Average"""
    return pd.Series(prices).ewm(span=period, adjust=False).mean().values

def execute_tool(tool_name, arguments):
    """Execute a tool (same logic as official MCP server)"""
    try:
        # Account & Portfolio
        if tool_name == "get_account":
            account = trading_client.get_account()
            return {
                # Account Status
                "account_number": str(account.account_number) if hasattr(account, 'account_number') else None,
                "status": account.status,
                "currency": str(account.currency) if hasattr(account, 'currency') else "USD",
                "pattern_day_trader": account.pattern_day_trader if hasattr(account, 'pattern_day_trader') else False,
                "trading_blocked": account.trading_blocked if hasattr(account, 'trading_blocked') else False,
                "transfers_blocked": account.transfers_blocked if hasattr(account, 'transfers_blocked') else False,
                "account_blocked": account.account_blocked if hasattr(account, 'account_blocked') else False,
                "trade_suspended_by_user": account.trade_suspended_by_user if hasattr(account, 'trade_suspended_by_user') else False,
                "shorting_enabled": account.shorting_enabled,
                "multiplier": str(account.multiplier),
                
                # Buying Power (Critical for Trading)
                "buying_power": float(account.buying_power),
                "regt_buying_power": float(account.regt_buying_power) if hasattr(account, 'regt_buying_power') and account.regt_buying_power else 0,
                "daytrading_buying_power": float(account.daytrading_buying_power) if hasattr(account, 'daytrading_buying_power') and account.daytrading_buying_power else 0,
                "non_marginable_buying_power": float(account.non_marginable_buying_power) if hasattr(account, 'non_marginable_buying_power') and account.non_marginable_buying_power else 0,
                "effective_buying_power": float(account.buying_power),  # Alias for clarity
                
                # Cash
                "cash": float(account.cash),
                "cash_withdrawable": float(account.cash_withdrawable) if hasattr(account, 'cash_withdrawable') and account.cash_withdrawable else 0,
                "pending_transfer_out": float(account.pending_transfer_out) if hasattr(account, 'pending_transfer_out') and account.pending_transfer_out else 0,
                "pending_transfer_in": float(account.pending_transfer_in) if hasattr(account, 'pending_transfer_in') and account.pending_transfer_in else 0,
                
                # Equity & Portfolio Value
                "portfolio_value": float(account.portfolio_value),
                "equity": float(account.equity),
                "last_equity": float(account.last_equity),
                
                # Position Values
                "long_market_value": float(account.long_market_value) if account.long_market_value else 0,
                "short_market_value": float(account.short_market_value) if account.short_market_value else 0,
                "position_market_value": abs(float(account.long_market_value) if account.long_market_value else 0) + abs(float(account.short_market_value) if account.short_market_value else 0),
                
                # Margin (Important for Margin Accounts)
                "initial_margin": float(account.initial_margin) if hasattr(account, 'initial_margin') and account.initial_margin else 0,
                "maintenance_margin": float(account.maintenance_margin) if hasattr(account, 'maintenance_margin') and account.maintenance_margin else 0,
                "last_maintenance_margin": float(account.last_maintenance_margin) if hasattr(account, 'last_maintenance_margin') and account.last_maintenance_margin else 0,
                "sma": float(account.sma) if hasattr(account, 'sma') and account.sma else 0,  # Special Memorandum Account
                
                # Pattern Day Trading (PDT) - CRITICAL
                "day_trade_count": int(account.daytrade_count) if hasattr(account, 'daytrade_count') else 0,
                
                # Miscellaneous
                "accrued_fees": float(account.accrued_fees) if hasattr(account, 'accrued_fees') and account.accrued_fees else 0,
                "balance_asof": str(account.balance_asof) if hasattr(account, 'balance_asof') and account.balance_asof else None,
                "crypto_status": str(account.crypto_status) if hasattr(account, 'crypto_status') else None,
                "created_at": account.created_at.isoformat() if hasattr(account, 'created_at') and account.created_at else None,
            }
        
        elif tool_name == "get_all_positions":
            positions = trading_client.get_all_positions()
            return [{
                "symbol": p.symbol,
                "qty": float(p.qty),
                "market_value": float(p.market_value),
                "cost_basis": float(p.cost_basis),
                "unrealized_pl": float(p.unrealized_pl),
                "unrealized_plpc": float(p.unrealized_plpc),
                "current_price": float(p.current_price),
                "side": str(p.side),
                "asset_class": str(p.asset_class)
            } for p in positions]
        
        elif tool_name == "close_position":
            symbol = arguments["symbol"]
            qty = arguments.get("qty")
            percentage = arguments.get("percentage")
            
            close_request = ClosePositionRequest(
                qty=str(qty) if qty else None,
                percentage=str(percentage) if percentage else None
            )
            order = trading_client.close_position(symbol, close_request)
            return {
                "success": True,
                "order_id": str(order.id),
                "symbol": order.symbol,
                "side": str(order.side),
                "qty": str(order.qty) if order.qty else None,
                "status": str(order.status)
            }
        
        # Crypto Trading
        elif tool_name == "get_crypto_latest_bar":
            symbol = arguments["symbol"]
            if '/' not in symbol:
                symbol = f"{symbol}/USD"
            
            request = CryptoLatestBarRequest(symbol_or_symbols=[symbol])
            latest_bars = crypto_data_client.get_crypto_latest_bar(request)
            
            if symbol in latest_bars:
                bar = latest_bars[symbol]
                return {
                    "symbol": symbol,
                    "price": float(bar.close),
                    "high": float(bar.high),
                    "low": float(bar.low),
                    "open": float(bar.open),
                    "volume": float(bar.volume),
                    "timestamp": bar.timestamp.isoformat()
                }
            return {"error": f"No data for {symbol}"}
        
        elif tool_name == "place_crypto_order":
            symbol = arguments["symbol"]
            if '/' not in symbol:
                symbol = f"{symbol}/USD"
            
            side = OrderSide.BUY if arguments["side"].lower() == "buy" else OrderSide.SELL
            
            order_request = MarketOrderRequest(
                symbol=symbol,
                qty=arguments.get("qty"),
                notional=arguments.get("notional"),
                side=side,
                time_in_force=TimeInForce.GTC
            )
            
            order = trading_client.submit_order(order_request)
            return {
                "success": True,
                "order_id": str(order.id),
                "symbol": order.symbol,
                "side": str(order.side),
                "qty": str(order.qty) if order.qty else None,
                "notional": str(order.notional) if order.notional else None,
                "status": str(order.status)
            }
        
        # Stock Trading
        elif tool_name == "place_stock_order":
            symbol = arguments["symbol"]
            side = OrderSide.BUY if arguments["side"].lower() == "buy" else OrderSide.SELL
            qty = arguments["qty"]
            order_type = arguments.get("order_type", "market")
            time_in_force_str = arguments.get("time_in_force", "day")
            
            # Map time in force
            tif_map = {
                "day": TimeInForce.DAY,
                "gtc": TimeInForce.GTC,
                "ioc": TimeInForce.IOC,
                "fok": TimeInForce.FOK
            }
            time_in_force = tif_map.get(time_in_force_str.lower(), TimeInForce.DAY)
            
            # Create appropriate order type
            if order_type == "market":
                order_request = MarketOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=side,
                    time_in_force=time_in_force
                )
            elif order_type == "limit":
                limit_price = arguments.get("limit_price")
                if not limit_price:
                    return {"error": "limit_price required for limit orders"}
                order_request = LimitOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=side,
                    time_in_force=time_in_force,
                    limit_price=limit_price
                )
            elif order_type == "stop":
                stop_price = arguments.get("stop_price")
                if not stop_price:
                    return {"error": "stop_price required for stop orders"}
                order_request = StopOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=side,
                    time_in_force=time_in_force,
                    stop_price=stop_price
                )
            elif order_type == "stop_limit":
                stop_price = arguments.get("stop_price")
                limit_price = arguments.get("limit_price")
                if not stop_price or not limit_price:
                    return {"error": "stop_price and limit_price required for stop_limit orders"}
                order_request = StopLimitOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=side,
                    time_in_force=time_in_force,
                    stop_price=stop_price,
                    limit_price=limit_price
                )
            else:
                return {"error": f"Unknown order_type: {order_type}"}
            
            order = trading_client.submit_order(order_request)
            return {
                "success": True,
                "order_id": str(order.id),
                "symbol": order.symbol,
                "side": str(order.side),
                "qty": str(order.qty),
                "order_type": order_type,
                "status": str(order.status),
                "limit_price": str(order.limit_price) if hasattr(order, 'limit_price') and order.limit_price else None,
                "stop_price": str(order.stop_price) if hasattr(order, 'stop_price') and order.stop_price else None
            }
        
        elif tool_name == "get_stock_quote":
            symbol = arguments["symbol"]
            request = StockLatestQuoteRequest(symbol_or_symbols=[symbol])
            quotes = stock_data_client.get_stock_latest_quote(request)
            
            if symbol in quotes:
                quote = quotes[symbol]
                return {
                    "symbol": symbol,
                    "ask_price": float(quote.ask_price),
                    "ask_size": int(quote.ask_size),
                    "bid_price": float(quote.bid_price),
                    "bid_size": int(quote.bid_size),
                    "timestamp": quote.timestamp.isoformat()
                }
            return {"error": f"No quote data for {symbol}"}
        
        elif tool_name == "get_stock_bars":
            symbol = arguments["symbol"]
            timeframe_str = arguments.get("timeframe", "1Day")
            days = arguments.get("days", 5)
            limit = arguments.get("limit", 100)
            
            # Map timeframe
            timeframe_map = {
                "1Min": TimeFrame(1, TimeFrameUnit.Minute),
                "5Min": TimeFrame(5, TimeFrameUnit.Minute),
                "15Min": TimeFrame(15, TimeFrameUnit.Minute),
                "1Hour": TimeFrame(1, TimeFrameUnit.Hour),
                "1Day": TimeFrame(1, TimeFrameUnit.Day)
            }
            timeframe = timeframe_map.get(timeframe_str, TimeFrame(1, TimeFrameUnit.Day))
            
            start_time = datetime.now() - timedelta(days=days)
            
            request = StockBarsRequest(
                symbol_or_symbols=[symbol],
                timeframe=timeframe,
                start=start_time,
                limit=limit
            )
            bars = stock_data_client.get_stock_bars(request)
            
            if symbol in bars:
                bars_list = [{
                    "timestamp": bar.timestamp.isoformat(),
                    "open": float(bar.open),
                    "high": float(bar.high),
                    "low": float(bar.low),
                    "close": float(bar.close),
                    "volume": int(bar.volume),
                    "vwap": float(bar.vwap) if bar.vwap else None
                } for bar in bars[symbol]]
                return {"symbol": symbol, "timeframe": timeframe_str, "bars": bars_list}
            return {"error": f"No bar data for {symbol}"}
        
        elif tool_name == "get_stock_snapshot":
            symbol = arguments["symbol"]
            request = StockSnapshotRequest(symbol_or_symbols=[symbol])
            snapshots = stock_data_client.get_stock_snapshot(request)
            
            if symbol in snapshots:
                snap = snapshots[symbol]
                return {
                    "symbol": symbol,
                    "latest_trade": {
                        "price": float(snap.latest_trade.price),
                        "size": int(snap.latest_trade.size),
                        "timestamp": snap.latest_trade.timestamp.isoformat()
                    } if snap.latest_trade else None,
                    "latest_quote": {
                        "ask_price": float(snap.latest_quote.ask_price),
                        "bid_price": float(snap.latest_quote.bid_price),
                        "timestamp": snap.latest_quote.timestamp.isoformat()
                    } if snap.latest_quote else None,
                    "minute_bar": {
                        "open": float(snap.minute_bar.open),
                        "high": float(snap.minute_bar.high),
                        "low": float(snap.minute_bar.low),
                        "close": float(snap.minute_bar.close),
                        "volume": int(snap.minute_bar.volume)
                    } if snap.minute_bar else None,
                    "daily_bar": {
                        "open": float(snap.daily_bar.open),
                        "high": float(snap.daily_bar.high),
                        "low": float(snap.daily_bar.low),
                        "close": float(snap.daily_bar.close),
                        "volume": int(snap.daily_bar.volume)
                    } if snap.daily_bar else None,
                    "prev_daily_bar": {
                        "open": float(snap.prev_daily_bar.open),
                        "high": float(snap.prev_daily_bar.high),
                        "low": float(snap.prev_daily_bar.low),
                        "close": float(snap.prev_daily_bar.close),
                        "volume": int(snap.prev_daily_bar.volume)
                    } if snap.prev_daily_bar else None
                }
            return {"error": f"No snapshot data for {symbol}"}
        
        # Options Trading
        elif tool_name == "get_option_contracts":
            underlying_symbol = arguments["underlying_symbol"]
            
            request_params = {"underlying_symbols": [underlying_symbol]}
            
            if "expiration_date_gte" in arguments:
                request_params["expiration_date_gte"] = arguments["expiration_date_gte"]
            if "expiration_date_lte" in arguments:
                request_params["expiration_date_lte"] = arguments["expiration_date_lte"]
            if "strike_price_gte" in arguments:
                request_params["strike_price_gte"] = arguments["strike_price_gte"]
            if "strike_price_lte" in arguments:
                request_params["strike_price_lte"] = arguments["strike_price_lte"]
            if "type" in arguments:
                request_params["type"] = arguments["type"]
            
            request_params["limit"] = arguments.get("limit", 100)
            
            request = GetOptionContractsRequest(**request_params)
            contracts = trading_client.get_option_contracts(request)
            
            return [{
                "symbol": c.symbol,
                "underlying_symbol": c.underlying_symbol,
                "name": c.name,
                "strike_price": float(c.strike_price),
                "expiration_date": c.expiration_date,
                "type": c.type,
                "style": c.style,
                "size": str(c.size)
            } for c in contracts.option_contracts]
        
        elif tool_name == "place_option_order":
            symbol = arguments["symbol"]
            side = OrderSide.BUY if arguments["side"].lower() == "buy" else OrderSide.SELL
            qty = arguments["qty"]
            order_type = arguments.get("order_type", "market")
            time_in_force_str = arguments.get("time_in_force", "day")
            
            tif_map = {"day": TimeInForce.DAY, "gtc": TimeInForce.GTC}
            time_in_force = tif_map.get(time_in_force_str.lower(), TimeInForce.DAY)
            
            if order_type == "market":
                order_request = MarketOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=side,
                    time_in_force=time_in_force
                )
            elif order_type == "limit":
                limit_price = arguments.get("limit_price")
                if not limit_price:
                    return {"error": "limit_price required for limit orders"}
                order_request = LimitOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=side,
                    time_in_force=time_in_force,
                    limit_price=limit_price
                )
            else:
                return {"error": f"Unknown order_type: {order_type}"}
            
            order = trading_client.submit_order(order_request)
            return {
                "success": True,
                "order_id": str(order.id),
                "symbol": order.symbol,
                "side": str(order.side),
                "qty": str(order.qty),
                "status": str(order.status)
            }
        
        elif tool_name == "get_option_chain":
            underlying_symbol = arguments["underlying_symbol"]
            days_to_exp = arguments.get("days_to_expiration", 60)
            
            # Calculate date range
            today = datetime.now().date()
            max_date = today + timedelta(days=days_to_exp)
            
            request = GetOptionContractsRequest(
                underlying_symbols=[underlying_symbol],
                expiration_date_gte=str(today),
                expiration_date_lte=str(max_date),
                limit=200  # Get more results for chain view
            )
            contracts = trading_client.get_option_contracts(request)
            
            # Organize by expiration and strike
            chain = {}
            for c in contracts.option_contracts:
                exp_date = c.expiration_date
                if exp_date not in chain:
                    chain[exp_date] = {"calls": [], "puts": []}
                
                contract_info = {
                    "symbol": c.symbol,
                    "strike": float(c.strike_price),
                    "name": c.name
                }
                
                if c.type == "call":
                    chain[exp_date]["calls"].append(contract_info)
                else:
                    chain[exp_date]["puts"].append(contract_info)
            
            # Sort by strike price
            for exp_date in chain:
                chain[exp_date]["calls"].sort(key=lambda x: x["strike"])
                chain[exp_date]["puts"].sort(key=lambda x: x["strike"])
            
            return {
                "underlying": underlying_symbol,
                "chain": chain,
                "total_contracts": len(contracts.option_contracts)
            }
        
        elif tool_name == "place_option_spread":
            legs = arguments["legs"]
            order_type = arguments["order_type"]
            qty = arguments.get("qty", 1)
            
            # Build leg requests
            leg_requests = []
            for leg in legs:
                side = OrderSide.BUY if leg["side"].lower() == "buy" else OrderSide.SELL
                leg_requests.append({
                    "symbol": leg["symbol"],
                    "side": side,
                    "ratio_qty": str(leg["ratio_qty"])
                })
            
            # Build multi-leg order
            order_data = {
                "order_class": "mleg",
                "type": order_type,
                "time_in_force": "day",  # Required for options
                "qty": str(qty),
                "legs": leg_requests
            }
            
            if order_type == "limit":
                limit_price = arguments.get("limit_price")
                if not limit_price:
                    return {"error": "limit_price required for limit orders"}
                order_data["limit_price"] = str(limit_price)
            
            # Submit using raw API call (multi-leg not in all SDK versions)
            headers = {
                "APCA-API-KEY-ID": trading_client.api_key,
                "APCA-API-SECRET-KEY": trading_client.secret_key
            }
            base_url = "https://paper-api.alpaca.markets" if trading_client.paper else "https://api.alpaca.markets"
            response = requests.post(f"{base_url}/v2/orders", json=order_data, headers=headers)
            
            if response.status_code == 200:
                order = response.json()
                return {
                    "success": True,
                    "order_id": order.get("id"),
                    "status": order.get("status"),
                    "legs": [f"{leg['symbol']} ({leg['side']})" for leg in legs],
                    "strategy": "multi-leg spread"
                }
            else:
                return {"error": f"Failed to place spread order: {response.text}"}
        
        elif tool_name == "close_option_position":
            # This is essentially the same as close_position
            symbol = arguments["symbol"]
            qty = arguments.get("qty")
            percentage = arguments.get("percentage")
            
            close_request = ClosePositionRequest(
                qty=str(qty) if qty else None,
                percentage=str(percentage) if percentage else None
            )
            order = trading_client.close_position(symbol, close_request)
            return {
                "success": True,
                "order_id": str(order.id),
                "symbol": order.symbol,
                "side": str(order.side),
                "qty": str(order.qty),
                "status": str(order.status)
            }
        
        # Technical Analysis
        elif tool_name == "get_technical_indicators":
            symbol = arguments["symbol"]
            timeframe_str = arguments.get("timeframe", "1Day")
            limit = min(arguments.get("limit", 200), 500)  # Cap at 500
            
            # Determine if crypto or stock
            # Check for "/" format OR common crypto symbols
            common_crypto = ["BTC", "ETH", "SOL", "DOGE", "LTC", "BCH", "LINK", "UNI", "AAVE", "XRP"]
            is_crypto = "/" in symbol or symbol.upper() in common_crypto
            
            # If crypto without "/" format, add it
            if is_crypto and "/" not in symbol:
                symbol = f"{symbol.upper()}/USD"
            
            # Map timeframe string to TimeFrame enum
            timeframe_map = {
                "1Min": TimeFrame(1, TimeFrameUnit.Minute),
                "5Min": TimeFrame(5, TimeFrameUnit.Minute),
                "15Min": TimeFrame(15, TimeFrameUnit.Minute),
                "1Hour": TimeFrame(1, TimeFrameUnit.Hour),
                "1Day": TimeFrame(1, TimeFrameUnit.Day)
            }
            timeframe = timeframe_map.get(timeframe_str, TimeFrame(1, TimeFrameUnit.Day))
            
            # Calculate date range (use dates instead of limit for better API compatibility)
            end_date = datetime.now()
            # Calculate days needed based on timeframe and limit
            if timeframe_str == "1Day":
                days = limit * 2  # Account for weekends
            elif timeframe_str == "1Hour":
                days = limit // 6  # ~6 hours per trading day
            else:
                days = limit // 2  # Conservative estimate
            start_date = end_date - timedelta(days=max(days, 365))
            
            try:
                # Fetch historical bars using date range
                if is_crypto:
                    # Use Alpaca for crypto (works great on free tier)
                    from alpaca.data.requests import CryptoBarsRequest
                    request = CryptoBarsRequest(
                        symbol_or_symbols=[symbol],
                        timeframe=timeframe,
                        start=start_date,
                        end=end_date
                    )
                    bars = crypto_data_client.get_crypto_bars(request)
                    if symbol not in bars.data:
                        return {"error": f"No data available for {symbol}"}
                    bars_data = list(bars.data[symbol])
                    
                    # Extract close prices and volumes from Alpaca bars
                    closes = np.array([float(bar.close) for bar in bars_data])
                    volumes = np.array([float(bar.volume) for bar in bars_data])
                    
                else:
                    # Use Yahoo Finance for stocks (free, unlimited data!)
                    try:
                        # Map timeframe to Yahoo Finance interval
                        interval_map = {
                            "1Min": "1m",
                            "5Min": "5m", 
                            "15Min": "15m",
                            "1Hour": "1h",
                            "1Day": "1d"
                        }
                        yf_interval = interval_map.get(timeframe_str, "1d")
                        
                        # Fetch data from Yahoo Finance with retry logic
                        max_retries = 3
                        retry_delay = 2
                        hist = None
                        
                        for attempt in range(max_retries):
                            try:
                                ticker = yf.Ticker(symbol)
                                hist = ticker.history(start=start_date, end=end_date, interval=yf_interval)
                                break  # Success!
                            except Exception as e:
                                if "rate limit" in str(e).lower() and attempt < max_retries - 1:
                                    # Rate limited, wait and retry
                                    import time as time_module
                                    time_module.sleep(retry_delay)
                                    retry_delay *= 2  # Exponential backoff
                                    continue
                                else:
                                    raise  # Give up after retries or if different error
                        
                        if hist is None or hist.empty:
                            return {"error": f"No data available for {symbol} from Yahoo Finance. Check symbol is valid."}
                        
                        # Limit to requested number of bars (most recent)
                        if len(hist) > limit:
                            hist = hist.tail(limit)
                        
                        # Extract close prices and volumes from Yahoo data
                        closes = hist['Close'].values
                        volumes = hist['Volume'].values
                        
                        if len(closes) < 50:
                            return {"error": f"Insufficient data for {symbol}: only {len(closes)} bars available (need at least 50)"}
                        
                    except Exception as e:
                        return {"error": f"Failed to fetch stock data from Yahoo Finance: {str(e)}. Symbol: {symbol}. Try again in a few moments if rate limited."}
                
                # Limit to requested number of bars (most recent) for crypto
                if is_crypto and len(closes) > limit:
                    closes = closes[-limit:]
                    volumes = volumes[-limit:]
                
                if len(closes) < 50:
                    return {"error": f"Insufficient data: only {len(closes)} bars available (need at least 50)"}
                
                # Calculate indicators
                rsi = calculate_rsi(closes)
                macd, macd_signal, macd_hist = calculate_macd(closes)
                bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(closes)
                sma_20 = calculate_sma(closes, 20)
                sma_50 = calculate_sma(closes, 50)
                sma_200 = calculate_sma(closes, 200) if len(closes) >= 200 else None
                ema_12 = calculate_ema(closes, 12)
                ema_26 = calculate_ema(closes, 26)
                
                # Current (latest) values
                current_price = closes[-1]
                current_rsi = rsi[-1]
                current_macd = macd[-1]
                current_macd_signal = macd_signal[-1]
                current_macd_hist = macd_hist[-1]
                
                # Volume analysis
                avg_volume = np.mean(volumes[-20:])  # 20-period average
                current_volume = volumes[-1]
                volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
                
                # Trend analysis
                price_vs_sma20 = ((current_price - sma_20[-1]) / sma_20[-1] * 100) if not np.isnan(sma_20[-1]) else None
                price_vs_sma50 = ((current_price - sma_50[-1]) / sma_50[-1] * 100) if not np.isnan(sma_50[-1]) else None
                price_vs_sma200 = ((current_price - sma_200[-1]) / sma_200[-1] * 100) if sma_200 is not None and not np.isnan(sma_200[-1]) else None
                
                # Bollinger Band position
                bb_position = None
                if not np.isnan(bb_upper[-1]) and not np.isnan(bb_lower[-1]):
                    bb_range = bb_upper[-1] - bb_lower[-1]
                    if bb_range > 0:
                        bb_position = ((current_price - bb_lower[-1]) / bb_range * 100)
                
                # Signal interpretations
                rsi_signal = "overbought" if current_rsi > 70 else "oversold" if current_rsi < 30 else "neutral"
                macd_signal_str = "bullish" if current_macd > current_macd_signal else "bearish"
                trend = "uptrend" if price_vs_sma20 and price_vs_sma20 > 0 and price_vs_sma50 and price_vs_sma50 > 0 else "downtrend" if price_vs_sma20 and price_vs_sma20 < 0 and price_vs_sma50 and price_vs_sma50 < 0 else "sideways"
                
                return {
                    "symbol": symbol,
                    "timeframe": timeframe_str,
                    "current_price": float(current_price),
                    "bars_analyzed": len(closes),
                    
                    "rsi": {
                        "value": float(current_rsi),
                        "signal": rsi_signal,
                        "interpretation": f"RSI at {current_rsi:.1f} indicates {rsi_signal} conditions"
                    },
                    
                    "macd": {
                        "macd": float(current_macd),
                        "signal": float(current_macd_signal),
                        "histogram": float(current_macd_hist),
                        "trend": macd_signal_str,
                        "interpretation": f"MACD {macd_signal_str} ({current_macd:.2f} vs signal {current_macd_signal:.2f})"
                    },
                    
                    "moving_averages": {
                        "sma_20": float(sma_20[-1]) if not np.isnan(sma_20[-1]) else None,
                        "sma_50": float(sma_50[-1]) if not np.isnan(sma_50[-1]) else None,
                        "sma_200": float(sma_200[-1]) if sma_200 is not None and not np.isnan(sma_200[-1]) else None,
                        "ema_12": float(ema_12[-1]) if not np.isnan(ema_12[-1]) else None,
                        "ema_26": float(ema_26[-1]) if not np.isnan(ema_26[-1]) else None,
                        "price_vs_sma20_pct": round(price_vs_sma20, 2) if price_vs_sma20 else None,
                        "price_vs_sma50_pct": round(price_vs_sma50, 2) if price_vs_sma50 else None,
                        "price_vs_sma200_pct": round(price_vs_sma200, 2) if price_vs_sma200 else None,
                        "trend": trend
                    },
                    
                    "bollinger_bands": {
                        "upper": float(bb_upper[-1]) if not np.isnan(bb_upper[-1]) else None,
                        "middle": float(bb_middle[-1]) if not np.isnan(bb_middle[-1]) else None,
                        "lower": float(bb_lower[-1]) if not np.isnan(bb_lower[-1]) else None,
                        "position_pct": round(bb_position, 1) if bb_position else None,
                        "interpretation": f"Price at {bb_position:.0f}% of BB range (0%=lower, 100%=upper)" if bb_position else None
                    },
                    
                    "volume": {
                        "current": float(current_volume),
                        "average_20": float(avg_volume),
                        "ratio": round(volume_ratio, 2),
                        "interpretation": f"Volume is {volume_ratio:.1f}x the 20-period average"
                    },
                    
                    "summary": {
                        "overall_trend": trend,
                        "momentum": rsi_signal,
                        "strength": "strong" if abs(price_vs_sma20 or 0) > 5 else "moderate" if abs(price_vs_sma20 or 0) > 2 else "weak"
                    }
                }
            except Exception as e:
                return {"error": f"Failed to calculate indicators: {str(e)}"}
        
        # Order Management
        elif tool_name == "get_orders":
            status_str = arguments.get("status", "open")
            limit = arguments.get("limit", 50)
            
            status_map = {
                "open": QueryOrderStatus.OPEN,
                "closed": QueryOrderStatus.CLOSED,
                "all": QueryOrderStatus.ALL
            }
            status = status_map.get(status_str.lower(), QueryOrderStatus.OPEN)
            
            request = GetOrdersRequest(status=status, limit=limit)
            orders = trading_client.get_orders(request)
            
            return [{
                "order_id": str(o.id),
                "symbol": o.symbol,
                "side": str(o.side),
                "qty": str(o.qty),
                "filled_qty": str(o.filled_qty) if o.filled_qty else "0",
                "order_type": str(o.order_type),
                "status": str(o.status),
                "created_at": o.created_at.isoformat(),
                "limit_price": str(o.limit_price) if hasattr(o, 'limit_price') and o.limit_price else None,
                "stop_price": str(o.stop_price) if hasattr(o, 'stop_price') and o.stop_price else None
            } for o in orders]
        
        elif tool_name == "cancel_order":
            order_id = arguments["order_id"]
            trading_client.cancel_order_by_id(order_id)
            return {"success": True, "message": f"Order {order_id} cancelled"}
        
        elif tool_name == "cancel_all_orders":
            trading_client.cancel_orders()
            return {"success": True, "message": "All orders cancelled"}
        
        # Market News
        elif tool_name == "get_news":
            symbols = arguments.get("symbols")
            limit = arguments.get("limit", 10)
            
            # NewsRequest expects comma-separated string or single symbol, not list
            if symbols:
                if isinstance(symbols, list):
                    # Convert list to comma-separated string
                    symbol_str = ",".join(symbols)
                else:
                    symbol_str = symbols
                
                request = NewsRequest(
                    symbols=symbol_str,
                    limit=limit
                )
            else:
                # Get general market news
                request = NewsRequest(limit=limit)
            
            news_response = news_client.get_news(request)
            
            # NewsSet object has .data['news'] structure, where each news item is a News object
            if hasattr(news_response, 'data') and isinstance(news_response.data, dict):
                news_articles = news_response.data.get('news', [])
            else:
                news_articles = []
            
            if not news_articles:
                return {"error": "No news articles available"}
            
            # News objects have attributes, not dictionary keys
            return [{
                "headline": article.headline if hasattr(article, 'headline') else article.get('headline', 'N/A'),
                "summary": article.summary if hasattr(article, 'summary') else article.get('summary', ''),
                "author": article.author if hasattr(article, 'author') else article.get('author', 'Unknown'),
                "created_at": article.created_at.isoformat() if hasattr(article, 'created_at') else "",
                "updated_at": article.updated_at.isoformat() if hasattr(article, 'updated_at') else "",
                "url": article.url if hasattr(article, 'url') else article.get('url', ''),
                "symbols": article.symbols if hasattr(article, 'symbols') else article.get('symbols', [])
            } for article in news_articles]
        
        # Market Clock
        elif tool_name == "get_market_clock":
            clock = trading_client.get_clock()
            return {
                "is_open": clock.is_open,
                "timestamp": clock.timestamp.isoformat(),
                "next_open": clock.next_open.isoformat(),
                "next_close": clock.next_close.isoformat()
            }
        
        # Trading Memory / Notes System
        elif tool_name == "read_trading_memory":
            memory_file = "trading_memory.md"
            if os.path.exists(memory_file):
                with open(memory_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Format with line numbers for easy editing
                numbered_content = ""
                for i, line in enumerate(lines, 1):
                    numbered_content += f"{i:4d}| {line}"
                
                return {
                    "success": True,
                    "content": numbered_content,
                    "total_lines": len(lines),
                    "file_size": sum(len(line) for line in lines),
                    "exists": True
                }
            else:
                return {
                    "success": True,
                    "content": "   1| # Trading Memory\n   2| \n   3| _No entries yet. Start documenting your trades!_\n",
                    "total_lines": 3,
                    "file_size": 0,
                    "exists": False
                }
        
        elif tool_name == "write_trading_memory":
            memory_file = "trading_memory.md"
            content = arguments.get("content", "")
            try:
                with open(memory_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                return {
                    "success": True,
                    "message": f"Trading memory updated ({len(content)} characters)",
                    "file": memory_file
                }
            except Exception as e:
                return {"error": f"Failed to write memory: {str(e)}"}
        
        elif tool_name == "append_trading_memory":
            memory_file = "trading_memory.md"
            content = arguments.get("content", "")
            try:
                # Create file if it doesn't exist
                if not os.path.exists(memory_file):
                    with open(memory_file, 'w', encoding='utf-8') as f:
                        f.write("# Trading Memory\n\n")
                
                # Append content
                with open(memory_file, 'a', encoding='utf-8') as f:
                    f.write(content)
                return {
                    "success": True,
                    "message": f"Appended {len(content)} characters to trading memory",
                    "file": memory_file
                }
            except Exception as e:
                return {"error": f"Failed to append memory: {str(e)}"}
        
        elif tool_name == "edit_trading_memory_lines":
            memory_file = "trading_memory.md"
            from_line = arguments.get("from_line")
            to_line = arguments.get("to_line")
            new_content = arguments.get("new_content", "")
            operation = arguments.get("operation", "replace")
            
            try:
                # Read current content
                if os.path.exists(memory_file):
                    with open(memory_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                else:
                    lines = ["# Trading Memory\n\n"]
                
                # Validate line numbers (1-indexed, convert to 0-indexed for Python)
                if from_line < 1 or to_line < 1:
                    return {"error": "Line numbers must be >= 1"}
                if from_line > len(lines) + 1:
                    return {"error": f"from_line {from_line} exceeds file length {len(lines)}"}
                
                # Convert to 0-indexed
                start_idx = from_line - 1
                end_idx = min(to_line, len(lines))  # Inclusive, so don't subtract 1 yet
                
                # Perform operation
                if operation == "delete":
                    # Delete lines from start_idx to end_idx (inclusive)
                    del lines[start_idx:end_idx]
                    operation_desc = f"Deleted lines {from_line}-{to_line}"
                
                elif operation == "insert_before":
                    # Insert new content before start_idx
                    new_lines = new_content.split('\n')
                    # Add newline to each line if not already present
                    new_lines = [line if line.endswith('\n') else line + '\n' for line in new_lines if line]
                    lines[start_idx:start_idx] = new_lines
                    operation_desc = f"Inserted {len(new_lines)} line(s) before line {from_line}"
                
                else:  # replace (default)
                    # Replace lines from start_idx to end_idx with new content
                    new_lines = new_content.split('\n')
                    new_lines = [line if line.endswith('\n') else line + '\n' for line in new_lines if line]
                    lines[start_idx:end_idx] = new_lines
                    operation_desc = f"Replaced lines {from_line}-{to_line} with {len(new_lines)} line(s)"
                
                # Write back
                with open(memory_file, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                
                return {
                    "success": True,
                    "message": operation_desc,
                    "file": memory_file,
                    "new_line_count": len(lines)
                }
            except Exception as e:
                return {"error": f"Failed to edit memory: {str(e)}"}
        
        elif tool_name == "clear_trading_memory":
            memory_file = "trading_memory.md"
            try:
                with open(memory_file, 'w', encoding='utf-8') as f:
                    f.write("# Trading Memory\n\n_Memory cleared. Start fresh!_\n")
                return {
                    "success": True,
                    "message": "Trading memory cleared",
                    "file": memory_file
                }
            except Exception as e:
                return {"error": f"Failed to clear memory: {str(e)}"}
        
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}")
        return {"error": str(e)}

# ==================== AI Model Helper Functions ====================

def convert_tools_to_openai_format():
    """Convert Anthropic tool format to OpenAI function format"""
    openai_tools = []
    for tool in TOOLS:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"]
            }
        })
    return openai_tools

def call_ai_with_tools(messages_for_ai, max_turns=10):
    """
    Unified function to call either Claude or DeepSeek with tool support.
    Handles multi-turn conversations with tool use for both models.
    
    Args:
        messages_for_ai: List of message dicts (format depends on model)
        max_turns: Maximum conversation turns
    
    Returns:
        Final text response from the AI
    """
    global conversation_history
    
    if ai_model == "deepseek":
        return _call_deepseek_with_tools(messages_for_ai, max_turns)
    else:
        return _call_claude_with_tools(messages_for_ai, max_turns)

def _call_claude_with_tools(messages, max_turns):
    """Call Claude with tool support (multi-turn conversation)"""
    turn_count = 0
    
    while turn_count < max_turns:
        turn_count += 1
        
        logger.info(f"🔄 Calling Claude API (turn {turn_count})...")
        
        # Call Claude with tools
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            tools=TOOLS,
            messages=messages
        )
        
        logger.info(f"✅ Claude responded - Turn {turn_count}: stop_reason={response.stop_reason}, content_blocks={len(response.content)}")
        
        # Process response content
        assistant_content = []
        tool_results = []
        has_tool_use = False
        
        for block in response.content:
            if hasattr(block, 'text') and block.text:
                assistant_content.append({"type": "text", "text": block.text})
                logger.info(f"  Text block: {block.text[:100]}...")
            elif block.type == "tool_use":
                has_tool_use = True
                assistant_content.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })
                
                logger.info(f"  Tool use: {block.name} with {block.input}")
                
                # Log to auto-trading if active
                if autotrading_active:
                    add_autotrading_log(f"⚡ Executing tool: {block.name}", "trade")
                
                # Execute tool
                tool_name = block.name
                result = execute_tool(tool_name, block.input)
                logger.info(f"  Tool result: {str(result)[:100]}...")
                
                # Log result to auto-trading if active
                if autotrading_active:
                    if isinstance(result, dict) and 'error' in result:
                        add_autotrading_log(f"❌ Tool error: {result['error']}", "error")
                    elif isinstance(result, list):
                        # Special handling for specific tools
                        if tool_name == "get_news" and len(result) > 0:
                            add_autotrading_log(f"✅ Found {len(result)} news articles", "success")
                            # Show details of each article
                            for idx, article in enumerate(result[:5], 1):  # Show first 5 articles
                                headline = article.get('headline', 'No headline')
                                summary = article.get('summary', '')
                                symbols = article.get('symbols', [])
                                symbols_str = ', '.join(symbols[:3]) if symbols else 'General'
                                
                                add_autotrading_log(f"  📰 Article {idx}: {headline}", "info")
                                if summary:
                                    # Truncate summary to first 150 characters
                                    summary_short = summary[:150] + "..." if len(summary) > 150 else summary
                                    add_autotrading_log(f"      {summary_short}", "info")
                                add_autotrading_log(f"      🏷️ Related: {symbols_str}", "info")
                            
                            if len(result) > 5:
                                add_autotrading_log(f"  ... and {len(result) - 5} more articles", "info")
                        elif tool_name == "get_all_positions":
                            add_autotrading_log(f"✅ Current positions: {len(result)}", "success")
                        elif tool_name == "get_orders":
                            add_autotrading_log(f"✅ Open orders: {len(result)}", "success")
                        else:
                            add_autotrading_log(f"✅ Tool result: {len(result)} items", "success")
                    elif isinstance(result, dict):
                        result_preview = str(result)[:100]
                        add_autotrading_log(f"✅ Tool result: {result_preview}...", "success")
                    else:
                        add_autotrading_log(f"✅ Tool result: {str(result)[:100]}...", "success")
                
                # Include error details in tool result for better debugging
                if isinstance(result, dict) and 'error' in result:
                    result_content = json.dumps({
                        "error": result['error'],
                        "tool": block.name,
                        "arguments": block.input
                    })
                else:
                    result_content = json.dumps(result)
                
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_content
                })
        
        # Add assistant response to messages
        messages.append({"role": "assistant", "content": assistant_content})
        
        # If there were tool uses, add results and continue conversation
        if has_tool_use and tool_results:
            messages.append({"role": "user", "content": tool_results})
            logger.info(f"  Continuing conversation with {len(tool_results)} tool results")
            continue  # Get next response from Claude
        
        # No tool use - conversation is complete
        # Extract final text response
        response_text = ""
        for block in response.content:
            if hasattr(block, 'text') and block.text:
                response_text += block.text
        
        logger.info(f"Conversation complete after {turn_count} turns")
        return response_text
    
    # Max turns reached
    logger.warning(f"Max turns ({max_turns}) reached")
    return "I've reached the maximum number of conversation turns. Please try again."

def _call_deepseek_with_tools(messages, max_turns):
    """Call DeepSeek (OpenAI-compatible) with tool support"""
    # Convert messages from Anthropic format to OpenAI format
    openai_messages = []
    for msg in messages:
        if msg["role"] == "assistant" and isinstance(msg["content"], list):
            # Convert Anthropic assistant content blocks to OpenAI format
            text_parts = []
            tool_calls = []
            for block in msg["content"]:
                if block.get("type") == "text":
                    text_parts.append(block["text"])
                elif block.get("type") == "tool_use":
                    tool_calls.append({
                        "id": block["id"],
                        "type": "function",
                        "function": {
                            "name": block["name"],
                            "arguments": json.dumps(block["input"])
                        }
                    })
            
            if text_parts:
                openai_messages.append({"role": "assistant", "content": " ".join(text_parts)})
            if tool_calls:
                openai_messages.append({"role": "assistant", "content": None, "tool_calls": tool_calls})
        
        elif msg["role"] == "user" and isinstance(msg["content"], list):
            # Convert Anthropic tool_result to OpenAI tool message
            for block in msg["content"]:
                if block.get("type") == "tool_result":
                    openai_messages.append({
                        "role": "tool",
                        "tool_call_id": block["tool_use_id"],
                        "content": block["content"]
                    })
        else:
            # Simple message
            openai_messages.append(msg)
    
    openai_tools = convert_tools_to_openai_format()
    turn_count = 0
    
    while turn_count < max_turns:
        turn_count += 1
        
        logger.info(f"🔄 Calling DeepSeek API (turn {turn_count})...")
        
        # Call DeepSeek with tools
        response = openai_client.chat.completions.create(
            model="deepseek-chat",
            messages=openai_messages,
            tools=openai_tools,
            max_tokens=4096
        )
        
        message = response.choices[0].message
        logger.info(f"✅ DeepSeek responded - Turn {turn_count}: finish_reason={response.choices[0].finish_reason}")
        
        # Log reasoning/thinking tokens if present
        if hasattr(response, 'usage') and response.usage:
            logger.info(f"📊 Token usage: prompt={response.usage.prompt_tokens}, completion={response.usage.completion_tokens}")
        
        # Check if there are tool calls
        if message.tool_calls:
            # Add assistant message to history
            openai_messages.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in message.tool_calls
                ]
            })
            
            # Execute tools and collect results
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                logger.info(f"  Tool use: {function_name} with {function_args}")
                
                # Log to auto-trading if active
                if autotrading_active:
                    add_autotrading_log(f"⚡ Executing tool: {function_name}", "trade")
                
                # Execute tool
                result = execute_tool(function_name, function_args)
                logger.info(f"  Tool result: {str(result)[:100]}...")
                
                # Log result to auto-trading if active
                if autotrading_active:
                    if isinstance(result, dict) and 'error' in result:
                        add_autotrading_log(f"❌ Tool error: {result['error']}", "error")
                    elif isinstance(result, list):
                        # Special handling for specific tools
                        if function_name == "get_news" and len(result) > 0:
                            add_autotrading_log(f"✅ Found {len(result)} news articles", "success")
                            # Show details of each article
                            for idx, article in enumerate(result[:5], 1):  # Show first 5 articles
                                headline = article.get('headline', 'No headline')
                                summary = article.get('summary', '')
                                symbols = article.get('symbols', [])
                                symbols_str = ', '.join(symbols[:3]) if symbols else 'General'
                                
                                add_autotrading_log(f"  📰 Article {idx}: {headline}", "info")
                                if summary:
                                    # Truncate summary to first 150 characters
                                    summary_short = summary[:150] + "..." if len(summary) > 150 else summary
                                    add_autotrading_log(f"      {summary_short}", "info")
                                add_autotrading_log(f"      🏷️ Related: {symbols_str}", "info")
                            
                            if len(result) > 5:
                                add_autotrading_log(f"  ... and {len(result) - 5} more articles", "info")
                        elif function_name == "get_all_positions":
                            add_autotrading_log(f"✅ Current positions: {len(result)}", "success")
                        elif function_name == "get_orders":
                            add_autotrading_log(f"✅ Open orders: {len(result)}", "success")
                        else:
                            add_autotrading_log(f"✅ Tool result: {len(result)} items", "success")
                    elif isinstance(result, dict):
                        result_preview = str(result)[:100]
                        add_autotrading_log(f"✅ Tool result: {result_preview}...", "success")
                    else:
                        add_autotrading_log(f"✅ Tool result: {str(result)[:100]}...", "success")
                
                # Add tool result to messages
                openai_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })
            
            continue  # Get next response
        
        # No tool calls - conversation is complete
        logger.info(f"Conversation complete after {turn_count} turns")
        return message.content or ""
    
    # Max turns reached
    logger.warning(f"Max turns ({max_turns}) reached")
    return "I've reached the maximum number of conversation turns. Please try again."

# ==================== Flask Routes ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "implementation": "alpaca-py (same library as official Alpaca MCP server)",
        "initialized": trading_client is not None
    })

@app.route('/api/initialize', methods=['POST'])
def initialize():
    """Initialize with API keys"""
    global trading_client, crypto_data_client, stock_data_client, anthropic_client, openai_client, conversation_history, news_client, ai_model
    
    data = request.json
    alpaca_key = data.get('alpaca_key')
    alpaca_secret = data.get('alpaca_secret')
    claude_key = data.get('claude_key')
    deepseek_key = data.get('deepseek_key')
    selected_model = data.get('ai_model', 'claude')
    paper_mode = data.get('paper_mode', True)
    
    try:
        # Initialize Alpaca clients (same as official MCP server)
        trading_client = TradingClient(
            api_key=alpaca_key,
            secret_key=alpaca_secret,
            paper=paper_mode
        )
        
        crypto_data_client = CryptoHistoricalDataClient()
        stock_data_client = StockHistoricalDataClient(
            api_key=alpaca_key,
            secret_key=alpaca_secret
        )
        
        # Initialize dedicated news client
        news_client = NewsClient(
            api_key=alpaca_key,
            secret_key=alpaca_secret
        )
        
        # Initialize AI client based on selection
        ai_model = selected_model
        if ai_model == "deepseek":
            # Initialize DeepSeek (OpenAI-compatible)
            openai_client = OpenAI(
                api_key=deepseek_key,
                base_url="https://api.deepseek.com"
            )
            anthropic_client = None
            logger.info("Initialized with DeepSeek-V3.2-Exp (Reasoning Model)")
        else:
            # Initialize Claude
            anthropic_client = Anthropic(api_key=claude_key)
            openai_client = None
            logger.info("Initialized with Claude 3.5 Sonnet")
        
        # Clear conversation history
        conversation_history = []
        
        logger.info(f"Initialized in {'PAPER' if paper_mode else 'LIVE'} mode with comprehensive trading tools")
        logger.info(f"Available tools: {len(TOOLS)} (crypto, stocks, options, technical indicators, market data, news, orders, market clock, trading memory)")
        
        return jsonify({
            "status": "initialized",
            "paper_mode": paper_mode,
            "ai_model": ai_model,
            "tools_count": len(TOOLS)
        })
    except Exception as e:
        logger.error(f"Initialization error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/account', methods=['GET'])
def get_account():
    """Get account information"""
    if not trading_client:
        return jsonify({"error": "Not initialized"}), 400
    
    try:
        result = execute_tool("get_account", {})
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting account: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/positions', methods=['GET'])
def get_positions():
    """Get current positions"""
    if not trading_client:
        return jsonify({"error": "Not initialized"}), 400
    
    try:
        result = execute_tool("get_all_positions", {})
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat endpoint for trading commands"""
    global conversation_history
    
    data = request.json
    user_message = data.get('message')
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    
    # Check if appropriate AI client is initialized
    if ai_model == "deepseek" and not openai_client:
        return jsonify({"error": "DeepSeek client not initialized"}), 400
    elif ai_model == "claude" and not anthropic_client:
        return jsonify({"error": "Claude client not initialized"}), 400
    
    if not trading_client:
        return jsonify({"error": "Trading client not initialized"}), 400
    
    try:
        # Add user message to history
        conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Use unified AI function
        response_text = call_ai_with_tools(conversation_history)
        
        # Update conversation history (handled internally by call_ai_with_tools)
        logger.info("Chat complete")
        return jsonify({"response": response_text})
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({"error": str(e)}), 500

# Auto-trading endpoints (same implementation)
@app.route('/api/autotrading/start', methods=['POST'])
def start_autotrading():
    """Start auto-trading"""
    global autotrading_active, autotrading_thread, autotrading_config, autotrading_logs
    
    # Check if appropriate AI client is initialized
    if ai_model == "deepseek" and not openai_client:
        return jsonify({"error": "DeepSeek client not initialized"}), 400
    elif ai_model == "claude" and not anthropic_client:
        return jsonify({"error": "Claude client not initialized"}), 400
    
    if not trading_client:
        return jsonify({"error": "Trading client not initialized"}), 400
    
    if autotrading_active:
        return jsonify({"error": "Auto-trading is already active"}), 400
    
    data = request.json
    autotrading_config = data
    
    # Don't clear logs - keep history across restarts
    add_autotrading_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "info")
    add_autotrading_log(f"📊 Starting auto-trading with {len(data.get('categories', []))} categories and {len(data.get('keywords', []))} keywords", "success")
    
    autotrading_active = True
    autotrading_thread = threading.Thread(target=autotrading_loop, daemon=True)
    autotrading_thread.start()
    
    return jsonify({"status": "started", "config": autotrading_config})

@app.route('/api/autotrading/stop', methods=['POST'])
def stop_autotrading():
    """Stop auto-trading"""
    global autotrading_active
    
    if not autotrading_active:
        return jsonify({"error": "Auto-trading is not active"}), 400
    
    autotrading_active = False
    add_autotrading_log("🛑 Stop requested by user", "info")
    
    return jsonify({"status": "stopped"})

@app.route('/api/autotrading/status', methods=['GET'])
def autotrading_status():
    """Get auto-trading status"""
    return jsonify({
        "active": autotrading_active,
        "config": autotrading_config if autotrading_active else None
    })

@app.route('/api/autotrading/logs', methods=['GET'])
def autotrading_logs_endpoint():
    """Get recent auto-trading logs"""
    return jsonify({
        "logs": autotrading_logs[-200:]  # Return last 200 logs (plenty for refreshes)
    })

@app.route('/api/autotrading/logs/clear', methods=['POST'])
def clear_autotrading_logs():
    """Clear auto-trading logs"""
    global autotrading_logs
    autotrading_logs = []
    add_autotrading_log("🧹 Logs cleared", "info")
    return jsonify({"status": "cleared"})

def autotrading_loop():
    """Background loop for auto-trading"""
    global autotrading_active, autotrading_config
    
    add_autotrading_log("🚀 Auto-trading loop started", "success")
    
    while autotrading_active:
        try:
            if not autotrading_config:
                time.sleep(5)
                continue
            
            add_autotrading_log("🔍 Analyzing market conditions...", "info")
            
            # Get market clock status FIRST
            market_clock = execute_tool("get_market_clock", {})
            
            # Check for errors in market clock
            if isinstance(market_clock, dict) and 'error' in market_clock:
                add_autotrading_log(f"⚠️ Failed to get market clock: {market_clock['error']}", "error")
                market_clock = {"is_open": False, "timestamp": "Unknown", "next_open": "Unknown", "next_close": "Unknown"}
            
            # Get account and positions
            account_info = execute_tool("get_account", {})
            positions_list = execute_tool("get_all_positions", {})
            
            # Check for errors in account info
            if isinstance(account_info, dict) and 'error' in account_info:
                add_autotrading_log(f"❌ Failed to get account info: {account_info['error']}", "error")
                add_autotrading_log("⏸️ Skipping this cycle, will retry next interval", "info")
                time.sleep(autotrading_config.get("checkInterval", 60))
                continue
            
            # Check for errors in positions
            if isinstance(positions_list, dict) and 'error' in positions_list:
                add_autotrading_log(f"❌ Failed to get positions: {positions_list['error']}", "error")
                positions_list = []  # Continue with empty positions
            
            # Ensure positions_list is actually a list
            if not isinstance(positions_list, list):
                positions_list = []
            
            # Extract key account metrics
            portfolio_value = account_info.get('portfolio_value', 0)
            cash = account_info.get('cash', 0)
            equity = account_info.get('equity', 0)
            buying_power = account_info.get('buying_power', 0)
            regt_buying_power = account_info.get('regt_buying_power', 0)
            daytrading_buying_power = account_info.get('daytrading_buying_power', 0)
            day_trade_count = account_info.get('day_trade_count', 0)
            pattern_day_trader = account_info.get('pattern_day_trader', False)
            account_status = account_info.get('status', 'UNKNOWN')
            long_market_value = account_info.get('long_market_value', 0)
            short_market_value = account_info.get('short_market_value', 0)
            initial_margin = account_info.get('initial_margin', 0)
            maintenance_margin = account_info.get('maintenance_margin', 0)
            
            # Warn if account appears empty (but only if no positions exist)
            if portfolio_value == 0 and cash == 0 and buying_power == 0 and len(positions_list) == 0:
                add_autotrading_log("⚠️ WARNING: Account shows $0 balance and no positions. This could mean:", "error")
                add_autotrading_log("   1. Paper trading account needs to be reset to get virtual funds", "error")
                add_autotrading_log("   2. Alpaca API keys may not be properly configured", "error")
                add_autotrading_log(f"   3. Account status is: {account_status}", "error")
                add_autotrading_log("   💡 TIP: Visit https://app.alpaca.markets/paper/dashboard/overview to check your paper account", "info")
                add_autotrading_log("⏸️ Skipping trading until account is funded", "info")
                time.sleep(autotrading_config.get("checkInterval", 60))
                continue
            
            # Special warning if values show $0 but positions exist (data inconsistency)
            if (portfolio_value == 0 or cash == 0) and len(positions_list) > 0:
                add_autotrading_log(f"⚠️ Note: Account values show $0 but {len(positions_list)} position(s) exist. This may be a temporary API sync issue.", "info")
                add_autotrading_log("   The AI will still analyze your positions and market conditions.", "info")
            
            # Market Status Display
            is_open = market_clock.get('is_open', False)
            market_status = "🟢 OPEN" if is_open else "🔴 CLOSED"
            next_event = market_clock.get('next_open' if not is_open else 'next_close', 'Unknown')
            
            # Comprehensive account summary
            add_autotrading_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "info")
            add_autotrading_log(f"🕐 MARKET STATUS: {market_status}", "info" if is_open else "error")
            if is_open:
                add_autotrading_log(f"   Market closes at: {next_event}", "info")
                add_autotrading_log("   ✅ Stocks: Can trade (market hours)", "info")
                add_autotrading_log("   ✅ Crypto: Can trade (24/7)", "info")
            else:
                add_autotrading_log(f"   Market opens at: {next_event}", "info")
                add_autotrading_log("   ❌ Stocks: CLOSED (no stock trading)", "error")
                add_autotrading_log("   ✅ Crypto: Can trade (24/7)", "info")
            add_autotrading_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "info")
            add_autotrading_log(f"💼 ACCOUNT OVERVIEW (Status: {account_status})", "info")
            add_autotrading_log(f"   Portfolio Value: ${portfolio_value:,.2f} | Equity: ${equity:,.2f}", "info")
            add_autotrading_log(f"   Cash: ${cash:,.2f} | Positions: {len(positions_list)}", "info")
            
            # Buying Power Breakdown
            add_autotrading_log("💰 BUYING POWER", "info")
            add_autotrading_log(f"   RegT Buying Power: ${regt_buying_power:,.2f}", "info")
            add_autotrading_log(f"   Day Trading Buying Power: ${daytrading_buying_power:,.2f}", "info")
            add_autotrading_log(f"   Effective Buying Power: ${buying_power:,.2f}", "info")
            
            # Position Details (if any)
            if long_market_value != 0 or short_market_value != 0:
                add_autotrading_log("📊 POSITIONS", "info")
                add_autotrading_log(f"   Long Market Value: ${long_market_value:,.2f}", "info")
                add_autotrading_log(f"   Short Market Value: ${short_market_value:,.2f}", "info")
            
            # Margin Info (if applicable)
            if initial_margin > 0 or maintenance_margin > 0:
                add_autotrading_log("📉 MARGIN", "info")
                add_autotrading_log(f"   Initial Margin: ${initial_margin:,.2f}", "info")
                add_autotrading_log(f"   Maintenance Margin: ${maintenance_margin:,.2f}", "info")
            
            # PDT Status (CRITICAL)
            pdt_status = "⚠️ PDT LIMITED (Swing Trade Stocks)" if day_trade_count >= 3 else "✅ CAN DAY TRADE"
            if pattern_day_trader:
                pdt_status = "🔴 FLAGGED AS PDT (Account Restricted)"
            
            add_autotrading_log(f"🚨 PDT STATUS: Day Trades: {day_trade_count}/3 - {pdt_status}", "info" if day_trade_count < 3 else "error")
            add_autotrading_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "info")
            
            # Build context with Polymarket data
            polymarket_data = autotrading_config.get("polymarketData", [])
            
            if polymarket_data:
                add_autotrading_log(f"📊 Analyzing ALL {len(polymarket_data)} Polymarket prediction markets", "info")
            
            context = f"""
═══════════════════════════════════════════════════════════════
🕐 MARKET STATUS (Check FIRST!)
═══════════════════════════════════════════════════════════════

MARKET CLOCK:
{json.dumps(market_clock, indent=2)}

IMPORTANT:
- If market is CLOSED (is_open = false): ONLY trade CRYPTO (BTC, ETH, SOL)
- If market is OPEN (is_open = true): Can trade BOTH stocks and crypto
- Stocks can ONLY be traded when is_open = true
- Crypto can be traded 24/7 regardless of market status

═══════════════════════════════════════════════════════════════
📊 YOUR CURRENT PORTFOLIO
═══════════════════════════════════════════════════════════════

ACCOUNT STATUS:
{json.dumps(account_info, indent=2)}

CURRENT POSITIONS:
{json.dumps(positions_list, indent=2)}

═══════════════════════════════════════════════════════════════
📈 POLYMARKET PREDICTION MARKETS
═══════════════════════════════════════════════════════════════
{json.dumps(polymarket_data, indent=2) if polymarket_data else "No market data available"}

═══════════════════════════════════════════════════════════════
⚙️ TRADING CONSTRAINTS
═══════════════════════════════════════════════════════════════
{json.dumps({
    "categories": autotrading_config.get("categories", []),
    "keywords": autotrading_config.get("keywords", []),
    "maxTradeAmount": autotrading_config.get("maxTradeAmount", 100)
}, indent=2)}

═══════════════════════════════════════════════════════════════

TASK: Based on YOUR CURRENT PORTFOLIO STATE (above) and the Polymarket prediction market signals, determine if any trades should be executed. Follow your systematic analysis process, starting with portfolio review.
"""
            
            model_name = "DeepSeek-V3.2-Exp" if ai_model == "deepseek" else "Claude 3.5 Sonnet"
            add_autotrading_log(f"🤖 Consulting {model_name} for trading decision...", "info")
            
            if ai_model == "deepseek":
                add_autotrading_log("🧠 DeepSeek is thinking (reasoning mode active)...", "info")
            
            system_prompt = autotrading_config.get("systemPrompt", "You are an AI trading assistant.")
            strategy_prompt = autotrading_config.get("strategyPrompt", "Execute profitable trades.")
            full_prompt = f"{system_prompt}\n\nSTRATEGY: {strategy_prompt}\n\n{context}"
            
            # Use unified AI function
            conversation = [{"role": "user", "content": full_prompt}]
            
            # Track AI response time
            start_time = time.time()
            response_text = call_ai_with_tools(conversation)
            elapsed_time = time.time() - start_time
            
            add_autotrading_log(f"✅ {model_name} responded in {elapsed_time:.1f}s", "success")
            
            # Log AI's final response (full text, no truncation)
            if len(response_text) > 1000:
                # For very long responses, log first part + summary
                add_autotrading_log(f"💭 AI says: {response_text[:800]}... [+{len(response_text)-800} more chars]", "info")
            else:
                add_autotrading_log(f"💭 AI says: {response_text}", "info")
            
            # Wait for next check
            interval = autotrading_config.get("checkInterval", 60)
            add_autotrading_log(f"⏰ Waiting {interval} seconds until next check...", "info")
            time.sleep(interval)
            
        except Exception as e:
            add_autotrading_log(f"❌ Error: {str(e)}", "error")
            logger.exception("Auto-trading error:")
            time.sleep(30)
    
    add_autotrading_log("🛑 Auto-trading loop stopped", "info")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    logger.info(f"Starting Alpaca Trading Server (using alpaca-py directly) on port {port}")
    logger.info("Uses same library and logic as official Alpaca MCP server")
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)

