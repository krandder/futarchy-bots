#!/usr/bin/env python3
"""
Script to calculate price impact for fixed trade sizes in Balancer and SushiSwap pools.

This script calculates:
1. Current price in each pool
2. Price impact for a fixed trade size (default: 0.01 GNO equivalent)
3. Provides this information for three pools:
   - Balancer sDAI/waGNO pool
   - SushiSwap YES conditional pool (sDAI YES/GNO YES)
   - SushiSwap NO conditional pool (sDAI NO/GNO NO)

Usage:
  python calculate_price_impact.py [--amount AMOUNT] [--verbose]

Options:
  --amount AMOUNT        Trade amount in GNO equivalent (default: 0.01)
  --verbose, -v          Enable verbose output
  --help, -h             Show this help message
"""

import os
import sys
import math
from decimal import Decimal
from web3 import Web3
from utils.web3_utils import setup_web3_connection
from config.constants import (
    BALANCER_CONFIG, 
    TOKEN_CONFIG, 
    CONTRACT_ADDRESSES, 
    POOL_CONFIG_YES, 
    POOL_CONFIG_NO, 
    UNISWAP_V3_POOL_ABI
)
import argparse

# Price impact percentage to calculate (0.1%)
PRICE_IMPACT_PERCENTAGE = 0.1

