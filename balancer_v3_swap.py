import json
import os
import time
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to Gnosis Chain
rpc_url = os.getenv('GNOSIS_RPC_URL')
w3 = Web3(Web3.HTTPProvider(rpc_url))

# Check connection
if not w3.is_connected():
    print("❌ Failed to connect to Gnosis Chain")
    exit(1)

print(f"✅ Connected to Gnosis Chain (Chain ID: {w3.eth.chain_id})")

# Load private key
private_key = os.getenv('PRIVATE_KEY')
if not private_key:
    print("❌ No private key found in .env file")
    exit(1)

account = Account.from_key(private_key)
address = account.address
print(f"🔑 Using account: {address}")

# Contract addresses - UPDATED based on successful example
BATCH_ROUTER_ADDRESS = w3.to_checksum_address('0xe2fa4e1d17725e72dcdafe943ecf45df4b9e285b')  # Correct router address
SDAI_ADDRESS = w3.to_checksum_address('0xaf204776c7245bF4147c2612BF6e5972Ee483701')
WAGNO_ADDRESS = w3.to_checksum_address('0x7c16F0185A26Db0AE7a9377f23BC18ea7ce5d644')
GNO_ADDRESS = w3.to_checksum_address('0x9c58bacc331c9aa871afd802db6379a98e80cedb')  # Added GNO token
POOL_ADDRESS = w3.to_checksum_address('0xD1D7Fa8871d84d0E77020fc28B7Cd5718C446522')

# NOTE: For Balancer V3, Permit2 approvals are required
# This script uses the traditional approval method which may not work for all V3 swaps
# For a complete implementation, consider using the Balancer SDK with Permit2
# See docs/balancer_v3_swapping.md for more information

# ERC20 ABI (minimal for approval)
ERC20_ABI = [
    {"inputs":[{"name":"owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]

# Load BatchRouter ABI
try:
    with open('config/batch_router_abi.json', 'r') as abi_file:
        batch_router_abi = json.load(abi_file)
except Exception as e:
    print(f"❌ Error loading ABI: {e}")
    exit(1)

# Initialize contracts
batch_router = w3.eth.contract(address=BATCH_ROUTER_ADDRESS, abi=batch_router_abi)
sdai_token = w3.eth.contract(address=SDAI_ADDRESS, abi=ERC20_ABI)

# Check token balance
sdai_balance = sdai_token.functions.balanceOf(address).call()
print(f"💰 sDAI Balance: {w3.from_wei(sdai_balance, 'ether')}")

if sdai_balance == 0:
    print("❌ No sDAI balance to swap")
    exit(1)

# Amount to swap (use a small amount for testing)
amount_to_swap = min(sdai_balance, w3.to_wei(0.01, 'ether'))
print(f"🔄 Swapping {w3.from_wei(amount_to_swap, 'ether')} sDAI to GNO via waGNO")

# Helper function to get raw transaction bytes
def get_raw_transaction(signed_tx):
    """Get raw transaction bytes, compatible with different web3.py versions."""
    if hasattr(signed_tx, 'rawTransaction'):
        return signed_tx.rawTransaction
    elif hasattr(signed_tx, 'raw_transaction'):
        return signed_tx.raw_transaction
    else:
        # Try to access the raw transaction directly
        return signed_tx.raw

# Skip approval check and go straight to swap
print("✅ Assuming BatchRouter is already approved to spend sDAI")
print("⚠️ Note: Balancer V3 typically requires Permit2 approvals, which this script doesn't implement")

# Prepare swap parameters
try:
    # Define swap path with TWO steps (matching the successful example)
    paths = [{
        'tokenIn': SDAI_ADDRESS,
        'steps': [
            # Step 1: sDAI → waGNO through pool
            {
                'pool': POOL_ADDRESS,
                'tokenOut': WAGNO_ADDRESS,
                'isBuffer': False
            },
            # Step 2: waGNO → GNO using buffer
            {
                'pool': WAGNO_ADDRESS,
                'tokenOut': GNO_ADDRESS,
                'isBuffer': True
            }
        ],
        'exactAmountIn': amount_to_swap,
        'minAmountOut': int(amount_to_swap * 0.9)  # 10% slippage
    }]
    
    # Set deadline to a very large value (matching the successful example)
    deadline = 9007199254740991
    
    # Execute swap with swapExactIn
    print("Executing swap with swapExactIn...")
    swap_tx = batch_router.functions.swapExactIn(
        paths,
        deadline,
        False,  # wethIsEth
        b''     # userData
    ).build_transaction({
        'from': address,
        'nonce': w3.eth.get_transaction_count(address),
        'gas': 700000,
        'gasPrice': w3.eth.gas_price,
        'value': 0
    })
    
    # Sign and send transaction
    signed_tx = account.sign_transaction(swap_tx)
    tx_hash = w3.eth.send_raw_transaction(get_raw_transaction(signed_tx))
    print(f"📤 Swap transaction sent: {tx_hash.hex()}")
    
    # Wait for swap transaction to be mined
    print("⏳ Waiting for transaction confirmation...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    if receipt['status'] == 1:
        print("✅ Swap successful!")
        
        # Check new balances
        new_sdai_balance = sdai_token.functions.balanceOf(address).call()
        print(f"New sDAI Balance: {w3.from_wei(new_sdai_balance, 'ether')}")
        
        # Initialize GNO token contract
        gno_token = w3.eth.contract(address=GNO_ADDRESS, abi=ERC20_ABI)
        gno_balance = gno_token.functions.balanceOf(address).call()
        print(f"GNO Balance: {w3.from_wei(gno_balance, 'ether')}")
    else:
        print("❌ Swap failed")
        print("⚠️ This may be due to missing Permit2 approvals required for V3 swaps")
        
except Exception as e:
    print(f"❌ Error during swap: {e}")
    print("⚠️ If the error is related to approvals, consider implementing Permit2 approvals")
    exit(1) 