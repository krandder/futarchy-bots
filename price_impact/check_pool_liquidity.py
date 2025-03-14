#!/usr/bin/env python3
import os
import sys
from web3 import Web3
from utils.web3_utils import setup_web3_connection
from config.constants import POOL_CONFIG_YES, POOL_CONFIG_NO, UNISWAP_V3_POOL_ABI, TOKEN_CONFIG

def check_pool_liquidity(pool_config, pool_name):
    """Check the liquidity of a pool."""
    print(f"\n=== Checking {pool_name} Pool Liquidity ===")
    
    # Set up Web3 connection
    w3 = setup_web3_connection()
    
    # Create pool contract
    pool_contract = w3.eth.contract(
        address=w3.to_checksum_address(pool_config['address']),
        abi=UNISWAP_V3_POOL_ABI
    )
    
    # Get token0 and token1
    token0 = pool_contract.functions.token0().call()
    token1 = pool_contract.functions.token1().call()
    
    print(f"Pool address: {pool_config['address']}")
    print(f"Token0: {token0}")
    print(f"Token1: {token1}")
    
    # Identify token names
    token0_name = "Unknown"
    token1_name = "Unknown"
    
    if token0.lower() == TOKEN_CONFIG["currency"]["yes_address"].lower():
        token0_name = "sDAI YES"
    elif token0.lower() == TOKEN_CONFIG["currency"]["no_address"].lower():
        token0_name = "sDAI NO"
    elif token0.lower() == TOKEN_CONFIG["company"]["yes_address"].lower():
        token0_name = "GNO YES"
    elif token0.lower() == TOKEN_CONFIG["company"]["no_address"].lower():
        token0_name = "GNO NO"
        
    if token1.lower() == TOKEN_CONFIG["currency"]["yes_address"].lower():
        token1_name = "sDAI YES"
    elif token1.lower() == TOKEN_CONFIG["currency"]["no_address"].lower():
        token1_name = "sDAI NO"
    elif token1.lower() == TOKEN_CONFIG["company"]["yes_address"].lower():
        token1_name = "GNO YES"
    elif token1.lower() == TOKEN_CONFIG["company"]["no_address"].lower():
        token1_name = "GNO NO"
    
    print(f"Token0 Name: {token0_name}")
    print(f"Token1 Name: {token1_name}")
    
    # Get slot0 data
    try:
        slot0 = pool_contract.functions.slot0().call()
        sqrt_price_x96 = slot0[0]
        tick = slot0[1]
        unlocked = slot0[6]
        
        print(f"sqrtPriceX96: {sqrt_price_x96}")
        print(f"tick: {tick}")
        print(f"unlocked: {unlocked}")
        
        # Calculate price from sqrtPriceX96
        price = (sqrt_price_x96 / (2**96))**2
        print(f"Price ({token1_name}/{token0_name}): {price}")
        print(f"Price ({token0_name}/{token1_name}): {1/price if price != 0 else 'infinity'}")
        
    except Exception as e:
        print(f"Error getting slot0 data: {e}")
    
    # Try to get liquidity
    try:
        # This is a simplified approach - in a real implementation, you would need to
        # query positions at various ticks to get the full liquidity picture
        liquidity = pool_contract.functions.liquidity().call()
        print(f"Current Liquidity: {liquidity}")
    except Exception as e:
        print(f"Error getting liquidity: {e}")

def main():
    """Check the liquidity of the YES and NO pools."""
    check_pool_liquidity(POOL_CONFIG_YES, "YES")
    check_pool_liquidity(POOL_CONFIG_NO, "NO")

if __name__ == "__main__":
    main() 