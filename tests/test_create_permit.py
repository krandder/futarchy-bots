#!/usr/bin/env python3
"""
Test script for creating a Permit2 authorization.
This script tests the Permit2 creation functionality without requiring user input.
"""

import os
import sys
import argparse

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from menu import FutarchyMenu

def main():
    """Test the Permit2 creation functionality."""
    parser = argparse.ArgumentParser(description='Test Permit2 creation functionality')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Dry run (do not send transaction)')
    parser.add_argument('--amount', '-a', type=float, default=0.1, help='Amount to authorize (in sDAI)')
    parser.add_argument('--expiration', '-e', type=int, default=24, help='Expiration in hours')
    args = parser.parse_args()
    
    print(f"=== Testing Permit2 Creation (Amount: {args.amount} sDAI, Expiration: {args.expiration} hours) ===")
    
    # Initialize the menu
    menu = FutarchyMenu(verbose=args.verbose)
    
    # Check current Permit2 status first
    print("\nChecking current Permit2 status...")
    permit_status = menu.check_permit2_status()
    
    if permit_status:
        sdai_batchrouter = permit_status['sdai_batchrouter']
        if not sdai_batchrouter['needs_permit']:
            print("✅ Permit2 authorization already exists for BatchRouter")
            if sdai_batchrouter['permit2_allowance']:
                print(f"Current allowance: {menu.bot.w3.from_wei(sdai_batchrouter['permit2_allowance']['amount'], 'ether'):.6f}")
                print(f"Expiration: {sdai_batchrouter['permit2_allowance']['expiration']}")
            return 0
    
    # Check if sDAI is approved for Permit2
    if permit_status and not permit_status['sdai_permit2']['token_approved_for_permit2']:
        print("❌ sDAI is not approved for Permit2. Please run test_approve_sdai.py first.")
        return 1
    
    if args.dry_run:
        print(f"\n🔍 DRY RUN: Would create Permit2 authorization for {args.amount} sDAI with {args.expiration} hour expiration")
        return 0
    
    # Create Permit2 authorization
    print("\nCreating Permit2 authorization...")
    result = menu.create_permit_for_batchrouter(args.amount, args.expiration)
    
    if result:
        print("\n✅ Permit2 creation test completed successfully")
        return 0
    else:
        print("\n❌ Permit2 creation test failed")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 