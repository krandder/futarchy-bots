"""
Constants for the price impact calculator.
"""

# ABIs
ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": False, "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "payable": False, "stateMutability": "nonpayable", "type": "function"},
    {"constant": True, "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "payable": False, "stateMutability": "view", "type": "function"}
]

# Extended ERC20 ABI with decimals function
EXTENDED_ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": False, "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "payable": False, "stateMutability": "nonpayable", "type": "function"},
    {"constant": True, "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "payable": False, "stateMutability": "view", "type": "function"}
]

# ERC4626 ABI (for waGNO)
ERC4626_ABI = [
    {"inputs": [{"internalType": "uint256", "name": "assets", "type": "uint256"}, {"internalType": "address", "name": "receiver", "type": "address"}], "name": "deposit", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"internalType": "address", "name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "shares", "type": "uint256"}, {"internalType": "address", "name": "receiver", "type": "address"}, {"internalType": "address", "name": "owner", "type": "address"}], "name": "redeem", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "shares", "type": "uint256"}], "name": "convertToAssets", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "assets", "type": "uint256"}], "name": "convertToShares", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "decimals", "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}], "stateMutability": "view", "type": "function"}
]

# Uniswap V3 Pool ABI
UNISWAP_V3_POOL_ABI = [
    {"inputs": [], "name": "slot0", "outputs": [{"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"}, {"internalType": "int24", "name": "tick", "type": "int24"}, {"internalType": "uint16", "name": "observationIndex", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"}, {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"}, {"internalType": "bool", "name": "unlocked", "type": "bool"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "token0", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "token1", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"}
]

# Uniswap V3 Quoter ABI
UNISWAP_V3_QUOTER_ABI = [
    {"inputs":[{"internalType":"bytes","name":"path","type":"bytes"},{"internalType":"uint256","name":"amountIn","type":"uint256"}],"name":"quoteExactInput","outputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256[]","name":"sqrtPriceX96AfterList","type":"uint256[]"},{"internalType":"uint32[]","name":"initializedTicksCrossedList","type":"uint32[]"},{"internalType":"uint256","name":"gasEstimate","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"address","name":"tokenIn","type":"address"},{"internalType":"address","name":"tokenOut","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint160","name":"sqrtPriceLimitX96","type":"uint160"}],"name":"quoteExactInputSingle","outputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint160","name":"sqrtPriceX96After","type":"uint160"},{"internalType":"uint32","name":"initializedTicksCrossed","type":"uint32"},{"internalType":"uint256","name":"gasEstimate","type":"uint256"}],"stateMutability":"nonpayable","type":"function"}
]

# SushiSwap Quoter address (same interface as Uniswap V3 Quoter)
SUSHISWAP_QUOTER_ADDRESS = "0xb1E835Dc2785b52265711e17fCCb0fd018226a6e"  # SushiSwap Quoter on Gnosis Chain

# Import from existing config
try:
    from config.constants import (
        BALANCER_CONFIG, 
        TOKEN_CONFIG, 
        CONTRACT_ADDRESSES, 
        POOL_CONFIG_YES, 
        POOL_CONFIG_NO
    )
except ImportError:
    # Default values if import fails
    BALANCER_CONFIG = {
        "vault_address": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        "pool_address": "0x388cae2f7d3704c937313d990298ba67d70a3709"
    }
    
    TOKEN_CONFIG = {
        "currency": {
            "address": "0xaf204776c7245bf4147c2612bf6e5972ee483701",
            "yes_address": "0x5364dc963cf0a9297aba7d5fd52e42b6f6b1b494",
            "no_address": "0x8ed9f5c8ce39fa9c962b1747e5bc984e50a3c30e"
        },
        "company": {
            "address": "0x9c58bacc331c9aa871afd802db6379a98e80cedb",
            "yes_address": "0x8b9d9a91fe3a98b1e212e194536925720d4e1d2b",
            "no_address": "0x57684d12718a1980e39bf71afc2e7f8cc2a9f789"
        },
        "wagno": {
            "address": "0x5D069c48d9ECB37d65f35f6C0F2C8F8b1615b25C"
        }
    }
    
    CONTRACT_ADDRESSES = {
        "batchRouter": "0xba1ba1ba1ba1ba1ba1ba1ba1ba1ba1ba1ba1ba1b"
    }
    
    POOL_CONFIG_YES = {
        "address": "0x5364dc963cf0a9297aba7d5fd52e42b6f6b1b494"
    }
    
    POOL_CONFIG_NO = {
        "address": "0x8ed9f5c8ce39fa9c962b1747e5bc984e50a3c30e"
    } 