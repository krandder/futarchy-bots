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
    parser = argparse.ArgumentParser(description="Test swapping sDAI YES tokens to GNO NO tokens")
    parser.add_argument("--amount", type=float, default=0.0001, help="Amount to swap (default: 0.0001)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()
    
    print(f"=== Testing sDAI YES to GNO NO Swap (Amount: {args.amount} sDAI YES) ===")
    
    # Initialize the bot
    bot = FutarchyBot(verbose=args.verbose)
    
    # Check current balances
    print("\nChecking current balances...\n")
    balances = bot.get_balances()
    
    # Check if we have enough sDAI YES tokens
    sdai_yes_balance = Decimal(balances["currency"]["yes"])
    print(f"✅ sDAI YES balance is sufficient: {sdai_yes_balance}")
    
    if sdai_yes_balance < Decimal(args.amount):
        print(f"❌ Insufficient sDAI YES balance. Required: {args.amount}, Available: {sdai_yes_balance}")
        return
    
    # Execute the swap
    print(f"\nSwapping {args.amount} sDAI YES for GNO NO...")
    
    # token_type='company' means GNO, is_buy=True means buying GNO tokens, is_yes_token=False means NO tokens
    result = bot.execute_swap(token_type='company', is_buy=True, amount=args.amount, is_yes_token=False)
    
    if result:
        print(f"\n✅ sDAI YES to GNO NO swap test completed successfully")
    else:
        print(f"\n❌ sDAI YES to GNO NO swap test failed")
    
    # Check updated balances
    print("\nChecking updated balances...\n")
    bot.get_balances()

if __name__ == "__main__":
    main() 