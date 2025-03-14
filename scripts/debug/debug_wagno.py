#!/usr/bin/env python3
"""
Simple script to deposit GNO to waGNO on Gnosis Chain
"""

import os
import sys
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from eth_account import Account
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.constants import (
    TOKEN_CONFIG, ERC20_ABI, WAGNO_ABI
)

# Load environment variables
load_dotenv()

# Contract addresses from constants
GNO_ADDRESS = TOKEN_CONFIG["company"]["address"]
WAGNO_ADDRESS = TOKEN_CONFIG["wagno"]["address"]

def get_raw_transaction(signed_tx):
    """Get raw transaction bytes, compatible with different web3.py versions."""
    if hasattr(signed_tx, 'rawTransaction'):
        return signed_tx.rawTransaction
    elif hasattr(signed_tx, 'raw_transaction'):
        return signed_tx.raw_transaction
    else:
        # Try to access the raw transaction directly
        return signed_tx.raw

def main():
    # Connect to Gnosis Chain
    rpc_url = os.getenv('GNOSIS_RPC_URL', 'https://rpc.gnosischain.com')
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    
    # Check connection
    if not w3.is_connected():
        print("❌ Failed to connect to Gnosis Chain")
        return
    
    print(f"✅ Connected to Gnosis Chain (Chain ID: {w3.eth.chain_id})")
    
    # Load account
    if not os.getenv('PRIVATE_KEY'):
        print("❌ No private key found. Set the PRIVATE_KEY environment variable.")
        return
    
    account = Account.from_key(os.getenv('PRIVATE_KEY'))
    address = account.address
    print(f"🔑 Using account: {address}")
    
    # Make sure addresses are checksummed
    gno_address_cs = w3.to_checksum_address(GNO_ADDRESS)
    wagno_address_cs = w3.to_checksum_address(WAGNO_ADDRESS)
    
    # Initialize contracts
    gno_token = w3.eth.contract(address=gno_address_cs, abi=ERC20_ABI)
    wagno_token = w3.eth.contract(address=wagno_address_cs, abi=WAGNO_ABI)
    
    # Get amount to deposit
    amount = float(input("Enter amount of GNO to deposit: "))
    amount_wei = w3.to_wei(amount, 'ether')
    
    # Check GNO balance
    gno_balance = gno_token.functions.balanceOf(address).call()
    print(f"GNO Balance: {w3.from_wei(gno_balance, 'ether')} GNO")
    
    if gno_balance < amount_wei:
        print(f"❌ Insufficient GNO balance")
        return
    
    # Approve GNO for waGNO contract
    current_allowance = gno_token.functions.allowance(address, wagno_address_cs).call()
    print(f"Current allowance: {w3.from_wei(current_allowance, 'ether')} GNO")
    
    if current_allowance < amount_wei:
        print("Approving GNO for waGNO contract...")
        tx = gno_token.functions.approve(wagno_address_cs, amount_wei).build_transaction({
            'from': address,
            'nonce': w3.eth.get_transaction_count(address),
            'gas': 70000,
            'gasPrice': w3.eth.gas_price,
            'chainId': w3.eth.chain_id,
        })
        
        signed_tx = account.sign_transaction(tx)
        # Use our helper function for compatibility
        raw_tx = get_raw_transaction(signed_tx)
        tx_hash = w3.eth.send_raw_transaction(raw_tx)
        print(f"Approval tx sent: {tx_hash.hex()}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt['status'] != 1:
            print("❌ Approval failed")
            return
        print("✅ Approval successful")
    
    # Deposit GNO to get waGNO
    print("\nExecuting deposit...")
    
    # Estimate gas for the deposit
    try:
        deposit_gas = wagno_token.functions.deposit(
            amount_wei,
            address
        ).estimate_gas({
            'from': address
        })
        
        print(f"Estimated gas: {deposit_gas}")
        
        # Build the transaction
        deposit_tx = wagno_token.functions.deposit(
            amount_wei,
            address
        ).build_transaction({
            'from': address,
            'nonce': w3.eth.get_transaction_count(address),
            'gas': int(deposit_gas * 1.2),  # Add 20% buffer
            'gasPrice': w3.eth.gas_price,
            'chainId': w3.eth.chain_id,
        })
        
        # Sign and send transaction
        signed_tx = account.sign_transaction(deposit_tx)
        # Use our helper function for compatibility
        raw_tx = get_raw_transaction(signed_tx)
        tx_hash = w3.eth.send_raw_transaction(raw_tx)
        print(f"Deposit transaction sent: {tx_hash.hex()}")
        
        # Wait for transaction confirmation
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt['status'] == 1:
            print(f"✅ Successfully deposited {amount} GNO for waGNO!")
            
            # Check new balances
            gno_balance_after = gno_token.functions.balanceOf(address).call()
            wagno_balance_after = wagno_token.functions.balanceOf(address).call()
            
            print(f"GNO Balance after: {w3.from_wei(gno_balance_after, 'ether')} GNO")
            print(f"waGNO Balance after: {w3.from_wei(wagno_balance_after, 'ether')} waGNO")
        else:
            print("❌ Deposit transaction failed!")
            
    except Exception as e:
        print(f"❌ Error depositing GNO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()