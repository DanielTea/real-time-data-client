"""
Base broker interface - all broker implementations must inherit from this.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime


class BaseBroker(ABC):
    """Abstract base class for broker implementations"""
    
    def __init__(self, api_key: str, api_secret: str, paper_mode: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.paper_mode = paper_mode
        
    @abstractmethod
    def get_broker_name(self) -> str:
        """Return the broker name"""
        pass
    
    @abstractmethod
    def get_account(self) -> Dict[str, Any]:
        """
        Get account information
        Returns: {
            'cash': float,
            'equity': float,
            'buying_power': float,
            'currency': str,
            'pattern_day_trader': bool,
            ...
        }
        """
        pass
    
    @abstractmethod
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get all positions
        Returns list of: {
            'symbol': str,
            'qty': float,
            'avg_entry_price': float,
            'current_price': float,
            'market_value': float,
            'unrealized_pl': float,
            'unrealized_pl_percent': float,
            'side': 'long' or 'short',
            'asset_class': 'crypto', 'stock', 'option',
            ...
        }
        """
        pass
    
    @abstractmethod
    def close_position(self, symbol: str, qty: Optional[float] = None, percentage: Optional[float] = None) -> Dict[str, Any]:
        """
        Close a position
        Args:
            symbol: Symbol to close
            qty: Quantity to close (optional)
            percentage: Percentage to close (optional)
        Returns: Order details
        """
        pass
    
    @abstractmethod
    def get_crypto_price(self, symbol: str) -> Dict[str, Any]:
        """
        Get latest crypto price
        Args:
            symbol: Crypto symbol (e.g., 'BTC/USD', 'BTCUSDT')
        Returns: {
            'symbol': str,
            'price': float,
            'timestamp': datetime,
            ...
        }
        """
        pass
    
    @abstractmethod
    def place_crypto_order(self, symbol: str, side: str, qty: Optional[float] = None, 
                          notional: Optional[float] = None, leverage: Optional[int] = None) -> Dict[str, Any]:
        """
        Place crypto order
        Args:
            symbol: Crypto symbol
            side: 'buy' or 'sell'
            qty: Quantity (optional if notional provided)
            notional: Dollar amount (optional if qty provided)
            leverage: Leverage multiplier (optional, for futures)
        Returns: Order details
        """
        pass
    
    @abstractmethod
    def place_stock_order(self, symbol: str, side: str, qty: Optional[float] = None,
                         notional: Optional[float] = None, order_type: str = 'market',
                         limit_price: Optional[float] = None, stop_price: Optional[float] = None,
                         time_in_force: str = 'day') -> Dict[str, Any]:
        """
        Place stock order
        Args:
            symbol: Stock symbol
            side: 'buy' or 'sell'
            qty: Quantity
            notional: Dollar amount (optional)
            order_type: 'market', 'limit', 'stop', 'stop_limit'
            limit_price: Limit price (for limit orders)
            stop_price: Stop price (for stop orders)
            time_in_force: 'day', 'gtc', 'ioc', 'fok'
        Returns: Order details
        """
        pass
    
    @abstractmethod
    def get_stock_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get stock quote
        Returns: {
            'symbol': str,
            'bid': float,
            'ask': float,
            'bid_size': int,
            'ask_size': int,
            'last_price': float,
            ...
        }
        """
        pass
    
    @abstractmethod
    def get_stock_bars(self, symbol: str, timeframe: str, start: datetime, 
                       end: Optional[datetime] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get historical bars
        Args:
            symbol: Stock symbol
            timeframe: '1Min', '5Min', '1Hour', '1Day', etc.
            start: Start datetime
            end: End datetime (optional)
            limit: Max bars to return
        Returns list of: {
            'timestamp': datetime,
            'open': float,
            'high': float,
            'low': float,
            'close': float,
            'volume': int,
            ...
        }
        """
        pass
    
    @abstractmethod
    def get_orders(self, status: str = 'all') -> List[Dict[str, Any]]:
        """
        Get orders
        Args:
            status: 'open', 'closed', 'all'
        Returns list of order dicts
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel specific order"""
        pass
    
    @abstractmethod
    def cancel_all_orders(self) -> Dict[str, Any]:
        """Cancel all pending orders"""
        pass
    
    @abstractmethod
    def get_market_status(self) -> Dict[str, Any]:
        """
        Get market status
        Returns: {
            'is_open': bool,
            'next_open': datetime,
            'next_close': datetime,
            ...
        }
        """
        pass
    
    # Optional methods with default implementations
    
    def supports_options(self) -> bool:
        """Return True if broker supports options trading"""
        return False
    
    def supports_crypto_leverage(self) -> bool:
        """Return True if broker supports crypto leverage/futures"""
        return False
    
    def supports_short_selling(self) -> bool:
        """Return True if broker supports short selling"""
        return True
    
    def get_max_leverage(self, asset_class: str) -> int:
        """Return max leverage for asset class"""
        return 1
    
    def normalize_symbol(self, symbol: str, asset_class: str) -> str:
        """
        Normalize symbol format for this broker
        Args:
            symbol: Symbol to normalize
            asset_class: 'crypto', 'stock', 'option'
        Returns: Normalized symbol
        """
        return symbol
