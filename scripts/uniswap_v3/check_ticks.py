#!/usr/bin/env python3
"""
Check if specific ticks are initialized in a Uniswap V3-style pool.

This script helps diagnose issues with Uniswap V3-style pools by checking
if specific ticks are initialized. This is particularly useful for custom
or new pools where liquidity addition might fail due to uninitialized ticks.

Usage:
    python check_ticks.py                                # Check default ticks in YES pool
    python check_ticks.py --ticks "51299,51300,51301"    # Check specific ticks
    python check_ticks.py --pool <pool_address>          # Check ticks in a different pool
"""

import os
import argparse
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
CONTRACT_ADDRESSES = {
    "baseCurrencyToken": "0xaf204776c7245bF4147c2612BF6e5972Ee483701",  # SDAI
    "baseCompanyToken": "0x9C58BAcC331c9aa871AFD802DB6379a98e80CEdb",  # GNO
    "currencyYesToken": "0x493A0D1c776f8797297Aa8B34594fBd0A7F8968a",  # sDAI YES
    "currencyNoToken": "0xE1133Ef862f3441880adADC2096AB67c63f6E102",
    "companyYesToken": "0x177304d505eCA60E1aE0dAF1bba4A4c4181dB8Ad",  # GNO YES
    "companyNoToken": "0xf1B3E5Ffc0219A4F8C0ac69EC98C97709EdfB6c9",
    "wagno": "0x7c16f0185a26db0ae7a9377f23bc18ea7ce5d644",
    "poolYes": "0x9a14d28909f42823ee29847f87a15fb3b6e8aed3",
    "poolNo": "0x6E33153115Ab58dab0e0F1E3a2ccda6e67FA5cD7",
    "sushiswapNFPM": "0xaB235da7f52d35fb4551AfBa11BFB56e18774A65",  # SushiSwap V3 NonFungiblePositionManager
}

