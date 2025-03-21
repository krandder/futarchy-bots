"""
Constants for development scripts.
Simplified version containing only what's needed for GNO wrapping/unwrapping.
"""

# Token Addresses on Gnosis Chain
GNO_ADDRESS = "0x9C58BAcC331c9aa871AFD802DB6379a98e80CEdb"
WAGNO_ADDRESS = "0x7c16F0185A26Db0AE7a9377f23BC18ea7ce5d644"

# ABIs
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]

WAGNO_ABI = ERC20_ABI + [
    {
        "inputs": [
            {"name": "assets", "type": "uint256"},
            {"name": "receiver", "type": "address"},
            {"name": "owner", "type": "address"}
        ],
        "name": "redeem",
        "outputs": [{"name": "shares", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "assets", "type": "uint256"},
            {"name": "receiver", "type": "address"}
        ],
        "name": "deposit",
        "outputs": [{"name": "shares", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    }
] 