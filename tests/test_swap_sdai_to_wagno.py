#!/usr/bin/env python3
"""
Test script for swapping sDAI to waGNO.
This script tests the swap functionality without requiring user input.
"""

import os
import sys
import argparse

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from menu import FutarchyMenu

def main():
    """Test the sDAI to waGNO swap functionality."""
    parser = argparse.ArgumentParser(description='Test sDAI to waGNO swap functionality')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Dry run (do not send transaction)')
    parser.add_argument('--amount', '-a', type=float, default=0.0001, help='Amount to swap (in sDAI)')
    parser.add_argument('--min-amount-out', '-m', type=float, help='Minimum amount to receive (in waGNO)')
    args = parser.parse_args()
    
    print(f"=== Testing sDAI to waGNO Swap (Amount: {args.amount} sDAI) ===")
    
    # Initialize the menu
    menu = FutarchyMenu(verbose=args.verbose)
    
    # Check balances first
    print("\nChecking current balances...")
    balances = menu.refresh_balances()
    
    if balances:
        sdai_balance = balances['sdai']
        if sdai_balance < args.amount:
            print(f"❌ Insufficient sDAI balance. Required: {args.amount}, Available: {sdai_balance}")
            return 1
        
        print(f"✅ sDAI balance is sufficient: {sdai_balance}")
    
    # Check Permit2 status
    print("\nChecking Permit2 status...")
    permit_status = menu.check_permit2_status()
    
    if permit_status:
        # Check if we need to create a Permit2 authorization
        sdai_batchrouter = permit_status['sdai_batchrouter']
        if sdai_batchrouter['needs_permit']:
            print("⚠️ Permit2 authorization needed for BatchRouter")
            
            # Check if sDAI is approved for Permit2
            sdai_permit2 = permit_status['sdai_permit2']
            if not sdai_permit2['token_approved_for_permit2']:
                print("❌ sDAI is not approved for Permit2. Please run test_approve_sdai.py first.")
                return 1
            
            if not args.dry_run:
                print("\nCreating Permit2 authorization...")
                permit_result = menu.create_permit_for_batchrouter(args.amount * 10)  # Create permit for 10x the swap amount
                if not permit_result:
                    print("❌ Failed to create Permit2 authorization")
                    return 1
    
    if args.dry_run:
        print(f"\n🔍 DRY RUN: Would swap {args.amount} sDAI for waGNO")
        return 0
    
    # Execute the swap
    print(f"\nSwapping {args.amount} sDAI for waGNO...")
    result = menu.swap_sdai_to_wagno(args.amount, args.min_amount_out)
    
    if result:
        print("\n✅ sDAI to waGNO swap test completed successfully")
        
        # Check updated balances
        print("\nChecking updated balances...")
        updated_balances = menu.refresh_balances()
        
        return 0
    else:
        print("\n❌ sDAI to waGNO swap test failed")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 