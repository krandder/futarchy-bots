#!/usr/bin/env python3
"""
Test script for approving sDAI for Permit2.
This script tests the token approval functionality without requiring user input.
"""

import os
import sys
import argparse

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from menu import FutarchyMenu

def main():
    """Test the sDAI approval functionality."""
    parser = argparse.ArgumentParser(description='Test sDAI approval functionality')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Dry run (do not send transaction)')
    args = parser.parse_args()
    
    print("=== Testing sDAI Approval for Permit2 ===")
    
    # Initialize the menu
    menu = FutarchyMenu(verbose=args.verbose)
    
    # Check current Permit2 status first
    print("\nChecking current Permit2 status...")
    permit_status = menu.check_permit2_status()
    
    if permit_status:
        sdai_permit2 = permit_status['sdai_permit2']
        if sdai_permit2['token_approved_for_permit2']:
            print("✅ sDAI is already approved for Permit2")
            print(f"Current allowance: {menu.bot.w3.from_wei(sdai_permit2['token_balance'], 'ether'):.6f}")
            return 0
    
    if args.dry_run:
        print("\n🔍 DRY RUN: Would approve sDAI for Permit2")
        return 0
    
    # Approve sDAI for Permit2
    print("\nApproving sDAI for Permit2...")
    result = menu.approve_sdai_for_permit2()
    
    if result:
        print("\n✅ sDAI approval test completed successfully")
        return 0
    else:
        print("\n❌ sDAI approval test failed")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 