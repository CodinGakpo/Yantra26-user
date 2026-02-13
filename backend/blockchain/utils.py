"""
Utility functions for blockchain integration
"""

import hashlib
import json
from typing import Dict, Any


def create_event_payload(
    complaint_id: str,
    event_type: str,
    data: Dict[str, Any],
    actor: str = None
) -> Dict:
    """
    Create standardized event payload for blockchain logging.
    
    Args:
        complaint_id: Complaint identifier
        event_type: Event type (CREATED, ASSIGNED, etc.)
        data: Event-specific data
        actor: User who triggered the event
        
    Returns:
        Standardized payload dictionary
    """
    import time
    
    payload = {
        'complaint_id': complaint_id,
        'event_type': event_type,
        'timestamp': int(time.time()),
        'data': data
    }
    
    if actor:
        payload['actor'] = actor
    
    return payload


def validate_complaint_id(complaint_id: str) -> bool:
    """
    Validate complaint ID format.
    
    Args:
        complaint_id: Complaint identifier
        
    Returns:
        True if valid
    """
    if not complaint_id or not isinstance(complaint_id, str):
        return False
    
    if len(complaint_id) > 100:
        return False
    
    return True


def format_blockchain_response(tx_hash: str, status: str, details: Dict = None) -> Dict:
    """
    Format blockchain operation response.
    
    Args:
        tx_hash: Transaction hash
        status: Status (success, pending, failed)
        details: Additional details
        
    Returns:
        Formatted response dictionary
    """
    response = {
        'tx_hash': tx_hash,
        'status': status,
        'explorer_url': get_explorer_url(tx_hash)
    }
    
    if details:
        response['details'] = details
    
    return response


def get_explorer_url(tx_hash: str) -> str:
    """
    Get blockchain explorer URL for transaction.
    
    Args:
        tx_hash: Transaction hash
        
    Returns:
        Explorer URL
    """
    from django.conf import settings
    
    base_url = getattr(settings, 'BLOCKCHAIN_EXPLORER_URL', 'https://etherscan.io')
    return f"{base_url}/tx/{tx_hash}"


def truncate_hash(hash_str: str, prefix_len: int = 10, suffix_len: int = 8) -> str:
    """
    Truncate hash for display purposes.
    
    Args:
        hash_str: Full hash string
        prefix_len: Number of characters to show at start
        suffix_len: Number of characters to show at end
        
    Returns:
        Truncated hash (e.g., "0x12345678...abcdef")
    """
    if len(hash_str) <= prefix_len + suffix_len:
        return hash_str
    
    return f"{hash_str[:prefix_len]}...{hash_str[-suffix_len:]}"


def estimate_gas_cost(gas_used: int, gas_price_gwei: float) -> Dict:
    """
    Estimate transaction cost in ETH and USD.
    
    Args:
        gas_used: Gas units used
        gas_price_gwei: Gas price in Gwei
        
    Returns:
        Dictionary with cost estimates
    """
    gas_price_wei = gas_price_gwei * 1e9
    cost_wei = gas_used * gas_price_wei
    cost_eth = cost_wei / 1e18
    
    # You could fetch ETH price from an API for USD estimate
    eth_price_usd = 3000  # Placeholder
    cost_usd = cost_eth * eth_price_usd
    
    return {
        'gas_used': gas_used,
        'gas_price_gwei': gas_price_gwei,
        'cost_eth': round(cost_eth, 6),
        'cost_usd': round(cost_usd, 2)
    }
