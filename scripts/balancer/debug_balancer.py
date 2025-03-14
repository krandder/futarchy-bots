#!/usr/bin/env python3
"""
Debug script for Balancer swaps on Gnosis Chain
"""

import os
import json
import sys
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from eth_account import Account
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.constants import (
    TOKEN_CONFIG, BALANCER_CONFIG, BALANCER_VAULT_ABI, BALANCER_POOL_ABI, ERC20_ABI
)

# Load environment variables
load_dotenv()

# Contract addresses from constants
WAGNO_ADDRESS = TOKEN_CONFIG["wagno"]["address"]
SDAI_ADDRESS = TOKEN_CONFIG["currency"]["address"]
BALANCER_VAULT_ADDRESS = BALANCER_CONFIG["vault_address"]
BALANCER_POOL_ADDRESS = BALANCER_CONFIG["pool_address"]

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
    wagno_address_cs = w3.to_checksum_address(WAGNO_ADDRESS)
    sdai_address_cs = w3.to_checksum_address(SDAI_ADDRESS)
    balancer_vault_address_cs = w3.to_checksum_address(BALANCER_VAULT_ADDRESS)
    balancer_pool_address_cs = w3.to_checksum_address(BALANCER_POOL_ADDRESS)
    
    # Initialize contracts
    wagno_token = w3.eth.contract(address=wagno_address_cs, abi=ERC20_ABI)
    sdai_token = w3.eth.contract(address=sdai_address_cs, abi=ERC20_ABI)
    balancer_vault = w3.eth.contract(address=balancer_vault_address_cs, abi=BALANCER_VAULT_ABI)
    balancer_pool = w3.eth.contract(address=balancer_pool_address_cs, abi=BALANCER_POOL_ABI)
    
    # 1. Get the pool ID directly from the pool contract
    try:
        pool_id = balancer_pool.functions.getPoolId().call()
        print(f"✅ Retrieved pool ID: {pool_id.hex()}")
    except Exception as e:
        print(f"❌ Error retrieving pool ID: {e}")
        # Set a fallback pool ID based on the pool address
        pool_id = bytes.fromhex(BALANCER_POOL_ADDRESS.replace("0x", "").lower() + "0002000000000000000001d7")
        print(f"⚠️ Using fallback pool ID: {pool_id.hex()}")
    
    # 2. Get pool tokens
    try:
        tokens, balances, _ = balancer_vault.functions.getPoolTokens(pool_id).call()
        print("\n📊 Pool Tokens:")
        for i, token in enumerate(tokens):
            print(f"  {i+1}: {token} - Balance: {w3.from_wei(balances[i], 'ether')}")
    except Exception as e:
        print(f"❌ Error getting pool tokens: {e}")
    
    # 3. Get token balances
    wagno_balance = wagno_token.functions.balanceOf(address).call()
    sdai_balance = sdai_token.functions.balanceOf(address).call()
    print("\n💰 Token Balances:")
    print(f"  waGNO: {w3.from_wei(wagno_balance, 'ether')}")
    print(f"  sDAI: {w3.from_wei(sdai_balance, 'ether')}")
    
    # 4. Which direction to swap?
    direction = input("\nSwap direction (1=waGNO->sDAI, 2=sDAI->waGNO): ")
    if direction == "1":
        from_token = wagno_address_cs
        to_token = sdai_address_cs
        from_token_name = "waGNO"
        to_token_name = "sDAI"
        from_balance = wagno_balance
    else:
        from_token = sdai_address_cs
        to_token = wagno_address_cs
        from_token_name = "sDAI"
        to_token_name = "waGNO"
        from_balance = sdai_balance
    
    # 5. Get amount to swap
    max_amount = w3.from_wei(from_balance, 'ether')
    amount_str = input(f"\nAmount of {from_token_name} to swap (max {max_amount}): ")
    amount = float(amount_str)
    amount_wei = w3.to_wei(amount, 'ether')
    
    # Make sure we have enough balance
    if amount_wei > from_balance:
        print(f"❌ Insufficient {from_token_name} balance.")
        return
    
    # 6. Set minimum amount to receive (default 10% slippage)
    min_amount_str = input(f"Minimum {to_token_name} to receive (leave blank for 10% slippage): ")
    if min_amount_str:
        min_amount = float(min_amount_str)
    else:
        min_amount = amount * 0.9
    min_amount_wei = w3.to_wei(min_amount, 'ether')
    
    print(f"\n⚙️ Swap Configuration:")
    print(f"  From: {amount} {from_token_name} ({from_token})")
    print(f"  To: {to_token_name} ({to_token})")
    print(f"  Minimum receive: {min_amount} {to_token_name}")
    print(f"  Pool ID: {pool_id.hex()}")
    
    # 7. Approve tokens for Balancer Vault
    from_token_contract = wagno_token if from_token == wagno_address_cs else sdai_token
    allowance = from_token_contract.functions.allowance(address, balancer_vault_address_cs).call()
    
    if allowance < amount_wei:
        print(f"\nApproving {from_token_name} for Balancer Vault...")
        approve_tx = from_token_contract.functions.approve(
            balancer_vault_address_cs,
            amount_wei
        ).build_transaction({
            'from': address,
            'nonce': w3.eth.get_transaction_count(address),
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
            'chainId': w3.eth.chain_id,
        })
        
        signed_tx = account.sign_transaction(approve_tx)
        tx_hash = w3.eth.send_raw_transaction(get_raw_transaction(signed_tx))
        print(f"Approval tx sent: {tx_hash.hex()}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt['status'] != 1:
            print("❌ Approval failed")
            return
        print("✅ Approval successful")
    else:
        print(f"✅ {from_token_name} already approved for Balancer Vault")
    
    # 8. Create swap parameters
    print("\n🔄 Creating swap parameters...")
    single_swap = {
        'poolId': pool_id,
        'assetIn': from_token,
        'assetOut': to_token,
        'amount': amount_wei,
        'userData': b''  # No specific userData needed
    }
    
    fund_management = {
        'sender': address,
        'fromInternalBalance': False,
        'recipient': address,
        'toInternalBalance': False
    }
    
    limit = min_amount_wei
    deadline = w3.eth.get_block('latest')['timestamp'] + 600  # 10 minutes
    
    print(f"  Asset In: {from_token}")
    print(f"  Asset Out: {to_token}")
    print(f"  Amount: {amount_wei}")
    print(f"  Limit: {limit}")
    print(f"  Deadline: {deadline}")
    
    # 9. Execute the swap
    proceed = input("\nProceed with swap? (y/n): ")
    if proceed.lower() != 'y':
        print("Swap cancelled.")
        return
    
    try:
        # Try to estimate gas - this might fail if swap would fail
        try:
            gas_estimate = balancer_vault.functions.swap(
                single_swap,
                fund_management,
                limit,
                deadline
            ).estimate_gas({'from': address, 'value': 0})
            print(f"Estimated gas: {gas_estimate}")
            gas_limit = int(gas_estimate * 1.2)  # Add 20% buffer
        except Exception as gas_err:
            print(f"⚠️ Gas estimation failed: {gas_err}")
            gas_limit = 700000  # Use a high default
        
        swap_tx = balancer_vault.functions.swap(
            single_swap,
            fund_management,
            limit,
            deadline
        ).build_transaction({
            'from': address,
            'nonce': w3.eth.get_transaction_count(address),
            'gas': gas_limit,
            'gasPrice': w3.eth.gas_price,
            'chainId': w3.eth.chain_id,
            'value': 0
        })
        
        # Print the full tx data for reference
        print(f"\nTransaction data: {swap_tx['data']}")
        
        signed_tx = account.sign_transaction(swap_tx)
        tx_hash = w3.eth.send_raw_transaction(get_raw_transaction(signed_tx))
        print(f"\n⏳ Swap transaction sent: {tx_hash.hex()}")
        
        print("Waiting for transaction confirmation...")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt['status'] == 1:
            print(f"✅ Swap successful!")
            
            # Get new balances
            new_wagno_balance = wagno_token.functions.balanceOf(address).call()
            new_sdai_balance = sdai_token.functions.balanceOf(address).call()
            
            print("\n💰 Updated Token Balances:")
            print(f"  waGNO: {w3.from_wei(new_wagno_balance, 'ether')} (Change: {w3.from_wei(new_wagno_balance - wagno_balance, 'ether')})")
            print(f"  sDAI: {w3.from_wei(new_sdai_balance, 'ether')} (Change: {w3.from_wei(new_sdai_balance - sdai_balance, 'ether')})")
        else:
            print("❌ Swap transaction failed!")
            
    except Exception as e:
        print(f"❌ Error executing swap: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()