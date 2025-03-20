#!/usr/bin/env python3
"""
Diagnose the sDAI-YES/sDAI pool 

This script examines the current state of the pool and tries to fetch initialized ticks.
"""

import os
import sys
import json
from web3 import Web3
from web3.middleware import geth_poa_middleware
from dotenv import load_dotenv
from config.constants import CONTRACT_ADDRESSES, TOKEN_CONFIG

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.futarchy_bot import FutarchyBot

# Load environment variables
load_dotenv()

# Complete Uniswap V3 Pool ABI with additional functions
COMPLETE_UNISWAP_V3_POOL_ABI = [
    {"inputs": [], "name": "token0", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "token1", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "slot0", "outputs": [{"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"}, {"internalType": "int24", "name": "tick", "type": "int24"}, {"internalType": "uint16", "name": "observationIndex", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"}, {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"}, {"internalType": "bool", "name": "unlocked", "type": "bool"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "fee", "outputs": [{"internalType": "uint24", "name": "", "type": "uint24"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "liquidity", "outputs": [{"internalType": "uint128", "name": "", "type": "uint128"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "tickSpacing", "outputs": [{"internalType": "int24", "name": "", "type": "int24"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "int24", "name": "tick", "type": "int24"}], "name": "ticks", "outputs": [{"internalType": "uint128", "name": "liquidityGross", "type": "uint128"}, {"internalType": "int128", "name": "liquidityNet", "type": "int128"}, {"internalType": "uint256", "name": "feeGrowthOutside0X128", "type": "uint256"}, {"internalType": "uint256", "name": "feeGrowthOutside1X128", "type": "uint256"}, {"internalType": "int56", "name": "tickCumulativeOutside", "type": "int56"}, {"internalType": "uint160", "name": "secondsPerLiquidityOutsideX128", "type": "uint160"}, {"internalType": "uint32", "name": "secondsOutside", "type": "uint32"}, {"internalType": "bool", "name": "initialized", "type": "bool"}], "stateMutability": "view", "type": "function"}
]

# Full ERC20 ABI including symbol() function
ERC20_FULL_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

def main():
    """Main diagnostic function."""
    # Initialize the bot
    bot = FutarchyBot(verbose=True)
    w3 = bot.w3
    
    # Get the sDAI-YES/sDAI pool address
    pool_address = CONTRACT_ADDRESSES["sdaiYesPool"]
    
    # Get pool contract with complete ABI
    pool_contract = w3.eth.contract(address=pool_address, abi=COMPLETE_UNISWAP_V3_POOL_ABI)
    
    # Get token addresses
    token0_address = pool_contract.functions.token0().call()
    token1_address = pool_contract.functions.token1().call()
    
    # Get SDAI and SDAI-YES addresses
    sdai_address = TOKEN_CONFIG["currency"]["address"]
    sdai_yes_address = TOKEN_CONFIG["currency"]["yes_address"]
    
    # Set token symbols manually for known tokens
    token0_symbol = "Unknown"
    token1_symbol = "Unknown"
    
    if token0_address.lower() == sdai_address.lower():
        token0_symbol = "sDAI"
    elif token0_address.lower() == sdai_yes_address.lower():
        token0_symbol = "sDAI-YES"
        
    if token1_address.lower() == sdai_address.lower():
        token1_symbol = "sDAI"
    elif token1_address.lower() == sdai_yes_address.lower():
        token1_symbol = "sDAI-YES"
    
    # Try to get token decimals (fallback to 18 if not available)
    token0_decimals = 18
    token1_decimals = 18
    
    try:
        token0_contract = w3.eth.contract(address=token0_address, abi=ERC20_FULL_ABI)
        token0_decimals = token0_contract.functions.decimals().call()
    except Exception as e:
        print(f"Could not get token0 decimals, using default of 18. Error: {e}")
    
    try:
        token1_contract = w3.eth.contract(address=token1_address, abi=ERC20_FULL_ABI)
        token1_decimals = token1_contract.functions.decimals().call()
    except Exception as e:
        print(f"Could not get token1 decimals, using default of 18. Error: {e}")
    
    # Get current pool state
    slot0 = pool_contract.functions.slot0().call()
    
    sqrt_price_x96 = slot0[0]
    current_tick = slot0[1]
    
    # Convert sqrtPriceX96 to price
    price = (sqrt_price_x96 / (2**96))**2
    
    # Get fee
    try:
        fee = pool_contract.functions.fee().call()
    except Exception as e:
        print(f"Could not get fee, using default of 3000 (0.3%). Error: {e}")
        fee = 3000
    
    # Get liquidity
    try:
        liquidity = pool_contract.functions.liquidity().call()
    except Exception as e:
        print(f"Could not get liquidity. Error: {e}")
        liquidity = "Unknown"
    
    # Get tick spacing
    try:
        tick_spacing = pool_contract.functions.tickSpacing().call()
    except Exception as e:
        print(f"Could not get tick spacing, using default of 60. Error: {e}")
        tick_spacing = 60
    
    print("====================== POOL DIAGNOSTIC ======================")
    print(f"Pool Address: {pool_address}")
    print(f"Token0: {token0_symbol} ({token0_address})")
    print(f"Token1: {token1_symbol} ({token1_address})")
    print(f"Fee: {fee / 10000}%")
    print(f"Tick Spacing: {tick_spacing}")
    print("\nPool State:")
    print(f"Current Price: {price:.6f} {token1_symbol} per {token0_symbol}")
    print(f"Current Tick: {current_tick}")
    print(f"Liquidity: {liquidity}")
    
    print("\nExamining initialized ticks (this may take a moment)...")
    
    # Try to check if ticks method is available
    try:
        # We'll try to access ticks around the current tick
        ticks_to_check = [
            current_tick - 180,
            current_tick - 120,
            current_tick - 60,
            current_tick,
            current_tick + 60,
            current_tick + 120,
            current_tick + 180
        ]
        
        # Also check some common tick boundaries 
        common_ticks = [-240, -180, -120, -60, 0, 60, 120, 180, 240]
        for tick in common_ticks:
            if tick not in ticks_to_check:
                ticks_to_check.append(tick)
        
        # Make sure ticks are multiples of tick spacing
        spaced_ticks = []
        for tick in ticks_to_check:
            nearest_tick = tick - (tick % tick_spacing)
            if nearest_tick not in spaced_ticks:
                spaced_ticks.append(nearest_tick)
        
        initialized_ticks = []
        
        for tick in sorted(spaced_ticks):
            try:
                # Try to get tick info - this will fail if tick is not initialized
                tick_info = pool_contract.functions.ticks(tick).call()
                initialized_ticks.append({
                    "tick": tick,
                    "liquidity_gross": tick_info[0],
                    "liquidity_net": tick_info[1],
                    "initialized": tick_info[7]
                })
                print(f"Tick {tick} is initialized with gross liquidity: {tick_info[0]}")
            except Exception as e:
                print(f"Tick {tick} is not initialized or accessible. Error: {e}")
        
        print("\nInitialized Ticks Summary:")
        if initialized_ticks:
            for tick_info in initialized_ticks:
                print(f"Tick: {tick_info['tick']}, Gross Liquidity: {tick_info['liquidity_gross']}, Net Liquidity: {tick_info['liquidity_net']}, Initialized: {tick_info['initialized']}")
        else:
            print("No initialized ticks found in the checked range!")
        
        print("\nRecommended Ranges:")
        if initialized_ticks:
            sorted_ticks = sorted([t["tick"] for t in initialized_ticks])
            print("For successful liquidity addition, try using tick ranges between these initialized ticks:")
            for i in range(len(sorted_ticks) - 1):
                print(f"Range {i+1}: {sorted_ticks[i]} to {sorted_ticks[i+1]}")
        else:
            print("Could not determine recommended ranges without initialized ticks")
    except Exception as e:
        print(f"Error accessing ticks: {e}")
        print("The pool contract might not support the ticks method, or there might be an issue with the ABI.")
    
    print("====================== END DIAGNOSTIC ======================")

if __name__ == "__main__":
    main() 