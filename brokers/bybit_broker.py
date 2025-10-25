"""
Bybit broker implementation
Supports: Spot, Perpetual Futures (with leverage), Paper Trading (Testnet)
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import time
import hmac
import hashlib
import requests
from .base import BaseBroker


class BybitBroker(BaseBroker):
    """Bybit broker implementation"""
    
    def __init__(self, api_key: str, api_secret: str, paper_mode: bool = True):
        super().__init__(api_key, api_secret, paper_mode)
        
        # Use testnet for paper trading
        if paper_mode:
            self.base_url = "https://api-testnet.bybit.com"
        else:
            self.base_url = "https://api.bybit.com"
        
        self.recv_window = 5000
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """Generate HMAC SHA256 signature for Bybit API"""
        param_str = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        return hmac.new(
            self.api_secret.encode('utf-8'),
            param_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                     signed: bool = False) -> Dict[str, Any]:
        """Make authenticated request to Bybit API"""
        url = f"{self.base_url}{endpoint}"
        
        if params is None:
            params = {}
        
        if signed:
            timestamp = int(time.time() * 1000)
            params['api_key'] = self.api_key
            params['timestamp'] = timestamp
            params['recv_window'] = self.recv_window
            params['sign'] = self._generate_signature(params)
        
        headers = {
            'Content-Type': 'application/json',
        }
        
        if method == 'GET':
            response = requests.get(url, params=params, headers=headers)
        else:
            response = requests.post(url, json=params, headers=headers)
        
        response.raise_for_status()
        data = response.json()
        
        if data.get('ret_code') != 0 and data.get('retCode') != 0:
            raise Exception(f"Bybit API error: {data.get('ret_msg') or data.get('retMsg')}")
        
        return data.get('result', {})
    
    def get_broker_name(self) -> str:
        return "Bybit"
    
    def get_account(self) -> Dict[str, Any]:
        """Get account information"""
        # Get wallet balance (for futures/derivatives)
        wallet = self._make_request('GET', '/v2/private/wallet/balance', signed=True)
        
        # Get spot balance
        spot = self._make_request('GET', '/spot/v3/private/account', signed=True)
        
        # Combine balances
        total_equity = 0
        total_available = 0
        
        # Add USDT balance from futures wallet
        if 'USDT' in wallet:
            total_equity += float(wallet['USDT'].get('equity', 0))
            total_available += float(wallet['USDT'].get('available_balance', 0))
        
        # Add spot balances
        for balance in spot.get('balances', []):
            if balance['coin'] == 'USDT':
                total_available += float(balance.get('free', 0))
                total_equity += float(balance.get('free', 0)) + float(balance.get('locked', 0))
        
        return {
            'cash': total_available,
            'equity': total_equity,
            'buying_power': total_available,  # Bybit doesn't have separate buying power concept
            'currency': 'USDT',
            'pattern_day_trader': False,  # Crypto doesn't have PDT rules
            'daytrade_count': 0,
            'daytrading_buying_power': total_available,
            'shorting_enabled': True,
            'account_blocked': False,
            'trading_blocked': False,
        }
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """Get all positions"""
        positions = []
        
        # Get futures positions
        futures_pos = self._make_request('GET', '/v2/private/position/list', signed=True)
        
        for pos in futures_pos:
            if float(pos.get('size', 0)) > 0:
                side = 'long' if pos.get('side') == 'Buy' else 'short'
                qty = float(pos.get('size', 0))
                
                positions.append({
                    'symbol': pos['symbol'],
                    'qty': qty if side == 'long' else -qty,
                    'avg_entry_price': float(pos.get('entry_price', 0)),
                    'current_price': float(pos.get('liq_price', 0)),
                    'market_value': float(pos.get('position_value', 0)),
                    'unrealized_pl': float(pos.get('unrealised_pnl', 0)),
                    'unrealized_pl_percent': (float(pos.get('unrealised_pnl', 0)) / 
                                             float(pos.get('position_value', 1))) * 100,
                    'side': side,
                    'asset_class': 'crypto_futures',
                    'exchange': 'bybit',
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
        close_side = 'Sell' if side == 'long' else 'Buy'
        
        params = {
            'symbol': symbol,
            'side': close_side,
            'order_type': 'Market',
            'qty': close_qty,
            'time_in_force': 'GoodTillCancel',
            'reduce_only': True,
            'close_on_trigger': False
        }
        
        result = self._make_request('POST', '/v2/private/order/create', params, signed=True)
        
        return {
            'order_id': result.get('order_id'),
            'symbol': symbol,
            'status': 'submitted',
            'side': close_side,
            'qty': close_qty,
        }
    
    def get_crypto_price(self, symbol: str) -> Dict[str, Any]:
        """Get latest crypto price"""
        symbol = self.normalize_symbol(symbol, 'crypto')
        
        result = self._make_request('GET', '/v2/public/tickers', {'symbol': symbol})
        
        ticker = result[0] if isinstance(result, list) else result
        
        return {
            'symbol': symbol,
            'price': float(ticker.get('last_price', 0)),
            'timestamp': datetime.fromtimestamp(int(ticker.get('time', 0)) / 1000).isoformat(),
            'open': float(ticker.get('open_value', 0)),
            'high': float(ticker.get('high_price_24h', 0)),
            'low': float(ticker.get('low_price_24h', 0)),
            'volume': float(ticker.get('volume_24h', 0)),
        }
    
    def place_crypto_order(self, symbol: str, side: str, qty: Optional[float] = None,
                          notional: Optional[float] = None, leverage: Optional[int] = None) -> Dict[str, Any]:
        """Place crypto order (futures with optional leverage)"""
        symbol = self.normalize_symbol(symbol, 'crypto')
        
        # Set leverage if provided
        if leverage and leverage > 1:
            self._make_request('POST', '/v2/private/position/leverage/save', {
                'symbol': symbol,
                'leverage': leverage
            }, signed=True)
        
        # If notional is provided, get current price and calculate qty
        if notional and not qty:
            price_data = self.get_crypto_price(symbol)
            qty = notional / price_data['price']
        
        params = {
            'symbol': symbol,
            'side': 'Buy' if side.lower() == 'buy' else 'Sell',
            'order_type': 'Market',
            'qty': qty,
            'time_in_force': 'GoodTillCancel',
            'reduce_only': False,
            'close_on_trigger': False
        }
        
        result = self._make_request('POST', '/v2/private/order/create', params, signed=True)
        
        return {
            'order_id': result.get('order_id'),
            'symbol': symbol,
            'side': side,
            'qty': qty,
            'notional': notional or 0,
            'status': 'submitted',
            'filled_avg_price': 0,
            'leverage': leverage or 1,
        }
    
    def place_stock_order(self, symbol: str, side: str, qty: Optional[float] = None,
                         notional: Optional[float] = None, order_type: str = 'market',
                         limit_price: Optional[float] = None, stop_price: Optional[float] = None,
                         time_in_force: str = 'day') -> Dict[str, Any]:
        """Bybit doesn't support stocks - raise error"""
        raise NotImplementedError("Bybit does not support stock trading. Please use crypto symbols.")
    
    def get_stock_quote(self, symbol: str) -> Dict[str, Any]:
        """Bybit doesn't support stocks"""
        raise NotImplementedError("Bybit does not support stock trading")
    
    def get_stock_bars(self, symbol: str, timeframe: str, start: datetime,
                       end: Optional[datetime] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get historical bars (crypto only for Bybit)"""
        symbol = self.normalize_symbol(symbol, 'crypto')
        
        # Map timeframe
        interval_map = {
            '1Min': '1',
            '5Min': '5',
            '15Min': '15',
            '1Hour': '60',
            '1Day': 'D',
        }
        
        interval = interval_map.get(timeframe, 'D')
        
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit,
            'from': int(start.timestamp())
        }
        
        result = self._make_request('GET', '/v2/public/kline/list', params)
        
        bars = []
        for bar in result:
            bars.append({
                'timestamp': datetime.fromtimestamp(int(bar.get('open_time', 0))).isoformat(),
                'open': float(bar.get('open', 0)),
                'high': float(bar.get('high', 0)),
                'low': float(bar.get('low', 0)),
                'close': float(bar.get('close', 0)),
                'volume': int(bar.get('volume', 0)),
                'vwap': None,
            })
        
        return bars
    
    def get_orders(self, status: str = 'all') -> List[Dict[str, Any]]:
        """Get orders"""
        params = {}
        
        if status == 'open':
            endpoint = '/v2/private/order'
        else:
            endpoint = '/v2/private/order/list'
        
        result = self._make_request('GET', endpoint, params, signed=True)
        
        orders = []
        data = result.get('data', []) if isinstance(result.get('data'), list) else [result]
        
        for order in data:
            orders.append({
                'order_id': order.get('order_id'),
                'symbol': order.get('symbol'),
                'side': order.get('side'),
                'qty': float(order.get('qty', 0)),
                'order_type': order.get('order_type'),
                'status': order.get('order_status'),
                'filled_qty': float(order.get('cum_exec_qty', 0)),
                'filled_avg_price': float(order.get('price', 0)),
                'created_at': datetime.fromtimestamp(int(order.get('created_time', 0)) / 1000).isoformat(),
            })
        
        return orders
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel specific order"""
        params = {'order_id': order_id}
        self._make_request('POST', '/v2/private/order/cancel', params, signed=True)
        return {'status': 'cancelled', 'order_id': order_id}
    
    def cancel_all_orders(self) -> Dict[str, Any]:
        """Cancel all pending orders"""
        result = self._make_request('POST', '/v2/private/order/cancelAll', signed=True)
        return {
            'status': 'success',
            'cancelled_count': len(result),
            'cancelled_orders': [o.get('order_id') for o in result]
        }
    
    def get_market_status(self) -> Dict[str, Any]:
        """Get market status - crypto markets are always open"""
        now = datetime.now()
        return {
            'is_open': True,  # Crypto markets are 24/7
            'next_open': now.isoformat(),
            'next_close': (now + timedelta(days=365)).isoformat(),
            'timestamp': now.isoformat(),
        }
    
    # Bybit-specific capabilities
    
    def supports_options(self) -> bool:
        return False  # Bybit focuses on futures
    
    def supports_crypto_leverage(self) -> bool:
        return True  # Up to 100x leverage on perpetual futures
    
    def supports_short_selling(self) -> bool:
        return True
    
    def get_max_leverage(self, asset_class: str) -> int:
        if asset_class in ['crypto', 'crypto_futures']:
            return 100  # Bybit offers up to 100x leverage
        return 1
    
    def normalize_symbol(self, symbol: str, asset_class: str) -> str:
        """Normalize symbol for Bybit (BTCUSDT format for futures)"""
        if asset_class in ['crypto', 'crypto_futures']:
            # Remove slashes and ensure USDT suffix
            symbol = symbol.replace('/', '').replace('-', '')
            if not symbol.endswith('USDT') and not symbol.endswith('USD'):
                symbol = symbol + 'USDT'
            # For futures, might need to add USDT
            if symbol.endswith('USD') and not symbol.endswith('USDT'):
                symbol = symbol[:-3] + 'USDT'
            return symbol
        return symbol
