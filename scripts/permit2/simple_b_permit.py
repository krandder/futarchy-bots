import os
import json
from web3 import Web3, HTTPProvider
from eth_account import Account
from eth_account.messages import encode_typed_data

# Load environment variables
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
USER_ADDRESS = os.getenv("USER_ADDRESS")
GNOSIS_RPC_URL = os.getenv("GNOSIS_RPC_URL")
BATCH_ROUTER_ADDRESS = os.getenv("BATCH_ROUTER_ADDRESS")
if not BATCH_ROUTER_ADDRESS:
    # Default Balancer Vault address on Gnosis Chain
    BATCH_ROUTER_ADDRESS = "0xBA12222222228d8Ba445958a75a0704d566BF2C8"
PERMIT2_ADDRESS = "0x000000000022d473030f116ddee9f6b43ac78ba3"
CHAIN_ID = 100

# Convert all addresses to checksum format
USER_ADDRESS = Web3.to_checksum_address(USER_ADDRESS)
BATCH_ROUTER_ADDRESS = Web3.to_checksum_address(BATCH_ROUTER_ADDRESS)
PERMIT2_ADDRESS = Web3.to_checksum_address(PERMIT2_ADDRESS)
TOKEN_ADDRESS = Web3.to_checksum_address(os.getenv("TOKEN_ADDRESS"))
VAULT_ADDRESS = Web3.to_checksum_address(os.getenv("VAULT_ADDRESS"))

print(f"Using RPC URL: {GNOSIS_RPC_URL}")
print(f"User address: {USER_ADDRESS}")
print(f"Batch router address: {BATCH_ROUTER_ADDRESS}")
print(f"Permit2 address: {PERMIT2_ADDRESS}")

# Initialize Web3 instance
w3 = Web3(HTTPProvider(GNOSIS_RPC_URL))

# Load BatchRouter ABI from file
with open('.reference/balancer_router.abi.json', 'r') as f:
    batch_router_abi = json.load(f)

# Initialize contract with checksummed address
router = w3.eth.contract(address=BATCH_ROUTER_ADDRESS, abi=batch_router_abi)

# Permit2 typed data structure (simplified example)
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
        "PermitBatch": [
            {"name": "details", "type": "PermitDetails[]"},
            {"name": "spender", "type": "address"},
            {"name": "sigDeadline", "type": "uint256"}
        ]
    },
    "domain": {
        "name": "Permit2",
        "chainId": CHAIN_ID,
        "verifyingContract": PERMIT2_ADDRESS
    },
    "primaryType": "PermitBatch",
    "message": {
        "details": [
            {
                "token": TOKEN_ADDRESS,
                "amount": int(os.getenv("AMOUNT")),
                "expiration": int(os.getenv("EXPIRATION")),
                "nonce": int(os.getenv("NONCE"))
            }
        ],
        "spender": VAULT_ADDRESS,
        "sigDeadline": int(os.getenv("SIG_DEADLINE"))
    }
}

print("Typed data for signing:", json.dumps(typed_data, indent=2))

# Sign the Permit2 message using the updated method
encoded_message = encode_typed_data(full_message=typed_data)
private_key = os.getenv("PRIVATE_KEY")
signed_message = Account.sign_message(encoded_message, private_key=private_key)
permit2_signature = signed_message.signature

print(f"Signature: {permit2_signature.hex()}")

# Print parameters for verification
print(f"TOKEN_ADDRESS: {TOKEN_ADDRESS}")
print(f"AMOUNT: {os.getenv('AMOUNT')}")
print(f"EXPIRATION: {os.getenv('EXPIRATION')}")
print(f"NONCE: {os.getenv('NONCE')}")
print(f"VAULT_ADDRESS: {VAULT_ADDRESS}")
print(f"SIG_DEADLINE: {os.getenv('SIG_DEADLINE')}")

# Create the permit batch tuple for the contract call
permit_batch_details = [(TOKEN_ADDRESS, int(os.getenv("AMOUNT")), int(os.getenv("EXPIRATION")), int(os.getenv("NONCE")))]
permit_batch = (permit_batch_details, VAULT_ADDRESS, int(os.getenv("SIG_DEADLINE")))

print("Permit batch for contract call:", permit_batch)

# Prepare permitBatchAndCall transaction (no permit1, no multicall)
tx = router.functions.permitBatchAndCall(
    [],  # empty permitBatch
    [],  # empty permitSignatures
    permit_batch,  # Permit2 batch
    permit2_signature,
    []  # empty multicallData
).build_transaction({
    'from': USER_ADDRESS,
    'nonce': w3.eth.get_transaction_count(USER_ADDRESS),
    'gasPrice': w3.eth.gas_price,
    'chainId': CHAIN_ID,
    'gas': 500000  # Set a higher gas limit to ensure transaction doesn't fail due to gas
})

print("Transaction data:", tx)

# Sign and send transaction
signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
print("Signed transaction:", signed_tx)

# The raw_transaction attribute might be named differently in newer web3.py versions
if hasattr(signed_tx, 'rawTransaction'):
    raw_tx = signed_tx.rawTransaction
elif hasattr(signed_tx, 'raw_transaction'):
    raw_tx = signed_tx.raw_transaction
else:
    # Print all available attributes for debugging
    print("Available attributes:", dir(signed_tx))
    # Try accessing as a dictionary
    raw_tx = signed_tx.get('rawTransaction') or signed_tx.get('raw_transaction')
    if not raw_tx:
        raise ValueError("Could not find rawTransaction in signed transaction object")

tx_hash = w3.eth.send_raw_transaction(raw_tx)

print(f"Transaction sent! Hash: {tx_hash.hex()}")
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(f"Transaction confirmed in block {receipt.blockNumber}, status: {receipt.status}")
