#!/usr/bin/env python3
"""
Add Full Range Liquidity to sDAI-YES/sDAI Pool

This script adds liquidity across the full price range (MIN_TICK to MAX_TICK)
to the sDAI-YES/sDAI pool using the Uniswap V3 NonFungiblePositionManager.
"""

import os
import sys
import argparse
import json
import time
from decimal import Decimal
from web3 import Web3
from dotenv import load_dotenv
from config.constants import CONTRACT_ADDRESSES, TOKEN_CONFIG, SUSHISWAP_V3_NFPM_ABI, UNISWAP_V3_POOL_ABI, ERC20_ABI
import math

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.futarchy_bot import FutarchyBot

# Load environment variables
load_dotenv()

# Constants
MIN_TICK = -887272  # Minimum possible tick
MAX_TICK = 887272   # Maximum possible tick

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Add liquidity to sDAI-YES/sDAI pool')
    parser.add_argument('--amount_sdai', type=float, default=0.001, help='Amount of sDAI to add (default: 0.001)')
    parser.add_argument('--amount_sdai_yes', type=float, default=0.001, help='Amount of sDAI-YES to add (default: 0.001)')
    parser.add_argument('--balance_ratio', action='store_true', 
                        help='Automatically balance token amounts according to pool ratio')
    parser.add_argument('--tick_range', type=int, default=0,
                        help='Tick range around current price (0 for full range)')
    parser.add_argument('--price-range-01', action='store_true',
                        help='Target the [0,1] price range for sDAI-YES/sDAI ratio')
    parser.add_argument('--try-all-options', action='store_true',
                        help='Try multiple tick ranges in order until one works')
    parser.add_argument('--focus-tick-zero', action='store_true',
                        help='Focus on tick 0 which has the most liquidity')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (do not execute transaction)')
    return parser.parse_args()

