"""
Configuration package for the Futarchy Trading Bot.

This module is currently in EXPERIMENTAL status.
Please use with caution as functionality may change.
"""

from futarchy.experimental.config.network import (
    DEFAULT_RPC_URLS,
    COWSWAP_API_URL
)

from futarchy.experimental.config.contracts import (
    CONTRACT_ADDRESSES,
    CONTRACT_WARNINGS,
    is_contract_safe,
    get_contract_warning
)

from futarchy.experimental.config.pools import (
    POOL_CONFIG_YES,
    POOL_CONFIG_NO,
    BALANCER_CONFIG,
    MIN_SQRT_RATIO,
    MAX_SQRT_RATIO,
    UNISWAP_V3_CONFIG
)

from futarchy.experimental.config.tokens import (
    TOKEN_CONFIG,
    DEFAULT_SWAP_CONFIG,
    DEFAULT_PERMIT_CONFIG,
    get_token_info,
    get_token_decimals,
    format_token_amount,
    get_base_token
)

__all__ = [
    # Network
    'DEFAULT_RPC_URLS',
    'COWSWAP_API_URL',
    
    # Contracts
    'CONTRACT_ADDRESSES',
    'CONTRACT_WARNINGS',
    'is_contract_safe',
    'get_contract_warning',
    
    # Pools
    'POOL_CONFIG_YES',
    'POOL_CONFIG_NO',
    'BALANCER_CONFIG',
    'MIN_SQRT_RATIO',
    'MAX_SQRT_RATIO',
    'UNISWAP_V3_CONFIG',
    
    # Tokens
    'TOKEN_CONFIG',
    'DEFAULT_SWAP_CONFIG',
    'DEFAULT_PERMIT_CONFIG',
    'get_token_info',
    'get_token_decimals',
    'format_token_amount',
    'get_base_token'
]
