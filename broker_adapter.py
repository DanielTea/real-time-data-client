"""
Broker adapter module - integrates broker abstraction with trading server
This module adapts the broker interface to work with the existing tool infrastructure
"""

import sys
import os

# Add brokers directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brokers'))

from brokers.factory import BrokerFactory
from brokers.base import BaseBroker
from typing import Optional, Dict, Any

# Global broker instance
current_broker: Optional[BaseBroker] = None


def initialize_broker(broker_type: str, api_key: str, api_secret: str, paper_mode: bool = True) -> BaseBroker:
    """
    Initialize broker instance
    
    Args:
        broker_type: Type of broker ('alpaca', 'bybit', 'binance')
        api_key: API key
        api_secret: API secret
        paper_mode: Whether to use paper trading
        
    Returns:
        BaseBroker instance
    """
    global current_broker
    current_broker = BrokerFactory.create_broker(
        broker_type=broker_type,
        api_key=api_key,
        api_secret=api_secret,
        paper_mode=paper_mode
    )
    return current_broker


def get_current_broker() -> Optional[BaseBroker]:
    """Get the current broker instance"""
    return current_broker


def get_broker_info() -> Dict[str, Any]:
    """Get information about all supported brokers"""
    return BrokerFactory.get_broker_info()


def get_supported_brokers() -> list:
    """Get list of supported broker types"""
    return BrokerFactory.get_supported_brokers()
