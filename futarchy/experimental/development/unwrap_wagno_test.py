#!/usr/bin/env python3
"""
Development script for testing waGNO to GNO unwrapping functionality.
"""

import os
import sys

# Add the development directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from utils.web3_utils import setup_web3_connection, get_account_from_private_key
from gno_handler import GnoHandler

def main():
    """Main function to test waGNO to GNO unwrapping."""
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
    
    # Amount of waGNO to unwrap (can be adjusted)
    amount_to_unwrap = 0.002996
    
    print(f"\n🔄 Attempting to unwrap {amount_to_unwrap} waGNO to GNO...")
    
    # Execute the unwrap
    result = handler.unwrap_wagno_to_gno(amount_to_unwrap)
    
    if result:
        print(f"\n✅ Unwrap transaction successful!")
        print(f"Transaction hash: {result}")
        print(f"View on GnosisScan: https://gnosisscan.io/tx/{result}")
        
        print("\n=== Final Balances ===")
        handler.print_balances()
    else:
        print("\n❌ Unwrap transaction failed!")

if __name__ == "__main__":
    main() 