class PoolLiquidityEstimator:
    """Class to estimate liquidity in various pools."""
    
    def __init__(self, verbose=False):
        """Initialize the estimator."""
        self.verbose = verbose
        self.w3 = setup_web3_connection()
        
        # Initialize contract addresses
        self.balancer_vault_address = self.w3.to_checksum_address(BALANCER_CONFIG["vault_address"])
        self.balancer_pool_address = self.w3.to_checksum_address(BALANCER_CONFIG["pool_address"])
        self.batch_router_address = self.w3.to_checksum_address(CONTRACT_ADDRESSES["batchRouter"])
        self.yes_pool_address = self.w3.to_checksum_address(POOL_CONFIG_YES["address"])
        self.no_pool_address = self.w3.to_checksum_address(POOL_CONFIG_NO["address"])
        
        # Initialize token addresses
        self.sdai_address = self.w3.to_checksum_address(TOKEN_CONFIG["currency"]["address"])
        self.wagno_address = self.w3.to_checksum_address(TOKEN_CONFIG["wagno"]["address"])
        self.gno_address = self.w3.to_checksum_address(TOKEN_CONFIG["company"]["address"])
        self.sdai_yes_address = self.w3.to_checksum_address(TOKEN_CONFIG["currency"]["yes_address"])
        self.sdai_no_address = self.w3.to_checksum_address(TOKEN_CONFIG["currency"]["no_address"])
        self.gno_yes_address = self.w3.to_checksum_address(TOKEN_CONFIG["company"]["yes_address"])
        self.gno_no_address = self.w3.to_checksum_address(TOKEN_CONFIG["company"]["no_address"])
        
        # Load ABIs
        self.load_abis()
        
        # Initialize contracts
        self.init_contracts()
        
        # Calculate GNO to waGNO conversion rate
        self.gno_to_wagno_rate = self.calculate_gno_to_wagno_rate()
        
        if self.verbose:
            print(f"Initialized PoolLiquidityEstimator")
            print(f"Balancer Pool: {self.balancer_pool_address}")
            print(f"YES Pool: {self.yes_pool_address}")
            print(f"NO Pool: {self.no_pool_address}")
            print(f"GNO to waGNO conversion rate: {self.gno_to_wagno_rate}")
    
    def load_abis(self):
        """Load contract ABIs."""
        # Try different possible locations for the ABI file
        possible_paths = [
            # Current working directory
            os.path.join(os.getcwd(), ".reference", "balancer_router.abi.json"),
            # Script directory
            os.path.join(os.path.dirname(os.path.abspath(__file__)), ".reference", "balancer_router.abi.json"),
            # Parent of script directory
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".reference", "balancer_router.abi.json"),
            # Absolute path
            "/Users/kas/futarchy-bots/.reference/balancer_router.abi.json"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    import json
                    self.batch_router_abi = json.load(f)
                    if self.verbose:
                        print(f"Loaded BatchRouter ABI from {path}")
                    return
        
        # If we get here, we couldn't find the file
        raise FileNotFoundError(f"BatchRouter ABI file not found. Tried: {possible_paths}")
    
    def init_contracts(self):
        """Initialize contract instances."""
        # Initialize BatchRouter contract
        self.batch_router = self.w3.eth.contract(
            address=self.batch_router_address,
            abi=self.batch_router_abi
        )
        
        # Initialize Uniswap V3 pool contracts for conditional tokens
        self.yes_pool = self.w3.eth.contract(
            address=self.yes_pool_address,
            abi=UNISWAP_V3_POOL_ABI
        )
        
        self.no_pool = self.w3.eth.contract(
            address=self.no_pool_address,
            abi=UNISWAP_V3_POOL_ABI
        )
    
    def calculate_gno_to_wagno_rate(self):
        """
        Calculate the conversion rate from GNO to waGNO.
        
        Returns:
            float: The conversion rate (1 GNO = X waGNO)
        """
        try:
            # For this example, we'll assume a 1:1 conversion rate
            # In a real implementation, you would query the actual conversion rate
            # from the appropriate contract or API
            conversion_rate = 1.0
            
            if self.verbose:
                print(f"GNO to waGNO conversion rate: {conversion_rate}")
            
            return conversion_rate
        except Exception as e:
            print(f"Error calculating GNO to waGNO conversion rate: {e}")
            # Default to 1:1 if there's an error
            return 1.0
    
    def estimate_balancer_pool_liquidity(self):
        """
        Estimate liquidity in the Balancer sDAI/waGNO pool.
        
        Returns:
            dict: Information about the pool liquidity
        """
        print("\n=== Balancer sDAI/waGNO Pool Liquidity ===")
        
        # Define paths for querying price
        paths = [
            {
                "tokenIn": self.sdai_address,
                "steps": [
                    {
                        "pool": self.balancer_pool_address,
                        "tokenOut": self.wagno_address,
                        "isBuffer": False
                    }
                ],
                "exactAmountIn": self.w3.to_wei(1, 'ether'),  # 1 sDAI
                "minAmountOut": 0
            }
        ]
        
        # Query current price (1 sDAI -> ? waGNO)
        try:
            result = self.batch_router.functions.querySwapExactIn(
                paths,
                self.w3.to_checksum_address("0x0000000000000000000000000000000000000000"),  # Zero address as sender
                '0x'  # Empty user data
            ).call()
            
            # Extract expected output amount
            expected_output = result[0][0]
            expected_output_eth = self.w3.from_wei(expected_output, 'ether')
            
            # Current price: 1 sDAI = ? waGNO
            current_price = float(expected_output_eth)
            print(f"Current Price: 1 sDAI = {current_price} waGNO")
            print(f"Current Price: 1 waGNO = {1/current_price if current_price != 0 else 'infinity'} sDAI")
            
            # Calculate amounts to move price by 0.1%
            # For price impact up (buying waGNO with sDAI)
            target_price_up = current_price * (1 + PRICE_IMPACT_PERCENTAGE/100)
            
            # Binary search to find amount needed for 0.1% price impact
            amount_for_impact_up = self.binary_search_balancer_impact(
                self.sdai_address, 
                self.wagno_address, 
                current_price, 
                target_price_up, 
                True
            )
            
            # For price impact down (selling waGNO for sDAI)
            target_price_down = current_price * (1 - PRICE_IMPACT_PERCENTAGE/100)
            
            amount_for_impact_down = self.binary_search_balancer_impact(
                self.wagno_address, 
                self.sdai_address, 
                1/current_price if current_price != 0 else float('inf'), 
                1/target_price_down if target_price_down != 0 else float('inf'), 
                False
            )
            
            print(f"\nTo move price UP by {PRICE_IMPACT_PERCENTAGE}% (1 sDAI = {target_price_up} waGNO):")
            print(f"Need to swap approximately {amount_for_impact_up} sDAI for waGNO")
            
            print(f"\nTo move price DOWN by {PRICE_IMPACT_PERCENTAGE}% (1 sDAI = {target_price_down} waGNO):")
            print(f"Need to swap approximately {amount_for_impact_down} waGNO for sDAI")
            
            return {
                "pool": "Balancer sDAI/waGNO",
                "current_price_sdai_to_wagno": current_price,
                "current_price_wagno_to_sdai": 1/current_price if current_price != 0 else float('inf'),
                "amount_for_up_impact": amount_for_impact_up,
                "amount_for_down_impact": amount_for_impact_down,
                "target_price_up": target_price_up,
                "target_price_down": target_price_down
            }
            
        except Exception as e:
            print(f"Error estimating Balancer pool liquidity: {e}")
            import traceback
            traceback.print_exc()
            return {
                "pool": "Balancer sDAI/waGNO",
                "error": str(e)
            }
    
    def binary_search_balancer_impact(self, token_in, token_out, current_price, target_price, is_price_up):
        """
        Use binary search to find amount needed for desired price impact.
        
        Args:
            token_in: Address of input token
            token_out: Address of output token
            current_price: Current price
            target_price: Target price after impact
            is_price_up: True if we're looking for price increase, False for decrease
            
        Returns:
            float: Approximate amount needed for the desired price impact
        """
        # Define search range - start with a smaller range
        min_amount = 0.001  # Start with a small amount
        max_amount = 100  # Start with a more reasonable upper bound
        best_amount = min_amount  # Default to minimum amount if nothing better is found
        best_price = None
        best_price_diff = float('inf')
        
        if self.verbose:
            print(f"\nBinary search for price impact:")
            print(f"Current price: {current_price}")
            print(f"Target price: {target_price}")
            print(f"Direction: {'UP' if is_price_up else 'DOWN'}")
        
        # Try a few small amounts first to get a better starting range
        test_amounts = [0.01, 0.1, 1.0, 10.0]
        for amount in test_amounts:
            try:
                # Query price for this amount
                paths = [
                    {
                        "tokenIn": token_in,
                        "steps": [
                            {
                                "pool": self.balancer_pool_address,
                                "tokenOut": token_out,
                                "isBuffer": False
                            }
                        ],
                        "exactAmountIn": self.w3.to_wei(amount, 'ether'),
                        "minAmountOut": 0
                    }
                ]
                
                result = self.batch_router.functions.querySwapExactIn(
                    paths,
                    self.w3.to_checksum_address("0x0000000000000000000000000000000000000000"),
                    '0x'
                ).call()
                
                # Calculate resulting price
                output_amount = float(self.w3.from_wei(result[0][0], 'ether'))
                resulting_price = output_amount / amount
                
                # For selling waGNO, we need to invert the price
                if not is_price_up:
                    resulting_price = 1 / resulting_price
                
                price_diff = abs(resulting_price - target_price)
                
                if self.verbose:
                    print(f"Test amount: {amount}, Resulting price: {resulting_price}, Diff: {price_diff}")
                
                # Update best estimate
                if price_diff < best_price_diff:
                    best_amount = amount
                    best_price = resulting_price
                    best_price_diff = price_diff
                
                # If we've passed the target price, we can set a better search range
                if (is_price_up and resulting_price > target_price) or (not is_price_up and resulting_price < target_price):
                    if amount < max_amount:
                        max_amount = amount * 2  # Set max to double this amount
                    if self.verbose:
                        print(f"Found upper bound at {amount}, setting max to {max_amount}")
                    break
            except Exception as e:
                if self.verbose:
                    print(f"Error testing amount {amount}: {e}")
        
        # Binary search with max 15 iterations for more precision
        for i in range(15):
            mid_amount = (min_amount + max_amount) / 2
            
            # Query price for this amount
            paths = [
                {
                    "tokenIn": token_in,
                    "steps": [
                        {
                            "pool": self.balancer_pool_address,
                            "tokenOut": token_out,
                            "isBuffer": False
                        }
                    ],
                    "exactAmountIn": self.w3.to_wei(mid_amount, 'ether'),
                    "minAmountOut": 0
                }
            ]
            
            try:
                result = self.batch_router.functions.querySwapExactIn(
                    paths,
                    self.w3.to_checksum_address("0x0000000000000000000000000000000000000000"),
                    '0x'
                ).call()
                
                # Calculate resulting price
                output_amount = float(self.w3.from_wei(result[0][0], 'ether'))
                resulting_price = output_amount / mid_amount
                
                # For selling waGNO, we need to invert the price
                if not is_price_up:
                    resulting_price = 1 / resulting_price
                
                price_diff = abs(resulting_price - target_price)
                
                if self.verbose:
                    print(f"Iteration {i+1}: Amount={mid_amount}, Price={resulting_price}, Target={target_price}, Diff={price_diff}")
                
                # Update best estimate
                if price_diff < best_price_diff:
                    best_amount = mid_amount
                    best_price = resulting_price
                    best_price_diff = price_diff
                
                # Adjust search range
                if (is_price_up and resulting_price < target_price) or (not is_price_up and resulting_price > target_price):
                    min_amount = mid_amount
                else:
                    max_amount = mid_amount
                    
                # If we're very close to the target, we can stop early
                if price_diff < 0.0000001 * target_price:
                    if self.verbose:
                        print(f"Found very close match, stopping early")
                    break
                    
            except Exception as e:
                # If error, try a smaller amount
                if self.verbose:
                    print(f"Error at amount {mid_amount}: {e}")
                max_amount = mid_amount
        
        if self.verbose:
            print(f"Best amount found: {best_amount}, resulting price: {best_price}, diff: {best_price_diff}")
            
        return best_amount
    
    def estimate_conditional_pool_liquidity(self, is_yes_pool):
        """
        Estimate liquidity in a conditional token pool.
        
        Args:
            is_yes_pool: True for YES pool, False for NO pool
            
        Returns:
            dict: Information about the pool liquidity
        """
        pool_name = "YES" if is_yes_pool else "NO"
        pool_contract = self.yes_pool if is_yes_pool else self.no_pool
        pool_address = self.yes_pool_address if is_yes_pool else self.no_pool_address
        
        print(f"\n=== SushiSwap {pool_name} Conditional Pool Liquidity ===")
        
        try:
            # Get token0 and token1
            token0 = pool_contract.functions.token0().call()
            token1 = pool_contract.functions.token1().call()
            
            # Identify token names
            token0_name = self.get_token_name(token0)
            token1_name = self.get_token_name(token1)
            
            print(f"Pool address: {pool_address}")
            print(f"Token0: {token0} ({token0_name})")
            print(f"Token1: {token1} ({token1_name})")
            
            # Get slot0 data for current price
            try:
                slot0 = pool_contract.functions.slot0().call()
                sqrt_price_x96 = slot0[0]
                tick = slot0[1]
                
                # Calculate price from sqrtPriceX96
                price = (sqrt_price_x96 / (2**96))**2
                
                print(f"sqrtPriceX96: {sqrt_price_x96}")
                print(f"tick: {tick}")
                print(f"Current Price ({token1_name}/{token0_name}): {price}")
                print(f"Current Price ({token0_name}/{token1_name}): {1/price if price != 0 else 'infinity'}")
                
                # Calculate target prices for 0.1% impact
                target_price_up = price * (1 + PRICE_IMPACT_PERCENTAGE/100)
                target_price_down = price * (1 - PRICE_IMPACT_PERCENTAGE/100)
                
                # Calculate sqrt price for target prices
                target_sqrt_price_up = int(math.sqrt(target_price_up) * (2**96))
                target_sqrt_price_down = int(math.sqrt(target_price_down) * (2**96))
                
                # Calculate tick for target prices
                # Formula: tick = log(sqrt_price_x96 / 2^96) / log(sqrt(1.0001))
                target_tick_up = math.log(target_sqrt_price_up / (2**96)) / math.log(math.sqrt(1.0001))
                target_tick_down = math.log(target_sqrt_price_down / (2**96)) / math.log(math.sqrt(1.0001))
                
                # For Uniswap V3 style pools, we would need to calculate the amount needed to move the price
                # This is complex and depends on the liquidity distribution across ticks
                # For a simplified estimate, we can use a constant product formula (x * y = k)
                
                # Note: This is a simplified approach and may not be accurate for concentrated liquidity pools
                # A more accurate approach would require analyzing the liquidity distribution
                
                # For now, we'll provide a rough estimate based on the current price and target price
                # This assumes uniform liquidity distribution, which is not accurate for Uniswap V3
                
                print(f"\nNote: For Uniswap V3 style pools, liquidity is concentrated and varies across price ranges.")
                print(f"The following estimates are rough approximations assuming uniform liquidity.")
                
                # Estimate amount needed for price impact (very rough approximation)
                # For a 0.1% price change in a constant product pool, approximately sqrt(0.001) * liquidity is needed
                # This is a very rough estimate and should be refined with actual liquidity data
                
                # Since we don't have direct access to the liquidity at each tick, we'll use a placeholder
                estimated_amount_up = "Requires detailed liquidity analysis"
                estimated_amount_down = "Requires detailed liquidity analysis"
                
                print(f"\nTo move price UP by {PRICE_IMPACT_PERCENTAGE}% ({token1_name}/{token0_name} = {target_price_up}):")
                print(f"Estimated amount needed: {estimated_amount_up}")
                
                print(f"\nTo move price DOWN by {PRICE_IMPACT_PERCENTAGE}% ({token1_name}/{token0_name} = {target_price_down}):")
                print(f"Estimated amount needed: {estimated_amount_down}")
                
                return {
                    "pool": f"SushiSwap {pool_name} Conditional Pool",
                    "token0": token0_name,
                    "token1": token1_name,
                    "current_price_token1_token0": price,
                    "current_price_token0_token1": 1/price if price != 0 else float('inf'),
                    "target_price_up": target_price_up,
                    "target_price_down": target_price_down,
                    "estimated_amount_up": estimated_amount_up,
                    "estimated_amount_down": estimated_amount_down
                }
                
            except Exception as e:
                print(f"Error getting slot0 data: {e}")
                return {
                    "pool": f"SushiSwap {pool_name} Conditional Pool",
                    "token0": token0_name,
                    "token1": token1_name,
                    "error": f"Error getting price data: {str(e)}"
                }
                
        except Exception as e:
            print(f"Error estimating {pool_name} pool liquidity: {e}")
            return {
                "pool": f"SushiSwap {pool_name} Conditional Pool",
                "error": str(e)
            }
    
    def get_token_name(self, address):
        """Get a human-readable name for a token address."""
        address_lower = address.lower()
        
        if address_lower == self.sdai_address.lower():
            return "sDAI"
        elif address_lower == self.wagno_address.lower():
            return "waGNO"
        elif address_lower == self.gno_address.lower():
            return "GNO"
        elif address_lower == self.sdai_yes_address.lower():
            return "sDAI YES"
        elif address_lower == self.sdai_no_address.lower():
            return "sDAI NO"
        elif address_lower == self.gno_yes_address.lower():
            return "GNO YES"
        elif address_lower == self.gno_no_address.lower():
            return "GNO NO"
        else:
            return "Unknown"

