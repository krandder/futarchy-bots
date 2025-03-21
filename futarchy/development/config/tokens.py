"""
Token configurations for the Futarchy Trading Bot.

This module is in DEVELOPMENT status.
Contains only the token configurations needed for conditional token operations.
"""

from typing import Dict, Any
from decimal import Decimal
from web3 import Web3

# Token configurations
TOKEN_CONFIG = {
    "currency": {
        "name": "SDAI",
        "address": Web3.to_checksum_address("0xaf204776c7245bF4147c2612BF6e5972Ee483701"),
        "decimals": 18,
        "yes_address": Web3.to_checksum_address("0x493A0D1c776f8797297Aa8B34594fBd0A7F8968a"),
        "no_address": Web3.to_checksum_address("0xE1133Ef862f3441880adADC2096AB67c63f6E102")
    },
    "company": {
        "name": "GNO",
        "address": Web3.to_checksum_address("0x9C58BAcC331c9aa871AFD802DB6379a98e80CEdb"),
        "decimals": 18,
        "yes_address": Web3.to_checksum_address("0x177304d505eCA60E1aE0dAF1bba4A4c4181dB8Ad"),
        "no_address": Web3.to_checksum_address("0xf1B3E5Ffc0219A4F8C0ac69EC98C97709EdfB6c9")
    }
}

def get_token_info(token_address: str) -> dict:
    """Get token information for a specific token address."""
    # Check main tokens
    for token_type, info in TOKEN_CONFIG.items():
        if info["address"].lower() == token_address.lower():
            return {**info, "type": token_type}
        
        # Check conditional tokens if they exist
        if "yes_address" in info and info["yes_address"].lower() == token_address.lower():
            return {**info, "type": f"{token_type}_yes"}
        if "no_address" in info and info["no_address"].lower() == token_address.lower():
            return {**info, "type": f"{token_type}_no"}
    
    return None

def get_token_decimals(token_address: str) -> int:
    """Get the number of decimals for a specific token address."""
    token_info = get_token_info(token_address)
    return token_info["decimals"] if token_info else 18  # Default to 18 decimals

def format_token_amount(amount: int, token_address: str) -> float:
    """Format a token amount from wei to its decimal representation."""
    decimals = get_token_decimals(token_address)
    return amount / (10 ** decimals)

def get_base_token(conditional_token_address: str) -> str:
    """Get the base token address for a conditional token."""
    for token_type, info in TOKEN_CONFIG.items():
        if "yes_address" in info and info["yes_address"].lower() == conditional_token_address.lower():
            return info["address"]
        if "no_address" in info and info["no_address"].lower() == conditional_token_address.lower():
            return info["address"]
    return None 