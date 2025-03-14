#!/usr/bin/env python3
"""
Test script for swapping waGNO to sDAI.
This script tests the swap functionality without requiring user input.
"""

import os
import sys
import argparse

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from menu import FutarchyMenu

def main():
    """Test the waGNO to sDAI swap functionality."""
    parser = argparse.ArgumentParser(description='Test waGNO to sDAI swap functionality')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Dry run (do not send transaction)')
    parser.add_argument('--amount', '-a', type=float, default=0.0001, help='Amount to swap (in waGNO)')
    parser.add_argument('--min-amount-out', '-m', type=float, help='Minimum amount to receive (in sDAI)')
    args = parser.parse_args()
    
    print(f"=== Testing waGNO to sDAI Swap (Amount: {args.amount} waGNO) ===")
    
    # Initialize the menu
    menu = FutarchyMenu(verbose=args.verbose)
    
    # Check balances first
    print("\nChecking current balances...")
    balances = menu.refresh_balances()
    
    if balances:
        wagno_balance = balances['wagno']
        if wagno_balance < args.amount:
            print(f"❌ Insufficient waGNO balance. Required: {args.amount}, Available: {wagno_balance}")
            return 1
        
        print(f"✅ waGNO balance is sufficient: {wagno_balance}")
    
    # Check Permit2 status (not strictly necessary for waGNO -> sDAI, but good to check)
    print("\nChecking Permit2 status...")
    menu.check_permit2_status()
    
    if args.dry_run:
        print(f"\n🔍 DRY RUN: Would swap {args.amount} waGNO for sDAI")
        return 0
    
    # Execute the swap
    print(f"\nSwapping {args.amount} waGNO for sDAI...")
    result = menu.swap_wagno_to_sdai(args.amount, args.min_amount_out)
    
    if result:
        print("\n✅ waGNO to sDAI swap test completed successfully")
        
        # Check updated balances
        print("\nChecking updated balances...")
        updated_balances = menu.refresh_balances()
        
        return 0
    else:
        print("\n❌ waGNO to sDAI swap test failed")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 