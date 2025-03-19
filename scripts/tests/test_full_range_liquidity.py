#!/usr/bin/env python3
"""
Test script for deploying full-range liquidity to the GNO-YES/sDAI-YES pool using the Uniswap V3 SDK.
"""

import os
import sys
import json
import requests
from decimal import Decimal
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Load environment variables
load_dotenv()

# Constants
UNISWAP_V3_BRIDGE_URL = "http://localhost:3001"  # Use localhost instead of Docker service name
RPC_URL = os.getenv("RPC_URL", "https://rpc.ankr.com/gnosis")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

# Pool and token addresses (checksum format)
w3_temp = Web3()  # Temporary Web3 instance for checksum conversion
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

def get_token_balance(w3, token_address, account_address):
    """Get token balance for an address"""
    abi = json.loads('[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]')
    contract = w3.eth.contract(address=token_address, abi=abi)
    balance = contract.functions.balanceOf(account_address).call()
    return balance

def get_pool_tokens(w3, pool_address):
    """Get token0 and token1 addresses from the pool"""
    abi = json.loads('[{"constant":true,"inputs":[],"name":"token0","outputs":[{"name":"","type":"address"}],"type":"function"},{"constant":true,"inputs":[],"name":"token1","outputs":[{"name":"","type":"address"}],"type":"function"}]')
    contract = w3.eth.contract(address=pool_address, abi=abi)
    token0 = contract.functions.token0().call()
    token1 = contract.functions.token1().call()
    return token0, token1

def approve_tokens(w3, account, token_address, spender_address, amount):
    """Approve tokens for spending"""
    abi = json.loads('[{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"}]')
    contract = w3.eth.contract(address=token_address, abi=abi)
    
    # Get the current nonce
    nonce = w3.eth.get_transaction_count(account.address)
    
    # Build the transaction
    tx = contract.functions.approve(
        spender_address,
        amount
    ).build_transaction({
        'chainId': 100,
        'gas': 100000,
        'gasPrice': w3.eth.gas_price,
        'nonce': nonce,
    })
    
    # Sign the transaction
    signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    
    try:
        # Send the transaction
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        print(f"Approval transaction hash: {tx_hash.hex()}")
        
        # Wait for the transaction to be mined
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Approval transaction confirmed in block {receipt['blockNumber']}")
        return receipt
    except Exception as e:
        print(f"Error sending approval transaction: {str(e)}")
        print(f"Transaction details: {tx}")
        raise

def add_full_range_liquidity():
    """Add full-range liquidity to the GNO-YES/sDAI-YES pool"""
    # Setup Web3 and account
    w3, account = setup_web3()
    print(f"Using account: {account.address}")
    
    # Get token order from the pool
    token0, token1 = get_pool_tokens(w3, POOL_YES)
    print(f"\nPool Token Order:")
    print(f"Token0: {token0}")
    print(f"Token1: {token1}")
    print(f"SDAI_YES: {SDAI_YES}")
    print(f"GNO_YES: {GNO_YES}")
    
    # Determine correct token order
    if token0 == SDAI_YES:
        token0_address = SDAI_YES
        token1_address = GNO_YES
    else:
        token0_address = GNO_YES
        token1_address = SDAI_YES
    
    # Get token information
    token0_decimals, token0_symbol = get_token_info(w3, token0_address)
    token1_decimals, token1_symbol = get_token_info(w3, token1_address)
    
    # Get token balances
    token0_balance = get_token_balance(w3, token0_address, account.address)
    token1_balance = get_token_balance(w3, token1_address, account.address)
    
    print(f"\nToken Balances:")
    print(f"{token0_symbol}: {token0_balance / (10 ** token0_decimals)}")
    print(f"{token1_symbol}: {token1_balance / (10 ** token1_decimals)}")
    
    # Get pool information from the bridge
    response = requests.get(f"{UNISWAP_V3_BRIDGE_URL}/pool-info", params={
        "poolAddress": POOL_YES,
        "token0Address": token0_address,
        "token1Address": token1_address
    })
    
    if response.status_code != 200:
        raise Exception(f"Failed to get pool info: {response.text}")
    
    pool_info = response.json()
    print(f"\nPool Information:")
    print(json.dumps(pool_info, indent=2))
    
    # Calculate liquidity amounts (using 10% of available balance)
    token0_amount = int(token0_balance * 0.1)
    token1_amount = int(token1_balance * 0.1)
    
    # Get the NFT position manager address from the bridge
    nft_manager_response = requests.get(f"{UNISWAP_V3_BRIDGE_URL}/nft-manager")
    if nft_manager_response.status_code != 200:
        raise Exception(f"Failed to get NFT manager address: {nft_manager_response.text}")
    
    nft_manager_address = w3.to_checksum_address(nft_manager_response.json()["address"])
    print(f"\nNFT Manager Address: {nft_manager_address}")
    
    # Approve tokens for the NFT position manager
    print("\nApproving tokens...")
    approve_tokens(w3, account, token0_address, nft_manager_address, token0_amount)
    approve_tokens(w3, account, token1_address, nft_manager_address, token1_amount)
    
    # Add liquidity using the bridge
    print("\nAdding full-range liquidity...")
    response = requests.post(f"{UNISWAP_V3_BRIDGE_URL}/add-liquidity", json={
        "poolAddress": POOL_YES,
        "token0Address": token0_address,
        "token1Address": token1_address,
        "amount0": str(token0_amount),
        "amount1": str(token1_amount),
        "useFullRange": True,
        "slippageTolerance": 0.05,  # 5% slippage tolerance
        "deadline": int(w3.eth.get_block('latest').timestamp + 3600),  # 1 hour deadline
        "signer": {
            "address": account.address,
            "privateKey": PRIVATE_KEY
        }
    })
    
    if response.status_code != 200:
        raise Exception(f"Failed to add liquidity: {response.text}")
    
    result = response.json()
    print("\nTransaction Result:")
    print(json.dumps(result, indent=2))
    
    # Wait for transaction confirmation
    if 'hash' in result:
        receipt = w3.eth.wait_for_transaction_receipt(result['hash'])
        print("\nTransaction confirmed!")
        print(f"Gas used: {receipt['gasUsed']}")
        print(f"Block number: {receipt['blockNumber']}")

if __name__ == "__main__":
    try:
        add_full_range_liquidity()
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1) 