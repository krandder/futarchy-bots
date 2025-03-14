#!/usr/bin/env python3
import os
import sys
from web3 import Web3
from utils.web3_utils import setup_web3_connection
from config.constants import POOL_CONFIG_YES, POOL_CONFIG_NO, UNISWAP_V3_POOL_ABI

def check_pool(pool_config, pool_name):
    """Check the status of a pool."""
    print(f"\n=== Checking {pool_name} Pool ===")
    
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
    
    # Get slot0 data
    try:
        slot0 = pool_contract.functions.slot0().call()
        print(f"sqrtPriceX96: {slot0[0]}")
        print(f"tick: {slot0[1]}")
        print(f"unlocked: {slot0[6]}")
    except Exception as e:
        print(f"Error getting slot0 data: {e}")

def main():
    """Check the status of the YES and NO pools."""
    check_pool(POOL_CONFIG_YES, "YES")
    check_pool(POOL_CONFIG_NO, "NO")

if __name__ == "__main__":
    main() 