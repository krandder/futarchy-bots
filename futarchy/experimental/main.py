#!/usr/bin/env python3
"""
Futarchy Trading Bot - Experimental Main Entry Point

This module is currently in EXPERIMENTAL status.
New implementation using modular configuration and core components.
"""

import sys
import os
import argparse
from decimal import Decimal
import time
from web3 import Web3
from dotenv import load_dotenv

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import experimental config
from futarchy.experimental.config import (
    # Network
    DEFAULT_RPC_URLS,
    COWSWAP_API_URL,
    
    # Contracts
    CONTRACT_ADDRESSES,
    CONTRACT_WARNINGS,
    is_contract_safe,
    get_contract_warning,
    
    # Pools
    POOL_CONFIG_YES,
    POOL_CONFIG_NO,
    BALANCER_CONFIG,
    MIN_SQRT_RATIO,
    MAX_SQRT_RATIO,
    UNISWAP_V3_CONFIG,
    
    # Tokens
    TOKEN_CONFIG,
    DEFAULT_SWAP_CONFIG,
    DEFAULT_PERMIT_CONFIG,
    get_token_info,
    get_token_decimals,
    format_token_amount,
    get_base_token
)

# Import experimental ABIs
from futarchy.experimental.config.abis import (
    ERC20_ABI,
    UNISWAP_V3_POOL_ABI,
    UNISWAP_V3_PASSTHROUGH_ROUTER_ABI,
    SUSHISWAP_V3_ROUTER_ABI,
    SUSHISWAP_V3_NFPM_ABI,
    BALANCER_VAULT_ABI,
    BALANCER_POOL_ABI,
    BALANCER_BATCH_ROUTER_ABI,
    FUTARCHY_ROUTER_ABI,
    SDAI_RATE_PROVIDER_ABI,
    WXDAI_ABI,
    SDAI_DEPOSIT_ABI,
    WAGNO_ABI,
    PERMIT2_ABI
)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Futarchy Trading Bot (Experimental)')
    
    # General options
    parser.add_argument('--rpc', type=str, help='RPC URL for Gnosis Chain')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    
    # Command mode
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Debug command
    debug_parser = subparsers.add_parser('debug', help='Run in debug mode with additional output')
    
    return parser.parse_args()

def main():
    """Main entry point"""
    # Load environment variables
    load_dotenv()
    
    # Parse arguments
    args = parse_args()
    
    # Initialize Web3
    rpc_url = args.rpc or os.getenv('RPC_URL') or DEFAULT_RPC_URLS[0]
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not w3.is_connected():
        print(f"❌ Failed to connect to RPC: {rpc_url}")
        sys.exit(1)
    
    print(f"✅ Connected to network: {w3.eth.chain_id}")
    
    if args.command == 'debug':
        print("\n🔍 Debug Information:")
        print(f"RPC URL: {rpc_url}")
        print(f"Chain ID: {w3.eth.chain_id}")
        print(f"Latest block: {w3.eth.block_number}")
        
        # Print some config info
        print("\n📝 Configuration:")
        print(f"SDAI Address: {TOKEN_CONFIG['currency']['address']}")
        print(f"GNO Address: {TOKEN_CONFIG['company']['address']}")
        print(f"YES Pool: {POOL_CONFIG_YES['address']}")
        print(f"NO Pool: {POOL_CONFIG_NO['address']}")
        
        return
    
    print("No command specified. Use --help to see available commands.")

if __name__ == '__main__':
    main() 