#!/usr/bin/env python3

import os
import json
import traceback
from web3 import Web3
from dotenv import load_dotenv
from eth_account import Account
from eth_account.signers.local import LocalAccount
from eth_utils import to_hex
from pathlib import Path
import sys
import binascii

# Add the project root to the path to import project modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import project constants
from config.constants import (
    CONTRACT_ADDRESSES, TOKEN_CONFIG, DEFAULT_SWAP_CONFIG, ERC20_ABI
)

# Load .env file but don't override existing environment variables
load_dotenv(override=False)  # This ensures command-line vars take precedence

DEBUG = True

def debug_print(msg):
    if DEBUG:
        print(f"[DEBUG] {msg}")

def send_signed_transaction(w3, signed_tx):
    """Helper function to handle different web3.py versions and their signed transaction formats"""
    try:
        # For newer web3.py versions
        return w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    except AttributeError:
        # For older web3.py versions or different signature formats
        if hasattr(signed_tx, 'raw_transaction'):
            return w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        elif isinstance(signed_tx, dict) and 'rawTransaction' in signed_tx:
            return w3.eth.send_raw_transaction(signed_tx['rawTransaction'])
        elif isinstance(signed_tx, dict) and 'raw_transaction' in signed_tx:
            return w3.eth.send_raw_transaction(signed_tx['raw_transaction'])
        elif hasattr(signed_tx, 'get'):
            if signed_tx.get('rawTransaction'):
                return w3.eth.send_raw_transaction(signed_tx.get('rawTransaction'))
            elif signed_tx.get('raw_transaction'):
                return w3.eth.send_raw_transaction(signed_tx.get('raw_transaction'))
        
        # If we can extract raw transaction as a hex string
        try:
            raw_tx_hex = to_hex(signed_tx)
            return w3.eth.send_raw_transaction(raw_tx_hex)
        except:
            pass
            
        # Last resort - try to access via r,s,v components
        try:
            tx_data = signed_tx.build_transaction()
            raw_tx = w3.eth.account.sign_transaction(tx_data, private_key=private_key)
            return w3.eth.send_raw_transaction(raw_tx.rawTransaction)
        except:
            raise ValueError(f"Could not extract raw transaction from signed transaction object: {type(signed_tx)}")

