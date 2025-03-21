"""
Futarchy router interface ABI.

This module is in DEVELOPMENT status.
Contains functions needed for splitting and merging conditional tokens.
"""

FUTARCHY_ROUTER_ABI = [
    # splitPosition - to split tokens into conditional tokens
    {
        "inputs": [
            {"name": "market", "type": "address"},
            {"name": "token", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "splitPosition",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    # mergePosition - to merge conditional tokens back
    {
        "inputs": [
            {"name": "market", "type": "address"},
            {"name": "token", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "mergePositions",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
] 