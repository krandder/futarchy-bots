#!/usr/bin/env python3
"""
Test script for creating Permit2 authorizations for conditional tokens.
This script tests the Permit2 creation functionality for conditional tokens.
"""

import os
import sys
import argparse

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.futarchy_bot import FutarchyBot
from config.constants import TOKEN_CONFIG, CONTRACT_ADDRESSES
from exchanges.balancer.permit2 import BalancerPermit2Handler

def main():
    """Test the Permit2 creation functionality for conditional tokens."""
    parser = argparse.ArgumentParser(description='Test Permit2 creation for conditional tokens')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Dry run (do not send transaction)')
    parser.add_argument('--amount', '-a', type=float, default=0.1, help='Amount to authorize')
    parser.add_argument('--expiration', '-e', type=int, default=24, help='Expiration in hours')
    parser.add_argument('--token', '-t', choices=['sdai_yes', 'gno_yes', 'gno_no'], default='sdai_yes', 
                        help='Token to create permit for')
    args = parser.parse_args()
    
    print(f"=== Testing Permit2 Creation for {args.token.upper()} (Amount: {args.amount}, Expiration: {args.expiration} hours) ===")
    
    # Initialize the bot
    bot = FutarchyBot(verbose=args.verbose)
    
    # Get token address based on the selected token
    if args.token == 'sdai_yes':
        token_address = TOKEN_CONFIG["currency"]["yes_address"]
        token_name = "sDAI YES"
    elif args.token == 'gno_yes':
        token_address = TOKEN_CONFIG["company"]["yes_address"]
        token_name = "GNO YES"
    elif args.token == 'gno_no':
        token_address = TOKEN_CONFIG["company"]["no_address"]
        token_name = "GNO NO"
    
    # Get token contract
    token_contract = bot.get_token_contract(token_address)
    
    # Check token balance
    token_balance = token_contract.functions.balanceOf(bot.address).call()
    token_balance_eth = bot.w3.from_wei(token_balance, 'ether')
    print(f"\n{token_name} balance: {token_balance_eth}")
    
    # Check if token is approved for Permit2
    permit2_address = CONTRACT_ADDRESSES["permit2"]
    allowance = token_contract.functions.allowance(bot.address, permit2_address).call()
    
    print(f"\n=== Current Approval Status ===")
    print(f"{token_name} -> Permit2: {'✅ APPROVED' if allowance > 0 else '❌ NOT APPROVED'}")
    if allowance > 0:
        print(f"  Allowance: {bot.w3.from_wei(allowance, 'ether')}")
    
    # If token is not approved for Permit2, approve it
    if allowance == 0:
        if args.dry_run:
            print(f"\n🔍 DRY RUN: Would approve {token_name} for Permit2")
        else:
            print(f"\nApproving {token_name} for Permit2...")
            max_amount = 2**256 - 1
            tx_hash = bot.approve_token(token_contract, permit2_address, max_amount)
            if tx_hash:
                print(f"✅ {token_name} approved for Permit2. Transaction: {tx_hash}")
            else:
                print(f"❌ Failed to approve {token_name} for Permit2")
                return 1
    
    # Create Permit2 authorization for SushiSwap
    sushiswap_address = CONTRACT_ADDRESSES["sushiswap"]
    
    if args.dry_run:
        print(f"\n🔍 DRY RUN: Would create Permit2 authorization for {args.amount} {token_name} with {args.expiration} hour expiration")
        return 0
    
    print(f"\nCreating Permit2 authorization for SushiSwap (amount: {args.amount} {token_name}, expiration: {args.expiration} hours)...")
    
    # Create the permit using the permit2 handler
    permit2_handler = BalancerPermit2Handler(bot, verbose=args.verbose)
    
    # Create the permit
    result = permit2_handler.create_permit(
        token_address=token_address,
        spender_address=sushiswap_address,
        amount=args.amount,
        expiration_hours=args.expiration
    )
    
    if result:
        print(f"\n✅ Permit2 authorization created for {token_name}. Transaction: {result}")
        print(f"\n✅ Conditional token Permit2 creation test completed successfully")
        return 0
    else:
        print(f"\n❌ Failed to create Permit2 authorization for {token_name}")
        print(f"\n❌ Conditional token Permit2 creation test failed")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 