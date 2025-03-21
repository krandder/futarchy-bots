"""
Web3 utilities for development scripts.
Simplified version of the experimental web3_utils.py, containing only what's needed for GNO wrapping/unwrapping.
"""

import os
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

def setup_web3_connection(rpc_url=None):
    """Set up a Web3 connection with appropriate middleware for Gnosis Chain."""
    load_dotenv()
    
    # Use provided RPC URL or get from environment
    if not rpc_url:
        rpc_url = os.getenv('GNOSIS_RPC_URL')
    
    # If no URL from env, use default
    if not rpc_url:
        rpc_url = 'https://rpc.gnosischain.com'
    
    # Create Web3 instance
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    # Add PoA middleware for Gnosis Chain
    from web3.middleware import geth_poa_middleware
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    
    if w3.is_connected():
        print(f"✅ Connected to Gnosis Chain (Chain ID: {w3.eth.chain_id})")
        print(f"📊 Latest block: {w3.eth.block_number}")
    else:
        raise Exception("Failed to connect to Gnosis Chain")
    
    return w3

def get_account_from_private_key():
    """Get account from private key in environment variables."""
    load_dotenv()
    
    private_key = os.getenv('PRIVATE_KEY')
    if not private_key:
        raise ValueError("No private key found. Set the PRIVATE_KEY environment variable.")
    
    account = Account.from_key(private_key)
    print(f"🔑 Using account: {account.address}")
    return account, account.address

def get_raw_transaction(signed_tx):
    """Get raw transaction bytes from a signed transaction."""
    return signed_tx.rawTransaction  # Web3.py v6+ always uses rawTransaction 