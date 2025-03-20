#!/usr/bin/env python3
"""
Sell sDAI-YES tokens for sDAI through SushiSwap V3 pool using the passthrough router.
"""

import os
import sys
import json
import time
import argparse
from web3 import Web3
from dotenv import load_dotenv
from config.constants import CONTRACT_ADDRESSES, TOKEN_CONFIG

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.futarchy_bot import FutarchyBot
from exchanges.passthrough_router import PassthroughRouter

# Load environment variables
load_dotenv()

# Constants
SDAI_YES_POOL = CONTRACT_ADDRESSES["sdaiYesPool"]  # SushiSwap V3 YES_sDAI/sDAI pool
SDAI_ADDRESS = TOKEN_CONFIG["currency"]["address"]
SDAI_YES_ADDRESS = TOKEN_CONFIG["currency"]["yes_address"]

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Sell sDAI-YES tokens for sDAI')
    parser.add_argument('amount', type=float, help='Amount of sDAI-YES to sell')
    parser.add_argument('--slippage', type=float, default=5.0, 
                        help='Slippage percentage (default: 5.0)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (do not execute transaction)')
    return parser.parse_args()

def main():
    """Main function."""
    args = parse_args()
    
    # Initialize the bot
    bot = FutarchyBot(verbose=True)
    w3 = bot.w3
    
    # Get current balances
    balances = bot.get_balances()
    sdai_yes_balance = balances['currency']['yes']
    sdai_balance = balances['currency']['wallet']
    
    print("Balance before swap:")
    print(f"sDAI-YES: {sdai_yes_balance:.6f}")
    print(f"sDAI: {sdai_balance:.6f}")
    
    # Check if enough balance
    if sdai_yes_balance < args.amount:
        print(f"❌ Insufficient balance. Have {sdai_yes_balance:.6f}, need {args.amount:.6f}")
        return
    
    # Get current pool price
    pool_address = w3.to_checksum_address(SDAI_YES_POOL)
    pool_abi = [{"inputs": [], "name": "slot0", "outputs": [{"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"}, {"internalType": "int24", "name": "tick", "type": "int24"}, {"internalType": "uint16", "name": "observationIndex", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"}, {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"}, {"internalType": "bool", "name": "unlocked", "type": "bool"}], "stateMutability": "view", "type": "function"},
               {"inputs": [], "name": "token0", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
               {"inputs": [], "name": "token1", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"}]
    
    pool_contract = w3.eth.contract(address=pool_address, abi=pool_abi)
    
    # Verify the pool tokens
    token0 = pool_contract.functions.token0().call()
    token1 = pool_contract.functions.token1().call()
    
    print(f"\nVerifying pool tokens:")
    print(f"Token0: {token0}")
    print(f"Token1: {token1}")
    print(f"Expected sDAI-YES: {SDAI_YES_ADDRESS}")
    print(f"Expected sDAI: {SDAI_ADDRESS}")
    
    # Determine if zero_for_one based on token positions
    if token0.lower() == SDAI_YES_ADDRESS.lower() and token1.lower() == SDAI_ADDRESS.lower():
        # sDAI-YES is token0, sDAI is token1
        zero_for_one = True
        print("Token order: sDAI-YES (token0) → sDAI (token1)")
        print("Using zero_for_one = True")
    elif token0.lower() == SDAI_ADDRESS.lower() and token1.lower() == SDAI_YES_ADDRESS.lower():
        # sDAI is token0, sDAI-YES is token1
        zero_for_one = False
        print("Token order: sDAI (token0) → sDAI-YES (token1)")
        print("Using zero_for_one = False")
    else:
        print("❌ Pool tokens don't match expected addresses!")
        return
    
    slot0 = pool_contract.functions.slot0().call()
    current_sqrt_price = slot0[0]
    current_tick = slot0[1]
    
    # Calculate price from sqrtPriceX96
    price = (current_sqrt_price / (2**96))**2
    
    if zero_for_one:
        # If sDAI-YES is token0, price is token1/token0 = sDAI per sDAI-YES
        price_display = f"{price:.6f} sDAI per sDAI-YES"
    else:
        # If sDAI is token0, price is token0/token1 = sDAI per sDAI-YES
        price_display = f"{(1/price):.6f} sDAI per sDAI-YES"
    
    print(f"\nCurrent Pool Status:")
    print(f"Current sqrtPriceX96: {current_sqrt_price}")
    print(f"Current tick: {current_tick}")
    print(f"Current price: {price_display}")
    
    # Set price limit based on direction
    slippage_factor = 1.0 - (args.slippage / 100.0)
    
    if zero_for_one:
        # For selling token0 to get token1, we set a lower price limit (down)
        sqrt_price_limit_x96 = int(current_sqrt_price * slippage_factor)
    else:
        # For selling token1 to get token0, we set an upper price limit (up)
        sqrt_price_limit_x96 = int(current_sqrt_price * (1 / slippage_factor))
    
    print(f"\nSwap Parameters:")
    print(f"Selling {args.amount:.6f} sDAI-YES")
    print(f"Slippage: {args.slippage:.2f}%")
    print(f"Price limit sqrtPriceX96: {sqrt_price_limit_x96}")
    
    if args.dry_run:
        print("\n🛑 DRY RUN MODE - Transaction will not be executed")
        return
    
    # Verify that the router contract address is set in the environment
    router_address = CONTRACT_ADDRESSES["uniswapV3PassthroughRouter"]
    if not router_address:
        print("❌ PassthroughRouter address not found!")
        return
    
    print(f"Using router at: {router_address}")
    
    # Execute the swap
    router = PassthroughRouter(
        w3,
        os.environ.get("PRIVATE_KEY"),
        router_address
    )
    
    print(f"\n🔄 Executing swap...")
    
    # If sDAI-YES is token0, set zero_for_one=True (selling token0)
    # If sDAI-YES is token1, set zero_for_one=False (selling token1)
    result = router.execute_swap(
        pool_address=pool_address,
        token_in=SDAI_YES_ADDRESS,
        token_out=SDAI_ADDRESS,
        amount=args.amount, 
        zero_for_one=zero_for_one,
        sqrt_price_limit_x96=sqrt_price_limit_x96
    )
    
    if result:
        print("✅ Swap successful!")
        
        # Get updated balances
        updated_balances = bot.get_balances()
        sdai_yes_change = updated_balances['currency']['yes'] - sdai_yes_balance
        sdai_change = updated_balances['currency']['wallet'] - sdai_balance
        
        print("\nBalance Changes:")
        print(f"sDAI-YES: {sdai_yes_change:+.6f}")
        print(f"sDAI: {sdai_change:+.6f}")
        
        # Calculate effective price
        if sdai_yes_change != 0:  # Avoid division by zero
            effective_price = abs(float(sdai_change) / float(sdai_yes_change))
            print(f"\nEffective price: {effective_price:.6f} sDAI per sDAI-YES")
        
        # Show the updated pool price
        try:
            new_slot0 = pool_contract.functions.slot0().call()
            new_sqrt_price = new_slot0[0]
            new_tick = new_slot0[1]
            new_price = (new_sqrt_price / (2**96))**2
            
            print(f"\nNew Pool Status:")
            print(f"New sqrtPriceX96: {new_sqrt_price}")
            print(f"New tick: {new_tick}")
            if zero_for_one:
                print(f"New price: {new_price:.6f} sDAI per sDAI-YES")
                print(f"Price change: {((new_price/price)-1)*100:.4f}%")
            else:
                print(f"New price: {(1/new_price):.6f} sDAI per sDAI-YES")
                print(f"Price change: {((1/new_price)/(1/price)-1)*100:.4f}%")
        except Exception as e:
            print(f"Error fetching updated pool price: {e}")
        
        # Show the full balances
        bot.print_balances(updated_balances)
    else:
        print("❌ Swap failed!")

if __name__ == "__main__":
    main() 