#!/usr/bin/env python3

import os
import sys
from decimal import Decimal
from web3 import Web3
from dotenv import load_dotenv
from eth_account import Account
from eth_account.signers.local import LocalAccount

# Load .env file but don't override existing environment variables
load_dotenv(override=False)

# Router ABI
ROUTER_ABI = [
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

# ERC20 ABI
ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": False, "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "payable": False, "stateMutability": "nonpayable", "type": "function"},
    {"constant": True, "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "payable": False, "stateMutability": "view", "type": "function"}
]

# Pool ABI for getting price
POOL_ABI = [
    {"inputs": [], "name": "slot0", "outputs": [{"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"}, {"internalType": "int24", "name": "tick", "type": "int24"}, {"internalType": "uint16", "name": "observationIndex", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"}, {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"}, {"internalType": "bool", "name": "unlocked", "type": "bool"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "token0", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "token1", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"}
]

def main():
    # Connect to RPC
    rpc_url = os.environ.get("RPC_URL", "https://gnosis-mainnet.public.blastapi.io")
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print("❌ Failed to connect to the blockchain")
        return False
    
    print(f"✅ Connected to chain (chainId: {w3.eth.chain_id})")
    
    # Load account
    private_key = os.environ.get("PRIVATE_KEY")
    if not private_key:
        print("❌ PRIVATE_KEY not set in environment")
        return False
    
    account = Account.from_key(private_key)
    owner_address = account.address
    print(f"🔑 Using account: {owner_address}")
    
    # Define addresses
    router_address = w3.to_checksum_address(os.environ.get("V3_PASSTHROUGH_ROUTER_ADDRESS"))
    pool_address = w3.to_checksum_address(os.environ.get("POOL_NO_ADDRESS", "0x6E33153115Ab58dab0e0F1E3a2ccda6e67FA5cD7"))
    sdai_no_address = w3.to_checksum_address(os.environ.get("SDAI_NO_ADDRESS", "0xE1133Ef862f3441880adADC2096AB67c63f6E102"))
    gno_no_address = w3.to_checksum_address(os.environ.get("GNO_NO_ADDRESS", "0xf1B3E5Ffc0219A4F8C0ac69EC98C97709EdfB6c9"))
    
    # Initialize contracts
    router_contract = w3.eth.contract(address=router_address, abi=ROUTER_ABI)
    sdai_no_contract = w3.eth.contract(address=sdai_no_address, abi=ERC20_ABI)
    gno_no_contract = w3.eth.contract(address=gno_no_address, abi=ERC20_ABI)
    pool_contract = w3.eth.contract(address=pool_address, abi=POOL_ABI)
    
    # Verify token order in the pool
    token0 = pool_contract.functions.token0().call()
    token1 = pool_contract.functions.token1().call()
    print(f"Pool token0: {token0}")
    print(f"Pool token1: {token1}")
    print(f"SDAI NO token: {sdai_no_address}")
    print(f"GNO NO token: {gno_no_address}")
    
    # Confirm token order
    if token0.lower() == sdai_no_address.lower() and token1.lower() == gno_no_address.lower():
        print("✅ Confirmed: token0 is SDAI NO, token1 is GNO NO")
        zero_for_one = True  # SDAI NO (token0) to GNO NO (token1)
    else:
        print("❌ Unexpected token order in pool")
        return False
    
    # Get current price
    slot0 = pool_contract.functions.slot0().call()
    current_sqrt_price = slot0[0]
    print(f"Current sqrtPriceX96: {current_sqrt_price}")
    
    # Try multiple price limits
    price_limits = [
        ("100%", current_sqrt_price),
        ("90%", int(current_sqrt_price * 0.9)),
        ("80%", int(current_sqrt_price * 0.8)),
        ("70%", int(current_sqrt_price * 0.7)),
        ("60%", int(current_sqrt_price * 0.6)),
        ("50%", int(current_sqrt_price * 0.5)),
        ("40%", int(current_sqrt_price * 0.4)),
        ("30%", int(current_sqrt_price * 0.3)),
        ("20%", int(current_sqrt_price * 0.2)),
        ("10%", int(current_sqrt_price * 0.1)),
        ("5%", int(current_sqrt_price * 0.05)),
        ("Min", 4295128739)  # Minimum possible price
    ]
    
    # Try different amounts
    amounts = [
        ("0.0001", w3.to_wei(0.0001, 'ether')),
        ("0.00005", w3.to_wei(0.00005, 'ether')),
        ("0.00001", w3.to_wei(0.00001, 'ether')),
        ("0.000005", w3.to_wei(0.000005, 'ether')),
        ("0.000001", w3.to_wei(0.000001, 'ether'))
    ]
    
    # Check balance
    sdai_no_balance = sdai_no_contract.functions.balanceOf(owner_address).call()
    print(f"SDAI NO balance: {w3.from_wei(sdai_no_balance, 'ether')}")
    
    # Authorize pool
    try:
        nonce = w3.eth.get_transaction_count(owner_address)
        authorize_tx = router_contract.functions.authorizePool(
            pool_address
        ).build_transaction({
            "from": owner_address,
            "nonce": nonce,
            "gas": 200000,
            "maxFeePerGas": w3.eth.gas_price * 2,
            "maxPriorityFeePerGas": w3.eth.gas_price,
            "chainId": w3.eth.chain_id,
            "type": "0x2"
        })
        
        signed_tx = w3.eth.account.sign_transaction(authorize_tx, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"⏳ Pool authorization tx sent: {tx_hash.hex()}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            print("✅ Pool authorization successful")
        else:
            print("❌ Pool authorization failed")
    except Exception as e:
        print(f"⚠️ Pool authorization exception: {str(e)}")
        print("Continuing anyway as the pool might already be authorized...")
    
    # Approve token if needed
    # Using a very small amount for testing to minimize risk
    for amount_label, amount_wei in amounts:
        current_allowance = sdai_no_contract.functions.allowance(owner_address, router_address).call()
        if current_allowance < amount_wei:
            try:
                nonce = w3.eth.get_transaction_count(owner_address)
                approve_tx = sdai_no_contract.functions.approve(
                    router_address,
                    amount_wei * 10  # Approve 10x to reduce future approvals
                ).build_transaction({
                    "from": owner_address,
                    "nonce": nonce,
                    "gas": 120000,
                    "maxFeePerGas": w3.eth.gas_price * 2,
                    "maxPriorityFeePerGas": w3.eth.gas_price,
                    "chainId": w3.eth.chain_id,
                    "type": "0x2"
                })
                
                signed_tx = w3.eth.account.sign_transaction(approve_tx, private_key=private_key)
                tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                print(f"⏳ Approval tx sent: {tx_hash.hex()}")
                
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                if receipt.status == 1:
                    print("✅ Approval successful")
                else:
                    print("❌ Approval failed")
                    return False
            except Exception as e:
                print(f"❌ Approval error: {str(e)}")
                return False
        
        # Get initial GNO NO balance for comparison
        gno_no_balance_before = gno_no_contract.functions.balanceOf(owner_address).call()
        
        # Try all price limits for the current amount
        print(f"\n\n=== Testing with amount {amount_label} ===")
        for price_label, price_limit in price_limits:
            print(f"\n--- Price limit: {price_label} ---")
            try:
                # Execute swap
                nonce = w3.eth.get_transaction_count(owner_address)
                swap_tx = router_contract.functions.swap(
                    pool_address,
                    owner_address,
                    zero_for_one,
                    amount_wei,
                    price_limit,
                    b''
                ).build_transaction({
                    "from": owner_address,
                    "nonce": nonce,
                    "gas": 1000000,
                    "maxFeePerGas": w3.eth.gas_price * 2,
                    "maxPriorityFeePerGas": w3.eth.gas_price,
                    "chainId": w3.eth.chain_id,
                    "type": "0x2"
                })
                
                signed_tx = w3.eth.account.sign_transaction(swap_tx, private_key=private_key)
                tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                print(f"⏳ Swap tx sent: {tx_hash.hex()}")
                
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                if receipt.status == 1:
                    gno_no_balance_after = gno_no_contract.functions.balanceOf(owner_address).call()
                    gained = gno_no_balance_after - gno_no_balance_before
                    print(f"✅ Swap successful with {amount_label} and price limit {price_label}!")
                    print(f"Gained: {w3.from_wei(gained, 'ether')} GNO NO")
                    
                    # Show transaction link
                    print(f"Transaction: https://gnosisscan.io/tx/{tx_hash.hex()}")
                    
                    # We found a working combination, so we can exit
                    return True
                else:
                    print(f"❌ Swap failed with {amount_label} and price limit {price_label}")
            except Exception as e:
                print(f"❌ Swap error: {str(e)}")
    
    print("\n❌ All combinations failed")
    return False

if __name__ == "__main__":
    main() 