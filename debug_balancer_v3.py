#!/usr/bin/env python3
"""
Debug script for Balancer V3 swaps using the Router V2 with single swap function
"""

import os
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from eth_account import Account
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Contract addresses
WAGNO_ADDRESS = "0x7c16F0185A26Db0AE7a9377f23BC18ea7ce5d644"
SDAI_ADDRESS = "0xaf204776c7245bF4147c2612BF6e5972Ee483701"
BALANCER_POOL_ADDRESS = "0xD1D7Fa8871d84d0E77020fc28B7Cd5718C446522"

# Latest V3 Router V2 address for Gnosis Chain
BALANCER_ROUTER_ADDRESS = "0x4eff2d77D9fFbAeFB4b141A3e494c085b3FF4Cb5"

# ABI definitions
ERC20_ABI = [
    {"inputs":[{"name":"owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]

POOL_ABI = [
    {"inputs":[],"name":"getVault","outputs":[{"internalType":"contract IVault","name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"getTokens","outputs":[{"internalType":"contract IERC20[]","name":"tokens","type":"address[]"}],"stateMutability":"view","type":"function"}
]

# Router ABI for the swapSingleTokenExactIn function from documentation
ROUTER_ABI = [
    {"inputs":[{"internalType":"address","name":"pool","type":"address"},{"internalType":"contract IERC20","name":"tokenIn","type":"address"},{"internalType":"contract IERC20","name":"tokenOut","type":"address"},{"internalType":"uint256","name":"exactAmountIn","type":"uint256"},{"internalType":"uint256","name":"minAmountOut","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"wethIsEth","type":"bool"},{"internalType":"bytes","name":"userData","type":"bytes"}],"name":"swapSingleTokenExactIn","outputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"}],"stateMutability":"payable","type":"function"},
    # Add multicall function for more complex operations if needed
    {"inputs":[{"internalType":"bytes[]","name":"data","type":"bytes[]"}],"name":"multicall","outputs":[{"internalType":"bytes[]","name":"results","type":"bytes[]"}],"stateMutability":"nonpayable","type":"function"}
]

def get_raw_transaction(signed_tx):
    """Get raw transaction bytes, compatible with different web3.py versions."""
    if hasattr(signed_tx, 'rawTransaction'):
        return signed_tx.rawTransaction
    elif hasattr(signed_tx, 'raw_transaction'):
        return signed_tx.raw_transaction
    else:
        return signed_tx.raw

def main():
    # Connect to Gnosis Chain
    rpc_url = os.getenv('GNOSIS_RPC_URL', 'https://rpc.gnosischain.com')
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    
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
    balancer_pool_address_cs = w3.to_checksum_address(BALANCER_POOL_ADDRESS)
    router_address_cs = w3.to_checksum_address(BALANCER_ROUTER_ADDRESS)
    
    # Initialize contracts
    wagno_token = w3.eth.contract(address=wagno_address_cs, abi=ERC20_ABI)
    sdai_token = w3.eth.contract(address=sdai_address_cs, abi=ERC20_ABI)
    pool = w3.eth.contract(address=balancer_pool_address_cs, abi=POOL_ABI)
    router = w3.eth.contract(address=router_address_cs, abi=ROUTER_ABI)
    
    # Get vault address
    try:
        vault_address = pool.functions.getVault().call()
        vault_address_cs = w3.to_checksum_address(vault_address)
        print(f"✅ Retrieved Vault address from pool: {vault_address_cs}")
    except Exception as e:
        print(f"❌ Error getting Vault address: {e}")
        return
    
    # Get token balances
    wagno_balance = wagno_token.functions.balanceOf(address).call()
    sdai_balance = sdai_token.functions.balanceOf(address).call()
    print("\n💰 Token Balances:")
    print(f"  waGNO: {w3.from_wei(wagno_balance, 'ether')}")
    print(f"  sDAI: {w3.from_wei(sdai_balance, 'ether')}")
    
    # Get swap direction
    direction = input("\nSwap direction (1=waGNO->sDAI, 2=sDAI->waGNO): ")
    if direction == "1":
        from_token = wagno_address_cs
        to_token = sdai_address_cs
        from_token_name = "waGNO"
        to_token_name = "sDAI"
        from_balance = wagno_balance
        from_token_contract = wagno_token
    else:
        from_token = sdai_address_cs
        to_token = wagno_address_cs
        from_token_name = "sDAI"
        to_token_name = "waGNO"
        from_balance = sdai_balance
        from_token_contract = sdai_token
    
    # Get amount to swap
    max_amount = w3.from_wei(from_balance, 'ether')
    amount_str = input(f"\nAmount of {from_token_name} to swap (max {max_amount}): ")
    amount = float(amount_str)
    amount_wei = w3.to_wei(amount, 'ether')
    
    if amount_wei > from_balance:
        print(f"❌ Insufficient {from_token_name} balance.")
        return
    
    # Set minimum amount to receive (default 10% slippage)
    min_amount_str = input(f"Minimum {to_token_name} to receive (leave blank for 10% slippage): ")
    if min_amount_str:
        min_amount = float(min_amount_str)
    else:
        min_amount = amount * 0.9
    min_amount_wei = w3.to_wei(min_amount, 'ether')
    
    print(f"\n⚙️ Swap Configuration:")
    print(f"  Router: {router_address_cs}")
    print(f"  Pool: {balancer_pool_address_cs}")
    print(f"  From: {amount} {from_token_name} ({from_token})")
    print(f"  To: {to_token_name} ({to_token})")
    print(f"  Minimum receive: {min_amount} {to_token_name}")
    
    # IMPORTANT: Approve the Vault (not the Router)
    allowance = from_token_contract.functions.allowance(address, vault_address_cs).call()
    if allowance < amount_wei:
        print(f"\nApproving {from_token_name} for Balancer Vault...")
        approve_tx = from_token_contract.functions.approve(
            vault_address_cs,
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
    
    # Set deadline to 10 minutes from now
    deadline = w3.eth.get_block('latest')['timestamp'] + 600
    
    # Execute the swap
    proceed = input("\nProceed with swap? (y/n): ")
    if proceed.lower() != 'y':
        print("Swap cancelled.")
        return
    
    try:
        print("\n🔄 Creating swap transaction...")
        
        # Build transaction
        swap_tx = router.functions.swapSingleTokenExactIn(
            balancer_pool_address_cs,
            from_token,
            to_token,
            amount_wei,
            min_amount_wei,
            deadline,
            False,  # wethIsEth
            '0x'  # userData as hex string
        ).build_transaction({
            'from': address,
            'nonce': w3.eth.get_transaction_count(address),
            'gas': 1000000,  # High gas limit
            'gasPrice': w3.eth.gas_price,
            'chainId': w3.eth.chain_id,
            'value': 0
        })
        
        # Sign transaction
        signed_tx = account.sign_transaction(swap_tx)
        tx_hash = w3.eth.send_raw_transaction(get_raw_transaction(signed_tx))
        print(f"\n⏳ Swap transaction sent: {tx_hash.hex()}")
        
        # Wait for confirmation
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