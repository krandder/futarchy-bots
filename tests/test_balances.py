#!/usr/bin/env python3
"""
Test script for checking token balances.
This script tests the balance checking functionality without requiring user input.
"""

import os
import sys
import argparse

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from menu import FutarchyMenu

def main():
    """Test the balance checking functionality."""
    parser = argparse.ArgumentParser(description='Test balance checking functionality')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    args = parser.parse_args()
    
    print("=== Testing Balance Checking ===")
    
    # Initialize the menu
    menu = FutarchyMenu(verbose=args.verbose)
    
    # Check balances
    balances = menu.refresh_balances()
    
    if balances:
        print("\n=== Balance Test Results ===")
        print(f"sDAI: {balances['sdai']:.6f}")
        print(f"waGNO: {balances['wagno']:.6f}")
        print(f"XDAI: {balances['xdai']:.6f}")
        
        # Check conditional tokens
        if any(balances['conditional'].values()):
            print("\nConditional Tokens:")
            for token, balance in balances['conditional'].items():
                if balance > 0:
                    print(f"{token}: {balance:.6f}")
        
        print("\n✅ Balance check test completed successfully")
        return 0
    else:
        print("\n❌ Balance check test failed")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 