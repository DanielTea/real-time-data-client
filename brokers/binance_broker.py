"""
Binance broker implementation
Supports: Spot, Futures (with leverage), Paper Trading (Testnet)
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import time
import hmac
import hashlib
import requests
from .base import BaseBroker


class BinanceBroker(BaseBroker):
    """Binance broker implementation"""
    
    def __init__(self, api_key: str, api_secret: str, paper_mode: bool = True):
        super().__init__(api_key, api_secret, paper_mode)
        
        # Use testnet for paper trading
        if paper_mode:
            self.base_url = "https://testnet.binancefuture.com"
            self.spot_url = "https://testnet.binance.vision"
        else:
            self.base_url = "https://fapi.binance.com"
            self.spot_url = "https://api.binance.com"
        
        self.recv_window = 5000
    
    def _generate_signature(self, params: str) -> str:
        """Generate HMAC SHA256 signature for Binance API"""
        return hmac.new(
            self.api_secret.encode('utf-8'),
            params.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None,
                     signed: bool = False, use_spot: bool = False) -> Any:
        """Make authenticated request to Binance API"""
        base = self.spot_url if use_spot else self.base_url
        url = f"{base}{endpoint}"
        
        if params is None:
            params = {}
        
        headers = {
            'X-MBX-APIKEY': self.api_key,
        }
        
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['recvWindow'] = self.recv_window
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            params['signature'] = self._generate_signature(query_string)
        
        if method == 'GET':
            response = requests.get(url, params=params, headers=headers)
        elif method == 'POST':
            response = requests.post(url, params=params, headers=headers)
        elif method == 'DELETE':
            response = requests.delete(url, params=params, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    
    def get_broker_name(self) -> str:
        return "Binance"
    
    def get_account(self) -> Dict[str, Any]:
        """Get account information"""
        # Get futures account
        futures_account = self._make_request('GET', '/fapi/v2/account', signed=True)
        
        total_balance = 0
        available_balance = 0
        
        for asset in futures_account.get('assets', []):
            if asset['asset'] == 'USDT':
                total_balance = float(asset.get('walletBalance', 0))
                available_balance = float(asset.get('availableBalance', 0))
                break
        
        return {
            'cash': available_balance,
            'equity': total_balance,
            'buying_power': available_balance,
            'currency': 'USDT',
            'pattern_day_trader': False,
            'daytrade_count': 0,
            'daytrading_buying_power': available_balance,
            'shorting_enabled': True,
            'account_blocked': False,
            'trading_blocked': False,
        }
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """Get all positions"""
        positions_data = self._make_request('GET', '/fapi/v2/positionRisk', signed=True)
        
        positions = []
        for pos in positions_data:
            pos_amt = float(pos.get('positionAmt', 0))
            if pos_amt != 0:
                entry_price = float(pos.get('entryPrice', 0))
                mark_price = float(pos.get('markPrice', 0))
                unrealized_pnl = float(pos.get('unRealizedProfit', 0))
                
                positions.append({
                    'symbol': pos['symbol'],
                    'qty': pos_amt,
                    'avg_entry_price': entry_price,
                    'current_price': mark_price,
                    'market_value': abs(pos_amt * mark_price),
                    'unrealized_pl': unrealized_pnl,
                    'unrealized_pl_percent': (unrealized_pnl / (abs(pos_amt) * entry_price) * 100) if entry_price else 0,
                    'side': 'long' if pos_amt > 0 else 'short',
                    'asset_class': 'crypto_futures',
                    'exchange': 'binance',
                    'leverage': int(pos.get('leverage', 1)),
                })
        
        return positions
    
    def close_position(self, symbol: str, qty: Optional[float] = None,
                       percentage: Optional[float] = None) -> Dict[str, Any]:
        """Close a position"""
        # Get current position
        positions = self.get_positions()
        position = next((p for p in positions if p['symbol'] == symbol), None)
        
        if not position:
            raise ValueError(f"No position found for {symbol}")
        
        current_qty = abs(position['qty'])
        side = position['side']
        
        # Calculate quantity to close
        if percentage:
            close_qty = current_qty * (percentage / 100)
        elif qty:
            close_qty = min(qty, current_qty)
        else:
            close_qty = current_qty
        
        # Close position by placing opposite order
        close_side = 'SELL' if side == 'long' else 'BUY'
        
        params = {
            'symbol': symbol,
            'side': close_side,
            'type': 'MARKET',
            'quantity': close_qty,
            'reduceOnly': 'true'
        }
        
        result = self._make_request('POST', '/fapi/v1/order', params, signed=True)
        
        return {
            'order_id': str(result.get('orderId')),
            'symbol': symbol,
            'status': result.get('status'),
            'side': close_side,
            'qty': close_qty,
        }
    
    def get_crypto_price(self, symbol: str) -> Dict[str, Any]:
        """Get latest crypto price"""
        symbol = self.normalize_symbol(symbol, 'crypto')
        
        ticker = self._make_request('GET', '/fapi/v1/ticker/24hr', {'symbol': symbol})
        
        return {
            'symbol': symbol,
            'price': float(ticker.get('lastPrice', 0)),
            'timestamp': datetime.fromtimestamp(int(ticker.get('closeTime', 0)) / 1000),
            'open': float(ticker.get('openPrice', 0)),
            'high': float(ticker.get('highPrice', 0)),
            'low': float(ticker.get('lowPrice', 0)),
            'volume': float(ticker.get('volume', 0)),
        }
    
    def place_crypto_order(self, symbol: str, side: str, qty: Optional[float] = None,
                          notional: Optional[float] = None, leverage: Optional[int] = None) -> Dict[str, Any]:
        """Place crypto order (futures with optional leverage)"""
        symbol = self.normalize_symbol(symbol, 'crypto')
        
        # Set leverage if provided
        if leverage and leverage > 1:
            self._make_request('POST', '/fapi/v1/leverage', {
                'symbol': symbol,
                'leverage': leverage
            }, signed=True)
        
        # If notional is provided, calculate quantity
        if notional and not qty:
            price_data = self.get_crypto_price(symbol)
            qty = notional / price_data['price']
        
        params = {
            'symbol': symbol,
            'side': 'BUY' if side.lower() == 'buy' else 'SELL',
            'type': 'MARKET',
            'quantity': qty,
        }
        
        result = self._make_request('POST', '/fapi/v1/order', params, signed=True)
        
        return {
            'order_id': str(result.get('orderId')),
            'symbol': symbol,
            'side': side,
            'qty': float(result.get('origQty', 0)),
            'notional': notional or 0,
            'status': result.get('status'),
            'filled_avg_price': float(result.get('avgPrice', 0)),
            'leverage': leverage or 1,
        }
    
    def place_stock_order(self, symbol: str, side: str, qty: Optional[float] = None,
                         notional: Optional[float] = None, order_type: str = 'market',
                         limit_price: Optional[float] = None, stop_price: Optional[float] = None,
                         time_in_force: str = 'day') -> Dict[str, Any]:
        """Binance doesn't support stocks - raise error"""
        raise NotImplementedError("Binance does not support stock trading. Please use crypto symbols.")
    
    def get_stock_quote(self, symbol: str) -> Dict[str, Any]:
        """Binance doesn't support stocks"""
        raise NotImplementedError("Binance does not support stock trading")
    
    def get_stock_bars(self, symbol: str, timeframe: str, start: datetime,
                       end: Optional[datetime] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get historical bars (crypto only for Binance)"""
        symbol = self.normalize_symbol(symbol, 'crypto')
        
        # Map timeframe
        interval_map = {
            '1Min': '1m',
            '5Min': '5m',
            '15Min': '15m',
            '1Hour': '1h',
            '1Day': '1d',
        }
        
        interval = interval_map.get(timeframe, '1d')
        
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit,
            'startTime': int(start.timestamp() * 1000)
        }
        
        if end:
            params['endTime'] = int(end.timestamp() * 1000)
        
        klines = self._make_request('GET', '/fapi/v1/klines', params)
        
        bars = []
        for kline in klines:
            bars.append({
                'timestamp': datetime.fromtimestamp(int(kline[0]) / 1000),
                'open': float(kline[1]),
                'high': float(kline[2]),
                'low': float(kline[3]),
                'close': float(kline[4]),
                'volume': int(float(kline[5])),
                'vwap': None,
            })
        
        return bars
    
    def get_orders(self, status: str = 'all') -> List[Dict[str, Any]]:
        """Get orders"""
        if status == 'open':
            result = self._make_request('GET', '/fapi/v1/openOrders', signed=True)
        else:
            result = self._make_request('GET', '/fapi/v1/allOrders', {'limit': 500}, signed=True)
        
        orders = []
        for order in result:
            orders.append({
                'order_id': str(order.get('orderId')),
                'symbol': order.get('symbol'),
                'side': order.get('side'),
                'qty': float(order.get('origQty', 0)),
                'order_type': order.get('type'),
                'status': order.get('status'),
                'filled_qty': float(order.get('executedQty', 0)),
                'filled_avg_price': float(order.get('avgPrice', 0)),
                'created_at': datetime.fromtimestamp(int(order.get('time', 0)) / 1000),
            })
        
        return orders
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel specific order"""
        params = {'orderId': order_id}
        self._make_request('DELETE', '/fapi/v1/order', params, signed=True)
        return {'status': 'cancelled', 'order_id': order_id}
    
    def cancel_all_orders(self) -> Dict[str, Any]:
        """Cancel all pending orders"""
        result = self._make_request('DELETE', '/fapi/v1/allOpenOrders', signed=True)
        return {
            'status': 'success',
            'cancelled_count': result.get('code', 0),
            'message': result.get('msg', 'All orders cancelled')
        }
    
    def get_market_status(self) -> Dict[str, Any]:
        """Get market status - crypto markets are always open"""
        return {
            'is_open': True,  # Crypto markets are 24/7
            'next_open': datetime.now(),
            'next_close': datetime.now() + timedelta(days=365),
            'timestamp': datetime.now(),
        }
    
    # Binance-specific capabilities
    
    def supports_options(self) -> bool:
        return False  # Binance focuses on spot and futures
    
    def supports_crypto_leverage(self) -> bool:
        return True  # Up to 125x leverage on futures
    
    def supports_short_selling(self) -> bool:
        return True
    
    def get_max_leverage(self, asset_class: str) -> int:
        if asset_class in ['crypto', 'crypto_futures']:
            return 125  # Binance offers up to 125x leverage
        return 1
    
    def normalize_symbol(self, symbol: str, asset_class: str) -> str:
        """Normalize symbol for Binance (BTCUSDT format)"""
        if asset_class in ['crypto', 'crypto_futures']:
            # Remove slashes and ensure USDT suffix
            symbol = symbol.replace('/', '').replace('-', '').upper()
            if not symbol.endswith('USDT'):
                if symbol.endswith('USD'):
                    symbol = symbol[:-3] + 'USDT'
                else:
                    symbol = symbol + 'USDT'
            return symbol
        return symbol