def add_liquidity(bot, pool_address, token0_address, token1_address, amount0, amount1, tick_lower=MIN_TICK, tick_upper=MAX_TICK, dry_run=False):
    """Add liquidity to a pool."""
    w3 = bot.w3
    
    # Get token information
    token0_decimals = 18  # Assuming all tokens have 18 decimals (standard for ERC20)
    token1_decimals = 18
    
    # Find token symbols based on known addresses
    if token0_address.lower() == TOKEN_CONFIG["currency"]["address"].lower():
        token0_symbol = "sDAI"
    elif token0_address.lower() == TOKEN_CONFIG["currency"]["yes_address"].lower():
        token0_symbol = "sDAI-YES"
    else:
        token0_symbol = "Token0"
        
    if token1_address.lower() == TOKEN_CONFIG["currency"]["address"].lower():
        token1_symbol = "sDAI"
    elif token1_address.lower() == TOKEN_CONFIG["currency"]["yes_address"].lower():
        token1_symbol = "sDAI-YES"
    else:
        token1_symbol = "Token1"
    
    # Convert human-readable amounts to wei
    amount0_wei = int(amount0 * (10 ** token0_decimals))
    amount1_wei = int(amount1 * (10 ** token1_decimals))
    
    # Get token balances
    token0_contract = w3.eth.contract(address=token0_address, abi=ERC20_ABI)
    token1_contract = w3.eth.contract(address=token1_address, abi=ERC20_ABI)
    
    token0_balance = token0_contract.functions.balanceOf(bot.address).call()
    token1_balance = token1_contract.functions.balanceOf(bot.address).call()
    
    token0_human_balance = token0_balance / (10 ** token0_decimals)
    token1_human_balance = token1_balance / (10 ** token1_decimals)
    
    print(f"\nPool Information:")
    print(f"Pool Address: {pool_address}")
    print(f"Token0: {token0_symbol} ({token0_address})")
    print(f"Token1: {token1_symbol} ({token1_address})")
    
    print(f"\nToken Balances:")
    print(f"{token0_symbol}: {token0_human_balance}")
    print(f"{token1_symbol}: {token1_human_balance}")
    
    print(f"\nLiquidity Addition:")
    print(f"Adding {amount0} {token0_symbol} and {amount1} {token1_symbol} as liquidity")
    if tick_lower == MIN_TICK and tick_upper == MAX_TICK:
        print(f"Full range: {tick_lower} to {tick_upper}")
    else:
        print(f"Concentrated range: {tick_lower} to {tick_upper}")
    
    # Check if we have enough balance
    if token0_balance < amount0_wei:
        print(f"❌ Not enough {token0_symbol} balance. Have {token0_human_balance}, need {amount0}")
        return False
    
    if token1_balance < amount1_wei:
        print(f"❌ Not enough {token1_symbol} balance. Have {token1_human_balance}, need {amount1}")
        return False
    
    if dry_run:
        print("\n🛑 DRY RUN MODE - Transaction will not be executed")
        return True
    
    # Get the NonFungiblePositionManager contract
    nfpm_address = CONTRACT_ADDRESSES["sushiswapNFPM"]
    nfpm_contract = w3.eth.contract(address=nfpm_address, abi=SUSHISWAP_V3_NFPM_ABI)
    
    # Approve tokens for the NonFungiblePositionManager
    print(f"\nApproving {amount0} {token0_symbol} for NFPM...")
    allowance0 = token0_contract.functions.allowance(bot.address, nfpm_address).call()
    
    if allowance0 < amount0_wei:
        tx_hash = bot.approve_token(token0_contract, nfpm_address, amount0_wei)
        if not tx_hash:
            print(f"❌ Failed to approve {token0_symbol}")
            return False
        print(f"✅ {token0_symbol} approved")
    else:
        print(f"✅ {token0_symbol} already approved")
    
    print(f"\nApproving {amount1} {token1_symbol} for NFPM...")
    allowance1 = token1_contract.functions.allowance(bot.address, nfpm_address).call()
    
    if allowance1 < amount1_wei:
        tx_hash = bot.approve_token(token1_contract, nfpm_address, amount1_wei)
        if not tx_hash:
            print(f"❌ Failed to approve {token1_symbol}")
            return False
        print(f"✅ {token1_symbol} approved")
    else:
        print(f"✅ {token1_symbol} already approved")
    
    # Set minimum amounts (allowing 1% slippage)
    amount0_min = int(amount0_wei * 0.99)
    amount1_min = int(amount1_wei * 0.99)
    
    # Set deadline (30 minutes from now)
    deadline = int(time.time() + 1800)
    
    # Create parameters for minting position
    print("\nCreating full-range liquidity position...")
    
    # Mint position
    try:
        # Build transaction
        tx = nfpm_contract.functions.mint(
            token0_address,
            token1_address,
            3000,  # 0.3% fee tier
            tick_lower,
            tick_upper,
            amount0_wei,
            amount1_wei,
            amount0_min,
            amount1_min,
            bot.address,
            deadline
        ).build_transaction({
            'from': bot.address,
            'nonce': w3.eth.get_transaction_count(bot.address),
            'gas': 900000,  # Increased gas limit for complex pool operations
            'gasPrice': w3.eth.gas_price
        })
        
        # Sign transaction
        signed_tx = w3.eth.account.sign_transaction(tx, bot.account.key)
        
        # Send transaction
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        print(f"Transaction submitted - TX Hash: {tx_hash.hex()}")
        
        # Wait for transaction receipt
        print("\nWaiting for transaction confirmation...")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            print(f"✅ Transaction successful - Block: {receipt.blockNumber}")
            
            # Parse the IncreaseLiquidity event to get tokenId and liquidity
            for log in receipt.logs:
                if log['address'].lower() == nfpm_address.lower():
                    try:
                        event = nfpm_contract.events.IncreaseLiquidity().process_log(log)
                        token_id = event.args.tokenId
                        liquidity = event.args.liquidity
                        amount0 = event.args.amount0
                        amount1 = event.args.amount1
                        
                        print(f"\nPosition details:")
                        print(f"NFT Position ID: {token_id}")
                        print(f"Liquidity: {liquidity}")
                        print(f"Token0 Amount: {amount0 / (10 ** token0_decimals)} {token0_symbol}")
                        print(f"Token1 Amount: {amount1 / (10 ** token1_decimals)} {token1_symbol}")
                        return True
                    except:
                        pass
            
            return True
        else:
            print(f"❌ Transaction failed - Status: {receipt.status}")
            
            # Try to get the revert reason
            try:
                # Replay the transaction to get the revert reason
                tx_params = {
                    'from': bot.address,
                    'to': nfpm_address,
                    'data': tx['data'],
                    'gas': tx['gas'],
                    'gasPrice': tx['gasPrice'],
                    'value': tx.get('value', 0)
                }
                
                # This will typically raise an exception with the revert reason
                w3.eth.call(tx_params, receipt.blockNumber)
            except Exception as call_ex:
                print(f"Revert reason: {call_ex}")
            
                # Print more detailed debug information
                print("\nDetailed debug information:")
                print(f"Transaction hash: {tx_hash.hex()}")
                print(f"From: {bot.address}")
                print(f"To: {nfpm_address}")
                print(f"Gas: {tx['gas']}")
                print(f"Gas price: {tx['gasPrice']}")
                print(f"Nonce: {tx['nonce']}")
                print(f"Token0: {token0_address} ({token0_symbol})")
                print(f"Token1: {token1_address} ({token1_symbol})")
                print(f"Amount0: {amount0} {token0_symbol} ({amount0_wei} wei)")
                print(f"Amount1: {amount1} {token1_symbol} ({amount1_wei} wei)")
                print(f"Tick lower: {tick_lower}")
                print(f"Tick upper: {tick_upper}")
                
                # Try with a different error handling approach
                try:
                    # Try extracting the error message from the exception
                    error_msg = str(call_ex)
                    if "reverted" in error_msg:
                        start_idx = error_msg.find("reverted")
                        if start_idx != -1:
                            print(f"Error message: {error_msg[start_idx:]}")
                except:
                    pass
            
            return False
            
    except Exception as e:
        print(f"❌ Error minting position: {e}")
        # Add more diagnostic information
        if hasattr(e, 'args') and len(e.args) > 0:
            print(f"Error details: {e.args[0]}")
        return False