# ABIs
UNISWAP_V3_POOL_ABI = [
    {"inputs": [], "name": "token0", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "token1", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "slot0", "outputs": [{"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"}, {"internalType": "int24", "name": "tick", "type": "int24"}, {"internalType": "uint16", "name": "observationIndex", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"}, {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"}, {"internalType": "bool", "name": "unlocked", "type": "bool"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "fee", "outputs": [{"internalType": "uint24", "name": "", "type": "uint24"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "tickSpacing", "outputs": [{"internalType": "int24", "name": "", "type": "int24"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "int24", "name": "tick", "type": "int24"}], "name": "ticks", "outputs": [{"internalType": "uint128", "name": "liquidityGross", "type": "uint128"}, {"internalType": "int128", "name": "liquidityNet", "type": "int128"}, {"internalType": "uint256", "name": "feeGrowthOutside0X128", "type": "uint256"}, {"internalType": "uint256", "name": "feeGrowthOutside1X128", "type": "uint256"}, {"internalType": "int56", "name": "tickCumulativeOutside", "type": "int56"}, {"internalType": "uint160", "name": "secondsPerLiquidityOutsideX128", "type": "uint160"}, {"internalType": "uint32", "name": "secondsOutside", "type": "uint32"}, {"internalType": "bool", "name": "initialized", "type": "bool"}], "stateMutability": "view", "type": "function"}
]

ERC20_ABI = [
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "payable": False, "stateMutability": "view", "type": "function"}
]

def check_tick_initialized(w3, pool_contract, tick):
    """
    Check if a tick is initialized.
    
    In Uniswap V3, a tick must be initialized before it can be used as a boundary
    for a liquidity position. This function checks if a specific tick is initialized
    by calling the 'ticks' function on the pool contract and checking the 'initialized'
    boolean in the returned data.
    
    Args:
        w3: Web3 instance
        pool_contract: Pool contract instance
        tick: Tick to check
        
    Returns:
        bool: True if initialized, False otherwise
    """
    try:
        tick_info = pool_contract.functions.ticks(tick).call()
        return tick_info[7]  # initialized boolean
    except Exception as e:
        print(f"Error checking tick {tick}: {e}")
        return False

def check_ticks(w3, pool_address, ticks_to_check):
    """
    Check if specific ticks are initialized in a pool.
    
    This function connects to a Uniswap V3-style pool and checks if specific ticks
    are initialized. It also checks ticks around the current tick to provide context.
    
    In Uniswap V3, liquidity is concentrated within specific price ranges defined by
    "ticks". For a position to be valid, these ticks must be "initialized" in the pool.
    When a pool is new or has low liquidity, many ticks may not be initialized yet,
    which can cause transactions to fail when trying to add liquidity.
    
    Args:
        w3: Web3 instance
        pool_address: Address of the pool
        ticks_to_check: List of ticks to check
        
    Returns:
        dict: Information about the ticks (key: tick, value: initialized boolean)
    """
    print("\n" + "="*80)
    print("CHECKING TICKS IN POOL")
    print("="*80)
    
    # Connect to the pool
    pool_contract = w3.eth.contract(
        address=w3.to_checksum_address(pool_address),
        abi=UNISWAP_V3_POOL_ABI
    )
    
    # Get pool information
    token0 = pool_contract.functions.token0().call()
    token1 = pool_contract.functions.token1().call()
    slot0 = pool_contract.functions.slot0().call()
    fee = pool_contract.functions.fee().call()
    
    try:
        tick_spacing = pool_contract.functions.tickSpacing().call()
    except Exception as e:
        print(f"Warning: Could not get tick spacing: {e}")
        tick_spacing = 1  # Default to 1 if we can't get it
    
    current_tick = slot0[1]
    
    # Get token information
    token0_contract = w3.eth.contract(address=w3.to_checksum_address(token0), abi=ERC20_ABI)
    token1_contract = w3.eth.contract(address=w3.to_checksum_address(token1), abi=ERC20_ABI)
    
    token0_symbol = token0_contract.functions.symbol().call()
    token1_symbol = token1_contract.functions.symbol().call()
    
    print(f"Pool Address: {pool_address}")
    print(f"Token0: {token0_symbol} ({token0})")
    print(f"Token1: {token1_symbol} ({token1})")
    print(f"Current Tick: {current_tick}")
    print(f"Fee: {fee/10000}%")
    print(f"Tick Spacing: {tick_spacing}")
    
    # Check the ticks
    print("\nChecking ticks:")
    
    results = {}
    for tick in ticks_to_check:
        # Make sure tick is a multiple of tick spacing
        adjusted_tick = (tick // tick_spacing) * tick_spacing
        
        is_initialized = check_tick_initialized(w3, pool_contract, adjusted_tick)
        results[adjusted_tick] = is_initialized
        
        print(f"Tick {adjusted_tick}: {'Initialized' if is_initialized else 'Not Initialized'}")
    
    # Check some ticks around the current tick
    print("\nChecking ticks around current tick:")
    
    for i in range(-5, 6):
        tick = current_tick + (i * tick_spacing)
        is_initialized = check_tick_initialized(w3, pool_contract, tick)
        results[tick] = is_initialized
        
        print(f"Tick {tick} ({i * tick_spacing} from current): {'Initialized' if is_initialized else 'Not Initialized'}")
    
    # Summary
    initialized_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    print("\nSummary:")
    print(f"Checked {total_count} ticks, {initialized_count} initialized, {total_count - initialized_count} not initialized")
    
    if initialized_count == 0:
        print("\nNone of the checked ticks are initialized. This may cause issues when adding liquidity.")
        print("Consider initializing ticks before adding liquidity, or check with the pool creator.")
    elif initialized_count < total_count:
        print("\nSome ticks are not initialized. Make sure to use initialized ticks when adding liquidity.")
    else:
        print("\nAll checked ticks are initialized. You should be able to add liquidity using these ticks.")
    
    return results

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Check if specific ticks are initialized in a pool')
    parser.add_argument('--pool', type=str, help='Pool address', default=CONTRACT_ADDRESSES["poolYes"])
    parser.add_argument('--ticks', type=str, help='Comma-separated list of ticks to check', default="-887272,887272,44367,58231")
    args = parser.parse_args()
    
    # Connect to Gnosis Chain
    rpc_url = os.getenv("RPC_URL", "https://rpc.gnosischain.com")
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    # Check connection
    if not w3.is_connected():
        print("❌ Failed to connect to the blockchain")
        return
    
    print(f"✅ Connected to {rpc_url}")
    
    # Parse ticks to check
    ticks_to_check = [int(tick.strip()) for tick in args.ticks.split(",")]
    
    # Check ticks
    check_ticks(
        w3=w3,
        pool_address=args.pool,
        ticks_to_check=ticks_to_check
    )

if __name__ == "__main__":
    main() 