def main():
    # 1. Connect to Gnosis (or your preferred) chain
    rpc_url = os.getenv("GNOSIS_RPC_URL", "https://rpc.gnosis.gateway.fm")
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print("❌ Failed to connect to the blockchain")
        return

    print(f"✅ Connected to chain (chainId: {w3.eth.chain_id})")

    # 2. Load private key and create account object
    private_key = os.getenv("PRIVATE_KEY")
    if not private_key:
        print("❌ PRIVATE_KEY not set in .env")
        return

    account: LocalAccount = Account.from_key(private_key)
    owner_address = account.address
    print(f"🔑 Using owner account: {owner_address}")

    # 3. Define contract addresses (update as needed)
    #    - Must match the deployed UniswapV3PassthroughRouter for which you are owner
    UNISWAP_V3_PASSTHROUGH_ROUTER_ADDRESS = w3.to_checksum_address(os.getenv("V3_PASSTHROUGH_ROUTER_ADDRESS", "0x77DBE0441C950cE9C97a5F9A79CF316947aAa578"))
    # Updated pool address for YES pool
    UNISWAP_V3_POOL_ADDRESS = w3.to_checksum_address(os.getenv("POOL_YES_ADDRESS", "0x9a14d28909f42823ee29847f87a15fb3b6e8aed3"))
    # Default recipient address
    RECIPIENT_ADDRESS = owner_address  # Use our own address as recipient
    
    # Use SDAI YES and GNO YES tokens
    TOKEN_IN_ADDRESS = w3.to_checksum_address(os.getenv("SDAI_YES_ADDRESS", "0x493A0D1c776f8797297Aa8B34594fBd0A7F8968a"))  # SDAI YES
    TOKEN_OUT_ADDRESS = w3.to_checksum_address(os.getenv("GNO_YES_ADDRESS", "0x177304d505eCA60E1aE0dAF1bba4A4c4181dB8Ad"))  # GNO YES

    # 4. ABIs
    # Passthrough Router ABI (interface definition). Ensure it matches your deployed version.
    passthrough_router_abi = [
        {
            "inputs": [
                {"internalType": "address", "name": "pool", "type": "address"},
                {"internalType": "address", "name": "recipient", "type": "address"},
                {"internalType": "bool", "name": "zeroForOne", "type": "bool"},
                {"internalType": "int256", "name": "amountSpecified", "type": "int256"},
                {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"},
                {"internalType": "bytes", "name": "data", "type": "bytes"}
            ],
            "name": "swap",
            "outputs": [
                {"internalType": "int256", "name": "amount0", "type": "int256"},
                {"internalType": "int256", "name": "amount1", "type": "int256"}
            ],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "owner",
            "outputs": [{"internalType": "address", "name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [{"internalType": "address", "name": "pool", "type": "address"}],
            "name": "authorizePool",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }
    ]

    # 5. Initialize contracts
    token_in_contract = w3.eth.contract(address=TOKEN_IN_ADDRESS, abi=ERC20_ABI)
    token_out_contract = w3.eth.contract(address=TOKEN_OUT_ADDRESS, abi=ERC20_ABI)
    router_contract = w3.eth.contract(address=UNISWAP_V3_PASSTHROUGH_ROUTER_ADDRESS, abi=passthrough_router_abi)

    # 6. Check balances
    token_in_balance = token_in_contract.functions.balanceOf(owner_address).call()
    token_out_balance_before = token_out_contract.functions.balanceOf(owner_address).call()
    
    # Update token names to reflect YES tokens
    token_in_symbol = "SDAI YES" if TOKEN_IN_ADDRESS.lower() == TOKEN_CONFIG["currency"]["yes_address"].lower() else "TOKEN_IN"
    token_out_symbol = "GNO YES" if TOKEN_OUT_ADDRESS.lower() == TOKEN_CONFIG["company"]["yes_address"].lower() else "TOKEN_OUT"
    
    print(f"💰 {w3.from_wei(token_in_balance, 'ether')} {token_in_symbol} balance")
    print(f"💰 {w3.from_wei(token_out_balance_before, 'ether')} {token_out_symbol} balance before swap")

    # 7. Decide how much to swap; ensure you have enough balance
    # Command-line override takes precedence over .env
    amount = float(os.environ.get("AMOUNT_TO_SWAP", "0.001"))  # Use os.environ.get instead of os.getenv
    amount_in_wei = w3.to_wei(amount, 'ether')
    
    print(f"🔄 Swap amount: {amount} {token_in_symbol}")
    
    if token_in_balance < amount_in_wei:
        print(f"❌ Insufficient {token_in_symbol} balance.")
        return

    # 8. Check allowance. If insufficient, approve the pass-through router.
    current_allowance = token_in_contract.functions.allowance(owner_address, UNISWAP_V3_PASSTHROUGH_ROUTER_ADDRESS).call()
    print(f"Current allowance for router: {w3.from_wei(current_allowance, 'ether')}")

    if current_allowance < amount_in_wei:
        print(f"🔑 Approving pass-through router to spend our {token_in_symbol}...")
        nonce = w3.eth.get_transaction_count(owner_address)
        try:
            approve_tx = token_in_contract.functions.approve(
                UNISWAP_V3_PASSTHROUGH_ROUTER_ADDRESS, 
                amount_in_wei * 10  # Approve 10x to reduce repeated approvals
            ).build_transaction({
                "from": owner_address,
                "nonce": nonce,
                "gas": 120000,
                "maxFeePerGas": w3.eth.gas_price * 2,
                "maxPriorityFeePerGas": w3.eth.gas_price,
                "chainId": w3.eth.chain_id,
                "type": "0x2"
            })

            signed_approve = w3.eth.account.sign_transaction(approve_tx, private_key=private_key)
            
            # Use our helper function to send the transaction safely
            tx_hash = send_signed_transaction(w3, signed_approve)
            
            print(f"⏳ Approval tx sent: {tx_hash.hex()}")
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt.status == 1:
                print("✅ Approval successful.")
            else:
                print("❌ Approval failed.")
                return
        except Exception as e:
            print(f"❌ Approval error: {str(e)}")
            traceback.print_exc()
            return

    # 9. Perform the swap
    # For a normal "exact input" swap, amountSpecified > 0. 
    # Updated parameters for SDAI YES to GNO YES swap
    zero_for_one = False  # SDAI YES (token1) to GNO YES (token0)
    # Use a higher price limit for zero_for_one=False (higher than current)
    sqrt_price_limit_x96 = int(974062921369258046699441232588 * 1.2)  # 120% of current price

    # Double check that your address is indeed the router's owner
    router_owner = router_contract.functions.owner().call()
    if router_owner.lower() != owner_address.lower():
        print("❌ You are not the owner of the UniswapV3PassthroughRouter. Swap will revert.")
        return

    # Determine if we need to authorize the pool first
    try:
        # Check if pool needs authorization
        # This could be done with a call to authorizedPools() if that function is available in the ABI
        # For simplicity, we'll just authorize the pool anyway (which is idempotent)
        print("\n🔑 Authorizing pool for the router...")
        nonce = w3.eth.get_transaction_count(owner_address)
        authorize_tx = router_contract.functions.authorizePool(
            UNISWAP_V3_POOL_ADDRESS
        ).build_transaction({
            "from": owner_address,
            "nonce": nonce,
            "gas": 200000,
            "maxFeePerGas": w3.eth.gas_price * 2,
            "maxPriorityFeePerGas": w3.eth.gas_price,
            "chainId": w3.eth.chain_id,
            "type": "0x2"
        })

        signed_authorize_tx = w3.eth.account.sign_transaction(authorize_tx, private_key=private_key)
        
        # Use our helper function to send the transaction safely
        tx_hash = send_signed_transaction(w3, signed_authorize_tx)
        
        print(f"⏳ Pool authorization tx sent: {tx_hash.hex()}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            print("✅ Pool authorization successful.")
        else:
            print("❌ Pool authorization failed.")
            return
    except Exception as e:
        print(f"❌ Pool authorization error: {str(e)}")
        # This might not be a fatal error if the pool is already authorized
        print("Continuing with swap attempt...")

    print("\n🔄 Executing Uniswap V3 swap...")
    print(f"Pool: {UNISWAP_V3_POOL_ADDRESS}")
    print(f"Recipient: {RECIPIENT_ADDRESS}")
    print(f"Zero for One: {zero_for_one}")
    print(f"Amount: {amount_in_wei} ({w3.from_wei(amount_in_wei, 'ether')} tokens)")
    print(f"Sqrt Price Limit X96: {sqrt_price_limit_x96}")
    print(f"Token In: {TOKEN_IN_ADDRESS} ({token_in_symbol})")
    print(f"Token Out: {TOKEN_OUT_ADDRESS} ({token_out_symbol})")
    
    try:
        nonce = w3.eth.get_transaction_count(owner_address)
        swap_tx = router_contract.functions.swap(
            UNISWAP_V3_POOL_ADDRESS,
            RECIPIENT_ADDRESS,        # Updated to use specified recipient
            zero_for_one,             # From the provided parameters
            amount_in_wei,            # From the provided parameters
            sqrt_price_limit_x96,     # From the provided parameters
            b''                       # No data as specified
        ).build_transaction({
            "from": owner_address,
            "nonce": nonce,
            "gas": 1000000,  # Increase gas limit
            "maxFeePerGas": w3.eth.gas_price * 2,
            "maxPriorityFeePerGas": w3.eth.gas_price,
            "chainId": w3.eth.chain_id,
            "type": "0x2"
        })

        debug_print("Signing and sending swap transaction...")
        signed_swap_tx = w3.eth.account.sign_transaction(swap_tx, private_key=private_key)
        
        # Use our helper function to send the transaction safely
        tx_hash = send_signed_transaction(w3, signed_swap_tx)
        
        print(f"⏳ Swap transaction sent: {tx_hash.hex()}")

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            print("✅ Swap successful!")
        else:
            print("❌ Swap transaction reverted or failed.")

        # 10. Check post-swap balances
        # If recipient is not our address, check their balance too
        token_out_balance_after = token_out_contract.functions.balanceOf(owner_address).call()
        print(f"🔹 {token_out_symbol} after swap (owner): {w3.from_wei(token_out_balance_after, 'ether')}")
        gained = token_out_balance_after - token_out_balance_before
        print(f"🔹 Gained (owner): {w3.from_wei(gained, 'ether')} {token_out_symbol}")
        
        if RECIPIENT_ADDRESS.lower() != owner_address.lower():
            recipient_balance = token_out_contract.functions.balanceOf(RECIPIENT_ADDRESS).call()
            print(f"🔹 {token_out_symbol} balance (recipient): {w3.from_wei(recipient_balance, 'ether')}")

        print(f"\n🔗 Explorer: https://gnosisscan.io/tx/{tx_hash.hex()}")

    except Exception as e:
        print(f"❌ Error during swap: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main() 