def main():
    """Main function to run the script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Calculate price impact for fixed trade sizes in Balancer and SushiSwap pools")
    parser.add_argument("--amount", type=float, default=0.01, help="Trade amount in GNO equivalent (default: 0.01)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Initialize the price impact calculator
    calculator = PriceImpactCalculator(verbose=args.verbose)
    
    # Calculate price impact for the specified GNO amount
    print(f"\nCalculating price impact for {args.amount} GNO equivalent...")
    
    # Calculate price impact for Balancer pool
    balancer_result = calculator.calculate_balancer_price_impact(args.amount)
    
    # Calculate price impact for YES conditional pool
    yes_result = calculator.calculate_conditional_price_impact(args.amount, is_yes_pool=True)
    
    # Calculate price impact for NO conditional pool
    no_result = calculator.calculate_conditional_price_impact(args.amount, is_yes_pool=False)
    
    # Print summary
    print("\n=== Price Impact Summary ===")
    print(f"Trade amount: {args.amount} GNO")
    print(f"GNO to waGNO conversion rate: {calculator.gno_to_wagno_rate}")
    
    print("\nBalancer sDAI/waGNO Pool:")
    if "error" in balancer_result:
        print(f"  Error: {balancer_result['error']}")
    else:
        print(f"  Current price: 1 sDAI = {balancer_result['current_price_sdai_to_wagno']} waGNO")
        print(f"  Buy impact: {balancer_result['buy_price_impact_percentage']:.4f}% for {args.amount * calculator.gno_to_wagno_rate} waGNO")
        print(f"  Sell impact: {balancer_result['sell_price_impact_percentage']:.4f}% for {args.amount * calculator.gno_to_wagno_rate} waGNO")
    
    print("\nSushiSwap YES Conditional Pool:")
    if "error" in yes_result:
        print(f"  Error: {yes_result['error']}")
    else:
        print(f"  Current price: 1 {yes_result['token0']} = {yes_result['current_price']} {yes_result['token1']}")
        print(f"  Estimated buy impact: {yes_result['estimated_buy_impact']}")
        print(f"  Estimated sell impact: {yes_result['estimated_sell_impact']}")
    
    print("\nSushiSwap NO Conditional Pool:")
    if "error" in no_result:
        print(f"  Error: {no_result['error']}")
    else:
        print(f"  Current price: 1 {no_result['token0']} = {no_result['current_price']} {no_result['token1']}")
        print(f"  Estimated buy impact: {no_result['estimated_buy_impact']}")
        print(f"  Estimated sell impact: {no_result['estimated_sell_impact']}")

if __name__ == "__main__":
    main() 