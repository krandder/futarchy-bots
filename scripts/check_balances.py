#!/usr/bin/env python3
"""
Script to check token balances for a given address.

Uses the TokenBalanceChecker to display balances of all configured tokens.
"""

import os
import sys
import argparse
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
from futarchy.development.config.abis.erc20 import ERC20_ABI
from futarchy.development.config.tokens import TOKEN_CONFIG
from futarchy.balance_checker import get_balances, get_address_from_env

def get_address_from_env():
    """Get address from private key in .env file."""
    load_dotenv()
    private_key = os.getenv('PRIVATE_KEY')
    if not private_key:
        return None
    
    account = Account.from_key(private_key)
    return account.address

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Check token balances')
    parser.add_argument('--address', type=str, help='Address to check balances for (defaults to address from PRIVATE_KEY in .env)')
    parser.add_argument('--rpc', type=str, 
                       default='https://gnosis-mainnet.public.blastapi.io',
                       help='RPC URL for Gnosis Chain')
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    
    # Get address from args, env var, or private key
    address = args.address or os.environ.get('ADDRESS') or get_address_from_env()
    if not address:
        print("❌ No address provided. Either:")
        print("  1. Use --address command line argument")
        print("  2. Set ADDRESS environment variable")
        print("  3. Set PRIVATE_KEY in .env file")
        sys.exit(1)
    
    try:
        # Initialize Web3
        w3 = Web3(Web3.HTTPProvider(args.rpc))
        if not w3.is_connected():
            print("❌ Failed to connect to RPC endpoint")
            sys.exit(1)
            
        print(f"Connected to network: {args.rpc}")
        print(f"Checking balances for: {address}")
        
        # Initialize balance checker
        checker = TokenBalanceChecker(w3, TOKEN_CONFIG, ERC20_ABI)
        
        # Get and print balances
        try:
            balances = checker.get_balances(address)
            checker.print_balances(balances)
        except Exception as e:
            print(f"❌ Error getting balances: {e}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 