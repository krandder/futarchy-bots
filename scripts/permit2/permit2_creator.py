from web3 import Web3
import json
import os
import sys
from eth_account.messages import encode_typed_data
from hexbytes import HexBytes

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.constants import (
    CONTRACT_ADDRESSES, TOKEN_CONFIG, DEFAULT_PERMIT_CONFIG
)

# Setup - more configurable version
RPC_URL = os.environ.get('RPC_URL', 'https://gnosis-mainnet.public.blastapi.io')
CHAIN_ID = int(os.environ.get('CHAIN_ID', '100'))  # Default to Gnosis Chain
private_key = os.environ.get('PRIVATE_KEY')

# Token and contract addresses from constants
TOKEN_ADDRESS = os.environ.get('TOKEN_ADDRESS', TOKEN_CONFIG["currency"]["address"])  # Default to sDAI
PERMIT2_ADDRESS = os.environ.get('PERMIT2_ADDRESS', CONTRACT_ADDRESSES["permit2"])
SPENDER_ADDRESS = os.environ.get('SPENDER_ADDRESS', CONTRACT_ADDRESSES["batchRouter"])  # Default to BatchRouter

# Connect to blockchain
w3 = Web3(Web3.HTTPProvider(RPC_URL))
if not w3.is_connected():
    raise Exception(f"Failed to connect to RPC endpoint: {RPC_URL}")

# Set up account from private key
if not private_key:
    raise Exception("PRIVATE_KEY environment variable not set. Please set it before running this script.")

account = w3.eth.account.from_key(private_key)
user_address = account.address

# Convert addresses to checksum format
token_address = Web3.to_checksum_address(TOKEN_ADDRESS)
permit2_address = Web3.to_checksum_address(PERMIT2_ADDRESS)
spender_address = Web3.to_checksum_address(SPENDER_ADDRESS)

print(f"Connected to chain ID: {CHAIN_ID}")
print(f"User address: {user_address}")
print(f"Token address: {token_address}")
print(f"Permit2 address: {permit2_address}")
print(f"Spender address: {spender_address}")

