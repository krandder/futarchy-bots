#!/usr/bin/env python3
"""
Calculate price impact for fixed trade sizes in Balancer and SushiSwap pools.

This script calculates the price impact of trading a fixed amount of GNO (or its waGNO equivalent)
in the Balancer sDAI/waGNO pool and SushiSwap conditional token pools.

For each pool, the script calculates:
1. The current price in the pool
2. The price impact when buying tokens with the specified GNO amount
3. The price impact when selling tokens with the specified GNO amount
4. The GNO to waGNO conversion rate

Usage:
    python price_impact_calculator.py [--amount AMOUNT] [--verbose]

Options:
    --amount AMOUNT    Trade amount in GNO equivalent (default: 0.01)
    --verbose, -v      Enable verbose output
    --help, -h         Show this help message and exit
"""

import argparse
import sys
import os

# Add the current directory to the path so we can import the price_impact package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from price_impact.utils.web3_utils import setup_web3_connection
from price_impact.gno_converter import GnoConverter
from price_impact.balancer_calculator import BalancerPriceImpactCalculator
from price_impact.sushiswap_calculator import SushiSwapPriceImpactCalculator
from price_impact.config.constants import (
    BALANCER_CONFIG, 
    TOKEN_CONFIG, 
    CONTRACT_ADDRESSES, 
    POOL_CONFIG_YES, 
    POOL_CONFIG_NO
)

def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description="Calculate price impact for fixed trade sizes in Balancer and SushiSwap pools")
    parser.add_argument("--amount", type=float, default=0.01, help="Trade amount in GNO equivalent (default: 0.01)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Set up Web3 connection
    w3 = setup_web3_connection()
    
    # Initialize GNO converter
    gno_converter = GnoConverter(
        w3=w3,
        gno_address=TOKEN_CONFIG["company"]["address"],
        wagno_address=TOKEN_CONFIG["wagno"]["address"],
        verbose=args.verbose
    )
    
    # Calculate GNO to waGNO conversion rate
    gno_to_wagno_rate = gno_converter.calculate_conversion_rate()
    
    # Initialize Balancer price impact calculator
    balancer_calculator = BalancerPriceImpactCalculator(
        w3=w3,
        balancer_pool_address=BALANCER_CONFIG["pool_address"],
        balancer_vault_address=BALANCER_CONFIG["vault_address"],
        batch_router_address=CONTRACT_ADDRESSES["batchRouter"],
        sdai_address=TOKEN_CONFIG["currency"]["address"],
        wagno_address=TOKEN_CONFIG["wagno"]["address"],
        gno_to_wagno_rate=gno_to_wagno_rate,
        verbose=args.verbose
    )
    
    # Initialize SushiSwap price impact calculator
    sushiswap_calculator = SushiSwapPriceImpactCalculator(
        w3=w3,
        yes_pool_address=POOL_CONFIG_YES["address"],
        no_pool_address=POOL_CONFIG_NO["address"],
        sdai_yes_address=TOKEN_CONFIG["currency"]["yes_address"],
        sdai_no_address=TOKEN_CONFIG["currency"]["no_address"],
        gno_yes_address=TOKEN_CONFIG["company"]["yes_address"],
        gno_no_address=TOKEN_CONFIG["company"]["no_address"],
        verbose=args.verbose
    )
    
    # Calculate price impact for the specified GNO amount
    print(f"\nCalculating price impact for {args.amount} GNO equivalent...")
    
    # Calculate price impact for Balancer pool
    balancer_result = balancer_calculator.calculate_price_impact(args.amount)
    
    # Calculate price impact for YES conditional pool
    yes_result = sushiswap_calculator.calculate_price_impact(args.amount, is_yes_pool=True)
    
    # Calculate price impact for NO conditional pool
    no_result = sushiswap_calculator.calculate_price_impact(args.amount, is_yes_pool=False)
    
    # Print summary
    print("\n=== Price Impact Summary ===")
    print(f"Trade amount: {args.amount} GNO")
    print(f"GNO to waGNO conversion rate: {gno_to_wagno_rate}")
    
    print("\nBalancer sDAI/waGNO Pool:")
    if "error" in balancer_result:
        print(f"  Error: {balancer_result['error']}")
    else:
        # Calculate and display GNO/sDAI price (using waGNO as proxy for GNO)
        gno_to_sdai_price = balancer_result['current_price_wagno_to_sdai']
        print(f"  Current price: 1 GNO = {gno_to_sdai_price:.6f} sDAI")
        print(f"  Buy impact: {balancer_result['buy_price_impact_percentage']:.4f}% for {args.amount} GNO")
        print(f"  Sell impact: {balancer_result['sell_price_impact_percentage']:.4f}% for {args.amount} GNO")
    
    print("\nSushiSwap YES Conditional Pool:")
    if "error" in yes_result:
        print(f"  Error: {yes_result['error']}")
    else:
        # Display GNO/sDAI price
        print(f"  Current price: 1 GNO YES = {yes_result['current_price_gno_to_sdai']:.6f} sDAI YES")
        print(f"  Simulated buy impact: {yes_result['buy_price_impact']}")
        print(f"  Simulated sell impact: {yes_result['sell_price_impact']}")
    
    print("\nSushiSwap NO Conditional Pool:")
    if "error" in no_result:
        print(f"  Error: {no_result['error']}")
    else:
        # Display GNO/sDAI price
        print(f"  Current price: 1 GNO NO = {no_result['current_price_gno_to_sdai']:.6f} sDAI NO")
        print(f"  Simulated buy impact: {no_result['buy_price_impact']}")
        print(f"  Simulated sell impact: {no_result['sell_price_impact']}")
    
    print("\nNote: For more accurate price impact calculations for Uniswap V3-style pools,")
    print("consider implementing integration with the SushiSwap Quoter contract or")
    print("using on-chain simulation via 'eth_call'.")

if __name__ == "__main__":
    main() 