"""
Alpaca broker implementation
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from .base import BaseBroker

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import (
    MarketOrderRequest, LimitOrderRequest, StopOrderRequest, StopLimitOrderRequest,
    GetOrdersRequest, ClosePositionRequest
)
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus
from alpaca.data.historical import CryptoHistoricalDataClient, StockHistoricalDataClient
from alpaca.data.requests import (
    CryptoBarsRequest, StockBarsRequest, StockLatestQuoteRequest, CryptoLatestBarRequest
)
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit


class AlpacaBroker(BaseBroker):
    """Alpaca broker implementation"""
    
    def __init__(self, api_key: str, api_secret: str, paper_mode: bool = True):
        super().__init__(api_key, api_secret, paper_mode)
        
        # Initialize Alpaca clients
        self.trading_client = TradingClient(
            api_key=api_key,
            secret_key=api_secret,
            paper=paper_mode
        )
        
        self.stock_data_client = StockHistoricalDataClient(
            api_key=api_key,
            secret_key=api_secret
        )
        
        self.crypto_data_client = CryptoHistoricalDataClient(
            api_key=api_key,
            secret_key=api_secret
        )
    
    def get_broker_name(self) -> str:
        return "Alpaca"
    
    def get_account(self) -> Dict[str, Any]:
        """Get account information"""
        account = self.trading_client.get_account()
        return {
            'cash': float(account.cash),
            'equity': float(account.equity),
            'buying_power': float(account.buying_power),
            'currency': account.currency,
            'pattern_day_trader': account.pattern_day_trader,
            'daytrade_count': account.daytrade_count,
            'daytrading_buying_power': float(account.daytrading_buying_power),
            'shorting_enabled': account.shorting_enabled,
            'account_blocked': account.account_blocked,
            'trading_blocked': account.trading_blocked,
        }
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """Get all positions"""
        positions = self.trading_client.get_all_positions()
        result = []
        
        for p in positions:
            result.append({
                'symbol': p.symbol,
                'qty': float(p.qty),
                'avg_entry_price': float(p.avg_entry_price),
                'current_price': float(p.current_price),
                'market_value': float(p.market_value),
                'unrealized_pl': float(p.unrealized_pl),
                'unrealized_pl_percent': float(p.unrealized_plpc) * 100,
                'side': 'long' if float(p.qty) > 0 else 'short',
                'asset_class': str(p.asset_class),
                'exchange': p.exchange,
            })
        
        return result
    
    def close_position(self, symbol: str, qty: Optional[float] = None, 
                       percentage: Optional[float] = None) -> Dict[str, Any]:
        """Close a position"""
        if percentage:
            request = ClosePositionRequest(qty=str(percentage) + "%")
        elif qty:
            request = ClosePositionRequest(qty=str(qty))
        else:
            request = None
        
        order = self.trading_client.close_position(symbol, close_options=request)
        
        return {
            'order_id': str(order.id),
            'symbol': order.symbol,
            'status': str(order.status),
            'side': str(order.side),
            'qty': float(order.qty) if order.qty else 0,
        }
    
    def get_crypto_price(self, symbol: str) -> Dict[str, Any]:
        """Get latest crypto price"""
        # Alpaca uses BTC/USD format
        symbol = self.normalize_symbol(symbol, 'crypto')
        
        request = CryptoLatestBarRequest(symbol_or_symbols=[symbol])
        bars = self.crypto_data_client.get_crypto_latest_bar(request)
        
        bar = bars[symbol]
        return {
            'symbol': symbol,
            'price': float(bar.close),
            'timestamp': bar.timestamp.isoformat() if hasattr(bar.timestamp, 'isoformat') else str(bar.timestamp),
            'open': float(bar.open),
            'high': float(bar.high),
            'low': float(bar.low),
            'volume': float(bar.volume),
        }
    
    def place_crypto_order(self, symbol: str, side: str, qty: Optional[float] = None,
                          notional: Optional[float] = None, leverage: Optional[int] = None) -> Dict[str, Any]:
        """Place crypto order"""
        symbol = self.normalize_symbol(symbol, 'crypto')
        
        order_side = OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL
        
        if notional:
            request = MarketOrderRequest(
                symbol=symbol,
                notional=notional,
                side=order_side,
                time_in_force=TimeInForce.GTC
            )
        else:
            request = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=order_side,
                time_in_force=TimeInForce.GTC
            )
        
        order = self.trading_client.submit_order(request)
        
        return {
            'order_id': str(order.id),
            'symbol': order.symbol,
            'side': str(order.side),
            'qty': float(order.qty) if order.qty else 0,
            'notional': float(order.notional) if order.notional else 0,
            'status': str(order.status),
            'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price else 0,
        }
    
    def place_stock_order(self, symbol: str, side: str, qty: Optional[float] = None,
                         notional: Optional[float] = None, order_type: str = 'market',
                         limit_price: Optional[float] = None, stop_price: Optional[float] = None,
                         time_in_force: str = 'day') -> Dict[str, Any]:
        """Place stock order"""
        order_side = OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL
        
        # Map time_in_force
        tif_map = {
            'day': TimeInForce.DAY,
            'gtc': TimeInForce.GTC,
            'ioc': TimeInForce.IOC,
            'fok': TimeInForce.FOK,
        }
        tif = tif_map.get(time_in_force.lower(), TimeInForce.DAY)
        
        # Create appropriate order request
        if order_type == 'market':
            if notional:
                request = MarketOrderRequest(
                    symbol=symbol, notional=notional, side=order_side, time_in_force=tif
                )
            else:
                request = MarketOrderRequest(
                    symbol=symbol, qty=qty, side=order_side, time_in_force=tif
                )
        elif order_type == 'limit':
            request = LimitOrderRequest(
                symbol=symbol, qty=qty, side=order_side, 
                limit_price=limit_price, time_in_force=tif
            )
        elif order_type == 'stop':
            request = StopOrderRequest(
                symbol=symbol, qty=qty, side=order_side,
                stop_price=stop_price, time_in_force=tif
            )
        elif order_type == 'stop_limit':
            request = StopLimitOrderRequest(
                symbol=symbol, qty=qty, side=order_side,
                stop_price=stop_price, limit_price=limit_price, time_in_force=tif
            )
        else:
            raise ValueError(f"Unsupported order type: {order_type}")
        
        order = self.trading_client.submit_order(request)
        
        return {
            'order_id': str(order.id),
            'symbol': order.symbol,
            'side': str(order.side),
            'qty': float(order.qty) if order.qty else 0,
            'order_type': str(order.order_type),
            'status': str(order.status),
            'limit_price': float(order.limit_price) if order.limit_price else None,
            'stop_price': float(order.stop_price) if order.stop_price else None,
        }
    
    def get_stock_quote(self, symbol: str) -> Dict[str, Any]:
        """Get stock quote"""
        request = StockLatestQuoteRequest(symbol_or_symbols=[symbol])
        quotes = self.stock_data_client.get_stock_latest_quote(request)
        
        quote = quotes[symbol]
        return {
            'symbol': symbol,
            'bid': float(quote.bid_price),
            'ask': float(quote.ask_price),
            'bid_size': int(quote.bid_size),
            'ask_size': int(quote.ask_size),
            'last_price': float((quote.bid_price + quote.ask_price) / 2),
            'timestamp': quote.timestamp,
        }
    
    def get_stock_bars(self, symbol: str, timeframe: str, start: datetime,
                       end: Optional[datetime] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get historical bars"""
        # Parse timeframe
        timeframe_map = {
            '1Min': TimeFrame(1, TimeFrameUnit.Minute),
            '5Min': TimeFrame(5, TimeFrameUnit.Minute),
            '15Min': TimeFrame(15, TimeFrameUnit.Minute),
            '1Hour': TimeFrame(1, TimeFrameUnit.Hour),
            '1Day': TimeFrame(1, TimeFrameUnit.Day),
        }
        
        tf = timeframe_map.get(timeframe, TimeFrame(1, TimeFrameUnit.Day))
        
        if not end:
            end = datetime.now()
        
        request = StockBarsRequest(
            symbol_or_symbols=[symbol],
            timeframe=tf,
            start=start,
            end=end,
            limit=limit
        )
        
        bars_data = self.stock_data_client.get_stock_bars(request)
        bars = bars_data[symbol]
        
        result = []
        for bar in bars:
            result.append({
                'timestamp': bar.timestamp.isoformat() if hasattr(bar.timestamp, 'isoformat') else str(bar.timestamp),
                'open': float(bar.open),
                'high': float(bar.high),
                'low': float(bar.low),
                'close': float(bar.close),
                'volume': int(bar.volume),
                'vwap': float(bar.vwap) if hasattr(bar, 'vwap') and bar.vwap else None,
            })
        
        return result
    
    def get_orders(self, status: str = 'all') -> List[Dict[str, Any]]:
        """Get orders"""
        status_map = {
            'open': QueryOrderStatus.OPEN,
            'closed': QueryOrderStatus.CLOSED,
            'all': QueryOrderStatus.ALL,
        }
        
        request = GetOrdersRequest(status=status_map.get(status, QueryOrderStatus.ALL))
        orders = self.trading_client.get_orders(filter=request)
        
        result = []
        for order in orders:
            result.append({
                'order_id': str(order.id),
                'symbol': order.symbol,
                'side': str(order.side),
                'qty': float(order.qty) if order.qty else 0,
                'order_type': str(order.order_type),
                'status': str(order.status),
                'filled_qty': float(order.filled_qty) if order.filled_qty else 0,
                'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price else 0,
                'created_at': order.created_at.isoformat() if hasattr(order.created_at, 'isoformat') else str(order.created_at),
            })
        
        return result
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel specific order"""
        self.trading_client.cancel_order_by_id(order_id)
        return {'status': 'cancelled', 'order_id': order_id}
    
    def cancel_all_orders(self) -> Dict[str, Any]:
        """Cancel all pending orders"""
        cancelled = self.trading_client.cancel_orders()
        return {
            'status': 'success',
            'cancelled_count': len(cancelled),
            'cancelled_orders': [str(o.id) for o in cancelled]
        }
    
    def get_market_status(self) -> Dict[str, Any]:
        """Get market status"""
        clock = self.trading_client.get_clock()
        return {
            'is_open': clock.is_open,
            'next_open': clock.next_open,
            'next_close': clock.next_close,
            'timestamp': clock.timestamp,
        }
    
    # Alpaca-specific capabilities
    
    def supports_options(self) -> bool:
        return True
    
    def supports_crypto_leverage(self) -> bool:
        return False  # Alpaca doesn't support crypto leverage
    
    def supports_short_selling(self) -> bool:
        return True
    
    def get_max_leverage(self, asset_class: str) -> int:
        if asset_class == 'stock':
            return 2  # Margin accounts have 2x leverage
        return 1
    
    def normalize_symbol(self, symbol: str, asset_class: str) -> str:
        """Normalize symbol for Alpaca (BTC/USD format for crypto)"""
        if asset_class == 'crypto':
            # Ensure crypto symbols are in BTC/USD format
            if '/' not in symbol:
                # Convert BTCUSD to BTC/USD
                if symbol.endswith('USD'):
                    base = symbol[:-3]
                    return f"{base}/USD"
                elif symbol.endswith('USDT'):
                    base = symbol[:-4]
                    return f"{base}/USD"
            return symbol
        return symbol