# Permit2 ABI with necessary functions
permit2_abi = [
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "owner",
                "type": "address"
            },
            {
                "components": [
                    {
                        "components": [
                            {
                                "internalType": "address",
                                "name": "token",
                                "type": "address"
                            },
                            {
                                "internalType": "uint160",
                                "name": "amount",
                                "type": "uint160"
                            },
                            {
                                "internalType": "uint48",
                                "name": "expiration",
                                "type": "uint48"
                            },
                            {
                                "internalType": "uint48",
                                "name": "nonce",
                                "type": "uint48"
                            }
                        ],
                        "internalType": "struct IAllowanceTransfer.PermitDetails",
                        "name": "details",
                        "type": "tuple"
                    },
                    {
                        "internalType": "address",
                        "name": "spender",
                        "type": "address"
                    },
                    {
                        "internalType": "uint256",
                        "name": "sigDeadline",
                        "type": "uint256"
                    }
                ],
                "internalType": "struct IAllowanceTransfer.PermitSingle",
                "name": "permitSingle",
                "type": "tuple"
            },
            {
                "internalType": "bytes",
                "name": "signature",
                "type": "bytes"
            }
        ],
        "name": "permit",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "owner",
                "type": "address"
            },
            {
                "internalType": "address",
                "name": "token",
                "type": "address"
            },
            {
                "internalType": "address",
                "name": "spender",
                "type": "address"
            }
        ],
        "name": "allowance",
        "outputs": [
            {
                "internalType": "uint160",
                "name": "amount",
                "type": "uint160"
            },
            {
                "internalType": "uint48",
                "name": "expiration",
                "type": "uint48"
            },
            {
                "internalType": "uint48",
                "name": "nonce",
                "type": "uint48"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# Initialize Permit2 contract
permit2 = w3.eth.contract(address=permit2_address, abi=permit2_abi)

def create_permit(amount, expiration_hours=24, sig_deadline_hours=1):
    """
    Create and send a Permit2 permit for the specified token and spender.
    
    Args:
        amount: The amount to approve (as an integer with correct decimals)
        expiration_hours: How many hours until the permit expires
        sig_deadline_hours: How many hours until the signature expires
        
    Returns:
        tx_hash: The transaction hash of the sent transaction
    """
    # 1. Check current allowance and nonce
    try:
        current_allowance = permit2.functions.allowance(user_address, token_address, spender_address).call()
        current_amount, expiration, current_nonce = current_allowance
        
        print("\nCurrent Permit2 allowance:")
        print(f"Amount: {current_amount}")
        print(f"Expiration: {expiration}")
        print(f"Nonce from allowance: {current_nonce}")
        
        timestamp = w3.eth.get_block('latest')['timestamp']
        print(f"Current timestamp: {timestamp}")
        
        if expiration > timestamp:
            print("Status: VALID - Allowance is still valid")
        else:
            print("Status: EXPIRED - Allowance has expired")
            
    except Exception as e:
        print(f"Error checking allowance: {e}")
        return None

    # 2. Create and sign a permit message
    # Permit2 expects the exact current nonce
    expiration_time = int(w3.eth.get_block('latest')['timestamp'] + 60 * 60 * expiration_hours)
    sig_deadline = int(w3.eth.get_block('latest')['timestamp'] + 60 * 60 * sig_deadline_hours)

    print(f"\nCreating permit with:")
    print(f"Amount: {amount}")
    print(f"Expiration: {expiration_time} ({expiration_hours} hours from now)")
    print(f"Using nonce value: {current_nonce}")

    # Prepare the typed data structure according to EIP-712 for Permit2
    typed_data = {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"}
            ],
            "PermitDetails": [
                {"name": "token", "type": "address"},
                {"name": "amount", "type": "uint160"},
                {"name": "expiration", "type": "uint48"},
                {"name": "nonce", "type": "uint48"}
            ],
            "PermitSingle": [
                {"name": "details", "type": "PermitDetails"},
                {"name": "spender", "type": "address"},
                {"name": "sigDeadline", "type": "uint256"}
            ]
        },
        "domain": {
            "name": "Permit2",
            "chainId": CHAIN_ID,
            "verifyingContract": permit2_address
        },
        "primaryType": "PermitSingle",
        "message": {
            "details": {
                "token": token_address,
                "amount": amount,
                "expiration": expiration_time,
                "nonce": current_nonce
            },
            "spender": spender_address,
            "sigDeadline": sig_deadline
        }
    }

    print("\nTyped data for signing:", json.dumps(typed_data, indent=2))

    # Sign the message
    encoded_message = encode_typed_data(full_message=typed_data)
    signed_message = account.sign_message(encoded_message)
    signature = signed_message.signature.hex()

    print(f"Signature: {signature}")

    # 3. Send the permit transaction directly to Permit2
    permit_single = (
        (token_address, amount, expiration_time, current_nonce),  # details - using current nonce
        spender_address,  # spender
        sig_deadline  # sigDeadline
    )

    print("\nSending permit transaction to Permit2...")
    try:
        # Convert hex signature to bytes
        signature_bytes = HexBytes(signature)
        
        tx = permit2.functions.permit(
            user_address,
            permit_single,
            signature_bytes
        ).build_transaction({
            'from': user_address,
            'nonce': w3.eth.get_transaction_count(user_address),
            'gas': 300000,
            'gasPrice': w3.eth.gas_price,
            'chainId': CHAIN_ID
        })
        
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_hash_hex = tx_hash.hex()
        print(f"Transaction sent: {tx_hash_hex}")
        
        # Wait for the transaction to be mined
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Transaction status: {'SUCCESS' if receipt.status == 1 else 'FAILED'}")
        print(f"Gas used: {receipt.gasUsed}")
        
        # 4. Verify the allowance was updated
        print("\nVerifying allowance after permit...")
        new_allowance = permit2.functions.allowance(user_address, token_address, spender_address).call()
        new_amount, new_expiration, new_nonce = new_allowance
        
        print(f"New amount: {new_amount}")
        print(f"New expiration: {new_expiration}")
        print(f"New nonce: {new_nonce}")
        
        if new_amount > 0 and new_expiration > w3.eth.get_block('latest')['timestamp']:
            print("✅ PERMIT SUCCESSFUL: Spender now has permission to spend your tokens through Permit2")
        else:
            print("❌ PERMIT FAILED: Spender still doesn't have permission")
            
        return tx_hash_hex
    except Exception as e:
        print(f"Error sending permit transaction: {e}")
        return None

# If run directly, create a permit with default values
if __name__ == "__main__":
    # Default amount - 0.001 tokens with 18 decimals
    default_amount = 1000000000000000
    
    # Allow overriding via environment variables
    amount = int(os.environ.get('PERMIT_AMOUNT', default_amount))
    
    tx_hash = create_permit(amount)
    if tx_hash:
        print(f"\nPermit transaction completed. View on explorer:")
        print(f"https://gnosisscan.io/tx/{tx_hash}")
    else:
        print("\nPermit transaction failed. Please check the errors above.") 