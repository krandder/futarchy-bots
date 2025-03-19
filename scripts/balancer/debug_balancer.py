#!/usr/bin/env python3
"""
Debug script for Balancer V3 swaps using the Router V2 contract
"""

import os
import json
from web3 import Web3
from eth_account import Account
from web3.middleware import geth_poa_middleware
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).resolve().parent.parent.parent
import sys
sys.path.append(str(project_root))

from config.constants import (
    TOKEN_CONFIG, BALANCER_CONFIG, CONTRACT_ADDRESSES,
    BALANCER_VAULT_ABI, ERC20_ABI
)

def main():
    # Connect to Gnosis Chain
    w3 = Web3(Web3.HTTPProvider('https://gnosis-mainnet.public.blastapi.io'))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    
    # Check connection
    if not w3.is_connected():
        print("Failed to connect to Gnosis Chain")
        return
    
    print(f"Connected to Gnosis Chain (Chain ID: {w3.eth.chain_id})")
    
    # Load account from private key
    private_key = os.environ.get('PRIVATE_KEY')
    if not private_key:
        print("No private key found in environment variables")
        return
        
    account = Account.from_key(private_key)
    print(f"Using account: {account.address}")
    
    # Load contract addresses
    vault_address = w3.to_checksum_address(CONTRACT_ADDRESSES['balancerVault'])
    sdai_address = w3.to_checksum_address(CONTRACT_ADDRESSES['baseCurrencyToken'])
    wagno_address = w3.to_checksum_address(CONTRACT_ADDRESSES['wagno'])
    pool_id = BALANCER_CONFIG['pool_id']
    
    print(f"\nContract Addresses:")
    print(f"Vault: {vault_address}")
    print(f"sDAI: {sdai_address}")
    print(f"waGNO: {wagno_address}")
    print(f"Pool ID: {pool_id}")
    
    # Create contract instances
    vault = w3.eth.contract(address=vault_address, abi=BALANCER_VAULT_ABI)
    sdai_token = w3.eth.contract(address=sdai_address, abi=ERC20_ABI)
    wagno_token = w3.eth.contract(address=wagno_address, abi=ERC20_ABI)
    
    # Check balances
    sdai_balance = sdai_token.functions.balanceOf(account.address).call()
    wagno_balance = wagno_token.functions.balanceOf(account.address).call()
    
    print(f"\nCurrent Balances:")
    print(f"sDAI: {w3.from_wei(sdai_balance, 'ether')}")
    print(f"waGNO: {w3.from_wei(wagno_balance, 'ether')}")
    
    # Check pool tokens and balances
    try:
        pool_info = vault.functions.getPoolTokens(pool_id).call()
        print(f"\nPool Info:")
        print(f"Pool Tokens: {pool_info[0]}")
        print(f"Pool Balances: {[w3.from_wei(b, 'ether') for b in pool_info[1]]}")
        print(f"Last Change Block: {pool_info[2]}")
        
        # Try to query expected output for 1 sDAI
        try:
            amount_in = w3.to_wei(1, 'ether')  # 1 sDAI
            expected_out = vault.functions.querySwap(
                pool_id,
                sdai_address,
                wagno_address,
                amount_in
            ).call()
            print(f"\nExpected output for 1 sDAI: {w3.from_wei(expected_out, 'ether')} waGNO")
        except Exception as e:
            print(f"Warning: Could not query expected output: {e}")
            
    except Exception as e:
        print(f"Warning: Could not get pool info: {e}")

if __name__ == "__main__":
    main()