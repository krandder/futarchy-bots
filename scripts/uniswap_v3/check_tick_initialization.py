#!/usr/bin/env python3
"""
Check Tick Initialization Status

This script checks if specific ticks are initialized in a Uniswap V3 pool.
It uses the Uniswap V3 JavaScript bridge to access the SDK functionality.
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
    parser = argparse.ArgumentParser(description='Check tick initialization status in a Uniswap V3 pool')
    parser.add_argument('--pool', type=str, help='Pool address', 
                        default=os.getenv("POOL_YES", "0x9a14d28909f42823ee29847f87a15fb3b6e8aed3"))
    parser.add_argument('--ticks', type=str, help='Comma-separated list of ticks to check')
    parser.add_argument('--range', type=int, help='Number of ticks to check around current tick', default=10)
    return parser.parse_args()

def main():
    """Main function to check tick initialization status."""
    args = parse_args()
    
    client = UniswapV3Client()
    
    try:
        # Get pool information
        print(f"Getting information for pool {args.pool}...")
        pool_info = client.get_pool_info(args.pool)
        
        token0 = pool_info['token0']['symbol']
        token1 = pool_info['token1']['symbol']
        current_tick = pool_info['tick']
        tick_spacing = pool_info['tickSpacing']
        
        print(f"\nPool Information:")
        print(f"Token0: {token0} ({pool_info['token0']['address']})")
        print(f"Token1: {token1} ({pool_info['token1']['address']})")
        print(f"Current Tick: {current_tick}")
        print(f"Fee: {pool_info['fee']/10000}%")
        print(f"Tick Spacing: {tick_spacing}")
        
        # Determine which ticks to check
        ticks_to_check = []
        
        # If specific ticks were provided, use those
        if args.ticks:
            ticks_to_check = [int(tick.strip()) for tick in args.ticks.split(',')]
        
        # Add ticks around current tick based on range
        for i in range(-args.range, args.range + 1):
            tick = current_tick + (i * tick_spacing)
            if tick not in ticks_to_check:
                ticks_to_check.append(tick)
        
        # Add MIN_TICK and MAX_TICK
        min_tick = -887272  # TickMath.MIN_TICK
        max_tick = 887272   # TickMath.MAX_TICK
        
        # Adjust to nearest tick spacing
        min_tick = (min_tick // tick_spacing) * tick_spacing
        max_tick = (max_tick // tick_spacing) * tick_spacing
        
        if min_tick not in ticks_to_check:
            ticks_to_check.append(min_tick)
        if max_tick not in ticks_to_check:
            ticks_to_check.append(max_tick)
        
        # Sort ticks
        ticks_to_check.sort()
        
        # Check tick initialization status
        print(f"\nChecking initialization status for {len(ticks_to_check)} ticks...")
        results = client.check_ticks(args.pool, ticks_to_check)
        
        # Display results
        print("\nTick Initialization Status:")
        print("=" * 80)
        print(f"{'Tick':<10} | {'Status':<15} | {'Distance from Current':<20} | {'Notes'}")
        print("-" * 80)
        
        initialized_count = 0
        for tick, is_initialized in results['results'].items():
            tick = int(tick)
            distance = tick - current_tick
            notes = []
            
            if tick == current_tick:
                notes.append("CURRENT TICK")
            if tick == min_tick:
                notes.append("MIN_TICK")
            if tick == max_tick:
                notes.append("MAX_TICK")
                
            status = "Initialized" if is_initialized else "Not Initialized"
            if is_initialized:
                initialized_count += 1
                
            print(f"{tick:<10} | {status:<15} | {distance:<20} | {', '.join(notes)}")
        
        # Summary
        print("\nSummary:")
        print(f"Checked {len(results['results'])} ticks")
        print(f"Initialized: {initialized_count}")
        print(f"Not Initialized: {len(results['results']) - initialized_count}")
        
        if initialized_count == 0:
            print("\nWARNING: None of the checked ticks are initialized!")
            print("This may cause issues when adding liquidity.")
            print("Consider using full range positions (MIN_TICK to MAX_TICK) or initializing ticks first.")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 