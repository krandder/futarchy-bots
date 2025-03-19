#!/usr/bin/env python3
"""
Add Full Range Liquidity to Uniswap V3 Pool

This script adds liquidity across the full price range (MIN_TICK to MAX_TICK)
to a Uniswap V3 pool. This approach works even with uninitialized ticks.
"""

import os
import sys
import argparse
import json
from dotenv import load_dotenv
from uniswap_v3_client import UniswapV3Client

# Load environment variables
load_dotenv()

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Add full range liquidity to a Uniswap V3 pool')
    parser.add_argument('--pool', type=str, help='Pool address', 
                        default=os.getenv("POOL_YES", "0x9a14d28909f42823ee29847f87a15fb3b6e8aed3"))
    parser.add_argument('--amount0', type=str, help='Amount of token0 to add', required=True)
    parser.add_argument('--amount1', type=str, help='Amount of token1 to add', required=True)
    parser.add_argument('--dry-run', action='store_true', help='Dry run (do not execute transaction)')
    return parser.parse_args()

def main():
    """Main function to add full range liquidity."""
    args = parse_args()
    
    client = UniswapV3Client()
    
    try:
        # Get pool information
        print(f"Getting information for pool {args.pool}...")
        pool_info = client.get_pool_info(args.pool)
        
        token0 = pool_info['token0']['symbol']
        token1 = pool_info['token1']['symbol']
        current_tick = pool_info['tick']
        
        print(f"\nPool Information:")
        print(f"Token0: {token0} ({pool_info['token0']['address']})")
        print(f"Token1: {token1} ({pool_info['token1']['address']})")
        print(f"Current Tick: {current_tick}")
        print(f"Fee: {pool_info['fee']/10000}%")
        print(f"Tick Spacing: {pool_info['tickSpacing']}")
        
        # Check if we're in dry run mode
        if args.dry_run:
            print("\nDRY RUN MODE - Transaction will not be executed")
            print(f"Would add {args.amount0} {token0} and {args.amount1} {token1} as full range liquidity")
            return
        
        # Add full range liquidity
        print(f"\nAdding {args.amount0} {token0} and {args.amount1} {token1} as full range liquidity...")
        result = client.add_full_range_liquidity(args.pool, args.amount0, args.amount1)
        
        print("\nTransaction successful!")
        print(f"Transaction Hash: {result['transactionHash']}")
        print(f"Position Details:")
        print(json.dumps(result['position'], indent=2))
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 