def main():
    """Main function."""
    args = parse_args()
    
    # Initialize the bot
    bot = FutarchyBot(verbose=True)
    w3 = bot.w3
    
    # Get the sDAI-YES/sDAI pool address
    pool_address = CONTRACT_ADDRESSES["sdaiYesPool"]
    
    # Get pool contract
    pool_contract = w3.eth.contract(address=pool_address, abi=UNISWAP_V3_POOL_ABI)
    
    # Get token addresses
    token0_address = pool_contract.functions.token0().call()
    token1_address = pool_contract.functions.token1().call()
    
    # Get SDAI and SDAI-YES addresses
    sdai_address = TOKEN_CONFIG["currency"]["address"]
    sdai_yes_address = TOKEN_CONFIG["currency"]["yes_address"]
    
    # Get current pool price and tick
    tick_lower = MIN_TICK
    tick_upper = MAX_TICK
    
    try:
        slot0 = pool_contract.functions.slot0().call()
        sqrt_price_x96 = slot0[0]
        current_tick = slot0[1]
        
        # Try to get tick spacing, default to 1 if not available
        try:
            tick_spacing = pool_contract.functions.tickSpacing().call()
        except Exception as e:
            print(f"Could not get tick spacing, using default of 1. Error: {e}")
            tick_spacing = 1
        
        print(f"Pool has tick spacing of {tick_spacing}")
        
        # Convert sqrtPriceX96 to price
        price = (sqrt_price_x96 / (2**96))**2
        
        print(f"\nCurrent Pool Price:")
        if token0_address.lower() == sdai_yes_address.lower():
            # If token0 is sDAI-YES, price is sDAI per sDAI-YES
            print(f"Price: {price:.6f} sDAI per sDAI-YES")
            price_token0_in_token1 = price
        else:
            # If token0 is sDAI, price is sDAI-YES per sDAI
            print(f"Price: {price:.6f} sDAI-YES per sDAI")
            price_token0_in_token1 = 1/price
        
        print(f"Current Tick: {current_tick}")
        
        # Define possible tick ranges to try, ordered by preference
        tick_ranges = []
        
        # If focus-tick-zero is used, use ranges around tick 0
        if args.focus_tick_zero:
            print("\nFocusing on tick 0 which contains the pool's liquidity")
            if token0_address.lower() == sdai_yes_address.lower():
                # sDAI-YES is token0, sDAI is token1
                tick_ranges = [
                    {"name": "Around tick 0 (narrow)", "lower": -10, "upper": 10},
                    {"name": "Around tick 0 (medium)", "lower": -50, "upper": 50},
                    {"name": "Around tick 0 (wide)", "lower": -100, "upper": 100}
                ]
            else:
                # sDAI is token0, sDAI-YES is token1
                tick_ranges = [
                    {"name": "Around tick 0 (narrow)", "lower": -10, "upper": 10},
                    {"name": "Around tick 0 (medium)", "lower": -50, "upper": 50},
                    {"name": "Around tick 0 (wide)", "lower": -100, "upper": 100}
                ]
        # If using the try-all-options flag, we'll attempt different ranges
        elif args.try_all_options:
            if token0_address.lower() == sdai_yes_address.lower():
                # sDAI-YES is token0, sDAI is token1
                tick_ranges = [
                    {"name": "Around current price", "lower": current_tick - 10, "upper": current_tick + 10},
                    {"name": "Around tick 0", "lower": -10, "upper": 10},
                    {"name": "Wide around tick 0", "lower": -100, "upper": 100},
                    {"name": "Full range", "lower": MIN_TICK, "upper": MAX_TICK}
                ]
            else:
                # sDAI is token0, sDAI-YES is token1
                tick_ranges = [
                    {"name": "Around current price", "lower": current_tick - 10, "upper": current_tick + 10},
                    {"name": "Around tick 0", "lower": -10, "upper": 10},
                    {"name": "Wide around tick 0", "lower": -100, "upper": 100},
                    {"name": "Full range", "lower": MIN_TICK, "upper": MAX_TICK}
                ]
                
            print("\nWill try multiple tick ranges in order:")
            for i, range_info in enumerate(tick_ranges):
                print(f"{i+1}. {range_info['name']}: {range_info['lower']} to {range_info['upper']}")
            
            # Start with the first option
            tick_lower = tick_ranges[0]["lower"]
            tick_upper = tick_ranges[0]["upper"]
            print(f"\nStarting with option 1: {tick_ranges[0]['name']}")
            
        # Check if we should use the [0,1] price range
        elif args.price_range_01:
            print("\nTargeting the [0,1] price range for sDAI-YES/sDAI ratio")
            
            if token0_address.lower() == sdai_yes_address.lower():
                # sDAI-YES is token0, sDAI is token1
                # For the [0 to 1] range: 0 sDAI per sDAI-YES to 1 sDAI per sDAI-YES
                tick_lower = -100  # Lower bound for price range
                tick_upper = 0     # Upper bound including price of 1.0
            else:
                # sDAI is token0, sDAI-YES is token1
                # For the [0 to 1] range: 0 sDAI-YES per sDAI to 1 sDAI-YES per sDAI
                tick_lower = 0     # Lower bound including price of 1.0
                tick_upper = 100   # Upper bound for price range
            
            print(f"Price range [0,1] corresponds to tick range: {tick_lower} to {tick_upper}")
            
        else:
            # Default to a range around tick 0 as that's where the liquidity is
            tick_lower = -10
            tick_upper = 10
            
            print(f"Using a range around tick 0 which contains most of the liquidity")
            print(f"Tick range: {tick_lower} to {tick_upper}")
        
        # If tick_range argument is provided, override our calculations
        if args.tick_range > 0:
            print(f"\nOverriding with user-specified tick range around current price")
            tick_lower = current_tick - args.tick_range
            tick_upper = current_tick + args.tick_range
            
            print(f"Updated tick range: {tick_lower} to {tick_upper}")
    except Exception as e:
        print(f"Error getting pool price: {e}")
        price_token0_in_token1 = 1.0  # Default to 1:1 if we can't get the price
    
    # Determine which is token0 and which is token1
    if token0_address.lower() == sdai_address.lower():
        # SDAI is token0, sDAI-YES is token1
        amount0 = args.amount_sdai
        amount1 = args.amount_sdai_yes
        print(f"\nToken order: sDAI is token0, sDAI-YES is token1")
        
        # If balance_ratio is enabled, adjust amount1 based on amount0 and the price
        if args.balance_ratio:
            # For a balanced full-range position: amount1 = amount0 * sqrt(price)
            balanced_amount1 = amount0 * (price_token0_in_token1 ** 0.5)
            print(f"Original amount1 (sDAI-YES): {amount1}")
            print(f"Balanced amount1 (sDAI-YES): {balanced_amount1:.6f}")
            
            if args.dry_run:
                print("In dry-run mode, not adjusting amounts")
            else:
                amount1 = balanced_amount1
                print(f"Updated amount1 to {amount1:.6f} sDAI-YES")
    else:
        # sDAI-YES is token0, SDAI is token1
        amount0 = args.amount_sdai_yes
        amount1 = args.amount_sdai
        print(f"\nToken order: sDAI-YES is token0, sDAI is token1")
        
        # If balance_ratio is enabled, adjust amount1 based on amount0 and the price
        if args.balance_ratio:
            # For a balanced full-range position: amount1 = amount0 * sqrt(price)
            balanced_amount1 = amount0 * (price_token0_in_token1 ** 0.5)
            print(f"Original amount1 (sDAI): {amount1}")
            print(f"Balanced amount1 (sDAI): {balanced_amount1:.6f}")
            
            if args.dry_run:
                print("In dry-run mode, not adjusting amounts")
            else:
                amount1 = balanced_amount1
                print(f"Updated amount1 to {amount1:.6f} sDAI")
    
    # Add liquidity
    success = False
    
    if args.focus_tick_zero and not args.dry_run:
        # Try multiple ranges around tick 0 in order until one works
        tick_ranges = [
            {"name": "Around tick 0 (narrow)", "lower": -10, "upper": 10},
            {"name": "Around tick 0 (medium)", "lower": -50, "upper": 50},
            {"name": "Around tick 0 (wide)", "lower": -100, "upper": 100}
        ]
        
        for i, range_info in enumerate(tick_ranges):
            tick_lower = range_info["lower"]
            tick_upper = range_info["upper"]
            print(f"\nTrying option {i+1}: {range_info['name']}")
            print(f"Tick range: {tick_lower} to {tick_upper}")
            
            success = add_liquidity(
                bot, 
                pool_address, 
                token0_address, 
                token1_address, 
                amount0, 
                amount1,
                tick_lower,
                tick_upper,
                dry_run=args.dry_run
            )
            
            if success:
                print(f"\n✅ Successfully added liquidity with tick range: {tick_lower} to {tick_upper}")
                break
            else:
                print(f"\n❌ Failed to add liquidity with tick range: {tick_lower} to {tick_upper}")
                if i < len(tick_ranges) - 1:
                    print(f"Will try next option...")
    elif args.try_all_options and not args.dry_run:
        # Try multiple ranges in order until one works
        for i, range_info in enumerate(tick_ranges):
            if i > 0:  # Skip first one as we already tried it
                tick_lower = range_info["lower"]
                tick_upper = range_info["upper"]
                print(f"\n\nTrying option {i+1}: {range_info['name']}")
                print(f"Tick range: {tick_lower} to {tick_upper}")
            
            success = add_liquidity(
                bot, 
                pool_address, 
                token0_address, 
                token1_address, 
                amount0, 
                amount1,
                tick_lower,
                tick_upper,
                dry_run=args.dry_run
            )
            
            if success:
                print(f"\n✅ Successfully added liquidity with tick range: {tick_lower} to {tick_upper}")
                break
            else:
                print(f"\n❌ Failed to add liquidity with tick range: {tick_lower} to {tick_upper}")
                if i < len(tick_ranges) - 1:
                    print(f"Will try next option...")
    else:
        # Just try once with the selected range
        success = add_liquidity(
            bot, 
            pool_address, 
            token0_address, 
            token1_address, 
            amount0, 
            amount1,
            tick_lower,
            tick_upper,
            dry_run=args.dry_run
        )
    
    if success and not args.dry_run:
        # Show updated balances
        balances = bot.get_balances()
        bot.print_balances(balances)

if __name__ == "__main__":
    main() 