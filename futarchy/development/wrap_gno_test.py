#!/usr/bin/env python3
"""
Development script for testing GNO to waGNO wrapping functionality.
"""

import os
import sys

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from futarchy.development.utils.web3_utils import setup_web3_connection, get_account_from_private_key
from futarchy.development.gno_handler import GnoHandler

def main():
    """Main function to test GNO to waGNO wrapping."""
    # Initialize Web3 and account
    w3 = setup_web3_connection()
    account, _ = get_account_from_private_key()
    
    if not account:
        return
    
    # Initialize handler
    handler = GnoHandler(w3, account)
    
    # Print initial balances
    print("\n=== Initial Balances ===")
    handler.print_balances()
    
    # Amount of GNO to wrap (can be adjusted)
    amount_to_wrap = 0.003
    
    print(f"\n🔄 Attempting to wrap {amount_to_wrap} GNO to waGNO...")
    
    # Execute the wrap
    result = handler.wrap_gno_to_wagno(amount_to_wrap)
    
    if result:
        print(f"\n✅ Wrap transaction successful!")
        print(f"Transaction hash: {result}")
        print(f"View on GnosisScan: https://gnosisscan.io/tx/{result}")
        
        print("\n=== Final Balances ===")
        handler.print_balances()
    else:
        print("\n❌ Wrap transaction failed!")

if __name__ == "__main__":
    main() 