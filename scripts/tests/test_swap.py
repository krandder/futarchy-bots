#!/usr/bin/env python3
"""
Test script for performing a small swap in the GNO-YES/sDAI-YES pool using the Uniswap V3 SDK.
"""

import os
import sys
import json
import requests
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Load environment variables
load_dotenv()

# Constants
UNISWAP_V3_BRIDGE_URL = "http://localhost:3001"
RPC_URL = os.getenv("RPC_URL", "https://rpc.ankr.com/gnosis")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

# Pool and token addresses (checksum format)
w3_temp = Web3()
POOL_YES = w3_temp.to_checksum_address("0x9a14d28909f42823ee29847f87a15fb3b6e8aed3")
SDAI_YES = w3_temp.to_checksum_address("0x493A0D1c776f8797297Aa8B34594fBd0A7F8968a")
GNO_YES = w3_temp.to_checksum_address("0x177304d505eCA60E1aE0dAF1bba4A4c4181dB8Ad")

def setup_web3():
    """Initialize Web3 and account"""
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        raise Exception("Failed to connect to Gnosis Chain")
    
    if not PRIVATE_KEY:
        raise Exception("PRIVATE_KEY not found in environment variables")
    
    account = Account.from_key(PRIVATE_KEY)
    return w3, account

def get_token_info(w3, token_address):
    """Get token decimals and symbol"""
    abi = json.loads('[{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"}]')
    contract = w3.eth.contract(address=token_address, abi=abi)
    decimals = contract.functions.decimals().call()
    symbol = contract.functions.symbol().call()
    return decimals, symbol

def approve_token(w3, account, token_address, spender_address, amount):
    """Approve token for swapping"""
    abi = json.loads('[{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"}]')
    contract = w3.eth.contract(address=token_address, abi=abi)
    
    nonce = w3.eth.get_transaction_count(account.address)
    tx = contract.functions.approve(
        spender_address,
        amount
    ).build_transaction({
        'chainId': 100,
        'gas': 100000,
        'gasPrice': w3.eth.gas_price,
        'nonce': nonce,
    })
    
    signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(f"Approval transaction hash: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Approval confirmed in block {receipt['blockNumber']}")
    return receipt

def perform_swap():
    """Perform a small swap in the pool"""
    # Setup Web3 and account
    w3, account = setup_web3()
    print(f"Using account: {account.address}")
    
    # Get pool information
    print("\nGetting pool information...")
    response = requests.get(f"{UNISWAP_V3_BRIDGE_URL}/api/pool/{POOL_YES}")
    if response.status_code != 200:
        raise Exception(f"Failed to get pool info: {response.text}")
    
    pool_info = response.json()
    print("\nPool Information:")
    print(json.dumps(pool_info, indent=2))
    
    # Get token information
    sdai_decimals, sdai_symbol = get_token_info(w3, SDAI_YES)
    gno_decimals, gno_symbol = get_token_info(w3, GNO_YES)
    
    # We'll swap a small amount of sDAI for GNO
    # Using 0.1 sDAI as input
    amount_in = int(0.1 * (10 ** sdai_decimals))
    
    # Approve sDAI for the swap router
    print("\nApproving sDAI for swap...")
    approve_token(w3, account, SDAI_YES, POOL_YES, amount_in)  # Approve for the pool directly
    
    # Perform the swap
    print("\nPerforming swap...")
    response = requests.post(f"{UNISWAP_V3_BRIDGE_URL}/api/swap", json={
        "poolAddress": POOL_YES,
        "tokenIn": SDAI_YES,
        "tokenOut": GNO_YES,
        "fee": pool_info["fee"],
        "recipient": account.address,
        "amountIn": str(amount_in),
        "amountOutMinimum": "0",  # Be careful with this in production!
        "sqrtPriceLimitX96": "0",  # No price limit
        "signer": {
            "address": account.address,
            "privateKey": PRIVATE_KEY
        }
    })
    
    if response.status_code != 200:
        raise Exception(f"Failed to perform swap: {response.text}")
    
    result = response.json()
    print("\nSwap Transaction Result:")
    print(json.dumps(result, indent=2))
    
    # Wait for transaction confirmation
    if 'hash' in result:
        receipt = w3.eth.wait_for_transaction_receipt(result['hash'])
        print("\nSwap transaction confirmed!")
        print(f"Gas used: {receipt['gasUsed']}")
        print(f"Block number: {receipt['blockNumber']}")

if __name__ == "__main__":
    try:
        perform_swap()
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1) 