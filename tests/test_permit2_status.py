#!/usr/bin/env python3
"""
Test script for checking Permit2 authorization status.
This script tests the Permit2 status checking functionality without requiring user input.
"""

import os
import sys
import argparse

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from menu import FutarchyMenu

def main():
    """Test the Permit2 status checking functionality."""
    parser = argparse.ArgumentParser(description='Test Permit2 status checking functionality')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    args = parser.parse_args()
    
    print("=== Testing Permit2 Status Checking ===")
    
    # Initialize the menu
    menu = FutarchyMenu(verbose=args.verbose)
    
    # Check Permit2 status
    permit_status = menu.check_permit2_status()
    
    if permit_status:
        print("\n=== Permit2 Status Test Results ===")
        
        # Check sDAI -> Permit2 status
        sdai_permit2 = permit_status['sdai_permit2']
        print(f"sDAI -> Permit2: {'✅ APPROVED' if sdai_permit2['token_approved_for_permit2'] else '❌ NOT APPROVED'}")
        
        # Check sDAI -> BatchRouter status
        sdai_batchrouter = permit_status['sdai_batchrouter']
        print(f"sDAI -> BatchRouter: {'✅ APPROVED' if not sdai_batchrouter['needs_permit'] else '❌ NOT APPROVED'}")
        
        if not sdai_batchrouter['needs_permit'] and sdai_batchrouter['permit2_allowance']:
            print(f"  Allowance: {menu.bot.w3.from_wei(sdai_batchrouter['permit2_allowance']['amount'], 'ether'):.2f}")
            print(f"  Valid: {'Yes' if sdai_batchrouter['permit2_allowance']['is_valid'] else 'No'}")
            print(f"  Sufficient: {'Yes' if sdai_batchrouter['permit2_allowance']['is_sufficient'] else 'No'}")
        
        print("\n✅ Permit2 status check test completed successfully")
        return 0
    else:
        print("\n❌ Permit2 status check test failed")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 