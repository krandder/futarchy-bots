#!/usr/bin/env python3
import os
import sys
import argparse
from decimal import Decimal

# Add the parent directory to the path so we can import the core module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.futarchy_bot import FutarchyBot
from config.constants import TOKEN_CONFIG

def main():
    parser = argparse.ArgumentParser(description="Test swapping GNO NO tokens to sDAI YES tokens")
    parser.add_argument("--amount", type=float, default=0.0001, help="Amount to swap (default: 0.0001)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()
    
    print(f"=== Testing GNO NO to sDAI YES Swap (Amount: {args.amount} GNO NO) ===")
    
    # Initialize the bot
    bot = FutarchyBot(verbose=args.verbose)
    
    # Check current balances
    print("\nChecking current balances...\n")
    balances = bot.get_balances()
    
    # Check if we have enough GNO NO tokens
    gno_no_balance = Decimal(balances["company"]["no"])
    print(f"✅ GNO NO balance is sufficient: {gno_no_balance}")
    
    if gno_no_balance < Decimal(args.amount):
        print(f"❌ Insufficient GNO NO balance. Required: {args.amount}, Available: {gno_no_balance}")
        return
    
    # Execute the swap
    print(f"\nSwapping {args.amount} GNO NO for sDAI YES...")
    
    # Get token addresses
    token_in = TOKEN_CONFIG["company"]["no_address"]  # GNO NO
    token_out = TOKEN_CONFIG["currency"]["yes_address"]  # SDAI YES
    
    # Convert amount to Wei
    amount_wei = bot.w3.to_wei(args.amount, 'ether')
    
    result = bot.execute_swap(token_in=token_in, token_out=token_out, amount=amount_wei)
    
    if result:
        print(f"\n✅ GNO NO to sDAI YES swap test completed successfully")
    else:
        print(f"\n❌ GNO NO to sDAI YES swap test failed")
    
    # Check updated balances
    print("\nChecking updated balances...\n")
    bot.get_balances()

if __name__ == "__main__":
    main() 