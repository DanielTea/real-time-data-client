"""
Broker factory - creates broker instances based on broker type
"""

from typing import Optional
from .base import BaseBroker
from .alpaca_broker import AlpacaBroker
from .bybit_broker import BybitBroker
from .binance_broker import BinanceBroker


class BrokerFactory:
    """Factory class for creating broker instances"""
    
    SUPPORTED_BROKERS = {
        'alpaca': AlpacaBroker,
        'bybit': BybitBroker,
        'binance': BinanceBroker,
    }
    
    @classmethod
    def create_broker(cls, broker_type: str, api_key: str, api_secret: str, 
                     paper_mode: bool = True) -> BaseBroker:
        """
        Create a broker instance
        
        Args:
            broker_type: Type of broker ('alpaca', 'bybit', 'binance')
            api_key: API key
            api_secret: API secret
            paper_mode: Whether to use paper trading mode
            
        Returns:
            BaseBroker: Broker instance
            
        Raises:
            ValueError: If broker type is not supported
        """
        broker_type = broker_type.lower().strip()
        
        if broker_type not in cls.SUPPORTED_BROKERS:
            supported = ', '.join(cls.SUPPORTED_BROKERS.keys())
            raise ValueError(
                f"Unsupported broker type: {broker_type}. "
                f"Supported brokers: {supported}"
            )
        
        broker_class = cls.SUPPORTED_BROKERS[broker_type]
        return broker_class(api_key=api_key, api_secret=api_secret, paper_mode=paper_mode)
    
    @classmethod
    def get_supported_brokers(cls) -> list:
        """Get list of supported broker types"""
        return list(cls.SUPPORTED_BROKERS.keys())
    
    @classmethod
    def get_broker_info(cls) -> dict:
        """Get information about each supported broker"""
        return {
            'alpaca': {
                'name': 'Alpaca',
                'description': 'US-based broker supporting stocks, crypto, and options',
                'supports_stocks': True,
                'supports_crypto': True,
                'supports_options': True,
                'supports_leverage': True,
                'max_crypto_leverage': 1,
                'max_stock_leverage': 2,
                'paper_trading': True,
                'website': 'https://alpaca.markets',
            },
            'bybit': {
                'name': 'Bybit',
                'description': 'Crypto exchange with perpetual futures and up to 100x leverage',
                'supports_stocks': False,
                'supports_crypto': True,
                'supports_options': False,
                'supports_leverage': True,
                'max_crypto_leverage': 100,
                'max_stock_leverage': 0,
                'paper_trading': True,
                'website': 'https://www.bybit.com',
            },
            'binance': {
                'name': 'Binance',
                'description': 'Largest crypto exchange with spot and futures trading (up to 125x leverage)',
                'supports_stocks': False,
                'supports_crypto': True,
                'supports_options': False,
                'supports_leverage': True,
                'max_crypto_leverage': 125,
                'max_stock_leverage': 0,
                'paper_trading': True,
                'website': 'https://www.binance.com',
            },
        }
