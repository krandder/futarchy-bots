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
    parser = argparse.ArgumentParser(description="Test swapping GNO YES tokens to sDAI YES tokens")
    parser.add_argument("--amount", type=float, default=0.0001, help="Amount to swap (default: 0.0001)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()
    
    print(f"=== Testing GNO YES to sDAI YES Swap (Amount: {args.amount} GNO YES) ===")
    
    # Initialize the bot
    bot = FutarchyBot(verbose=args.verbose)
    
    # Check current balances
    print("\nChecking current balances...\n")
    balances = bot.get_balances()
    
    # Check if we have enough GNO YES tokens
    gno_yes_balance = Decimal(balances["company"]["yes"])
    print(f"✅ GNO YES balance is sufficient: {gno_yes_balance}")
    
    if gno_yes_balance < Decimal(args.amount):
        print(f"❌ Insufficient GNO YES balance. Required: {args.amount}, Available: {gno_yes_balance}")
        return
    
    # Execute the swap
    print(f"\nSwapping {args.amount} GNO YES for sDAI YES...")
    
    # token_type='company' means GNO, is_buy=False means selling GNO tokens, is_yes_token=True means YES tokens
    result = bot.execute_swap(token_type='company', is_buy=False, amount=args.amount, is_yes_token=True)
    
    if result:
        print(f"\n✅ GNO YES to sDAI YES swap test completed successfully")
    else:
        print(f"\n❌ GNO YES to sDAI YES swap test failed")
    
    # Check updated balances
    print("\nChecking updated balances...\n")
    bot.get_balances()

if __name__ == "__main__":
    main() 