"""
Contract addresses for the Futarchy Trading Bot.

This module is in DEVELOPMENT status.
Contains only the contract addresses needed for conditional token operations.
"""

from web3 import Web3

# Contract addresses on Gnosis Chain
CONTRACTS = {
    "CONDITIONAL_TOKEN": Web3.to_checksum_address("0xCeAfDD6bc0bEF976fdCd1112955828E00543c0Ce"),  # Futarchy market
    "FUTARCHY_ROUTER": Web3.to_checksum_address("0x7495a583ba85875d59407781b4958ED6e0E1228f"),  # Router for splitting/merging
    "MARKET": Web3.to_checksum_address("0x6242AbA055957A63d682e9D3de3364ACB53D053A")  # Market address
} 