import os
from web3 import Web3
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

# Common Permit2 addresses on various chains
PERMIT2_ADDRESSES = {
    "Ethereum": "0x000000000022D473030F116dDEE9F6B43aC78BA3",
    "Arbitrum": "0x000000000022D473030F116dDEE9F6B43aC78BA3",
    "Optimism": "0x000000000022D473030F116dDEE9F6B43aC78BA3",
    "Polygon": "0x000000000022D473030F116dDEE9F6B43aC78BA3",
    "Base": "0x000000000022D473030F116dDEE9F6B43aC78BA3",
    "Gnosis": "0x000000000022D473030F116dDEE9F6B43aC78BA3",  # Assuming same as Ethereum
}

# Check if the Permit2 contract exists at the expected address
permit2_address = w3.to_checksum_address(PERMIT2_ADDRESSES["Gnosis"])
print(f"Checking Permit2 contract at: {permit2_address}")

# Check if there's code at the address
code = w3.eth.get_code(permit2_address)
if code and code != "0x":
    print("✅ Permit2 contract found!")
    
    # Try to get the contract's bytecode size
    print(f"Contract bytecode size: {len(code)} bytes")
    
    # Check if the account has a balance
    balance = w3.eth.get_balance(permit2_address)
    print(f"Contract balance: {w3.from_wei(balance, 'ether')} ETH")
else:
    print("❌ No contract found at the expected Permit2 address")
    print("This suggests that Permit2 might not be deployed on Gnosis Chain")
    print("or it might be deployed at a different address.")

print("\nRecommendations:")
print("1. Check the Balancer documentation for the correct Permit2 address on Gnosis Chain")
print("2. Consider using the Balancer SDK which handles Permit2 approvals automatically")
print("3. For Python implementation, you might need to deploy your own Permit2 contract") 