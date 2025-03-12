import json
import os
from web3 import Web3
from pathlib import Path

# --- Configuration ---
# Gnosis Chain public RPC endpoint
RPC_URL = "https://rpc.gnosischain.com"
# Router contract address (replace with the actual address)
ROUTER_ADDRESS = Web3.to_checksum_address("0xe2fa4e1d17725e72dcdAfe943Ecf45dF4B9E285b")  # Balancer Router on Gnosis Chain
# Your private key (store securely, never commit your real key)
PRIVATE_KEY = os.environ.get("PRIVATE_KEY", "YOUR_PRIVATE_KEY")  # Better to use environment variable

# Chain ID for Gnosis Chain is 100
CHAIN_ID = 100

# --- Load ABI from file ---
def load_abi():
    """Load the Balancer Router ABI from a JSON file."""
    reference_path = Path(__file__).parent / ".reference" / "balancer_router.abi.json"
    if reference_path.exists():
        with open(reference_path, 'r') as f:
            return json.load(f)
    else:
        raise FileNotFoundError(f"ABI file not found at {reference_path}")

# --- Connect to Gnosis Chain ---
def connect_to_chain():
    """Establish connection to the Gnosis Chain RPC endpoint."""
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        raise Exception(f"Failed to connect to the RPC endpoint: {RPC_URL}")
    return w3

def main():
    """Main function to execute a Balancer swap on Gnosis Chain."""
    # Load ABI and connect to chain
    try:
        abi = load_abi()
        w3 = connect_to_chain()
    except Exception as e:
        print(f"Initialization error: {e}")
        return

    # Set up our account (address derived from the private key)
    if PRIVATE_KEY == "YOUR_PRIVATE_KEY":
        print("Error: Private key not set. Please set the PRIVATE_KEY environment variable.")
        return
        
    account = w3.eth.account.from_key(PRIVATE_KEY)
    sender_address = account.address
    print("Using account:", sender_address)

    # --- Instantiate the Router Contract ---
    router = w3.eth.contract(address=ROUTER_ADDRESS, abi=abi)

    # --- Define Swap Parameters ---
    # We need to prepare the parameters for swapExactIn:
    paths = [
        {
            "tokenIn": Web3.to_checksum_address("0xaf204776c7245bf4147c2612bf6e5972ee483701"),  # Input token
            "steps": [
                {
                    "pool": Web3.to_checksum_address("0xd1d7fa8871d84d0e77020fc28b7cd5718c446522"),  # First pool
                    "tokenOut": Web3.to_checksum_address("0x7c16f0185a26db0ae7a9377f23bc18ea7ce5d644"),  # Intermediate token
                    "isBuffer": False
                },
                {
                    "pool": Web3.to_checksum_address("0x7c16f0185a26db0ae7a9377f23bc18ea7ce5d644"),  # Second pool
                    "tokenOut": Web3.to_checksum_address("0x9c58bacc331c9aa871afd802db6379a98e80cedb"),  # Final token
                    "isBuffer": True
                }
            ],
            "exactAmountIn": int("10000000000000000"),  # 0.01 tokens (depending on decimals)
            "minAmountOut": int("92622554828851")  # Minimum amount to receive
        }
    ]
    deadline = 9007199254740991  # a far future deadline
    wethIsEth = False  # Not using ETH directly
    userData = b""  # no additional data

    try:
        # --- Build the Transaction ---
        # Get current gas price with a small buffer for faster inclusion
        gas_price = int(w3.eth.gas_price * 1.1)
        
        # The swapExactIn function is payable; in our case we don't need to send ETH
        tx = router.functions.swapExactIn(
            paths, 
            deadline, 
            wethIsEth, 
            userData
        ).build_transaction({
            "chainId": CHAIN_ID,
            "from": sender_address,
            "nonce": w3.eth.get_transaction_count(sender_address),
            "gas": 800000,  # Higher gas limit for complex swaps
            "gasPrice": gas_price,
            "value": 0  # no ETH sent since wethIsEth is false
        })

        print("Transaction built successfully")

        # --- Sign the Transaction ---
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)

        # --- Send the Transaction ---
        # Use raw_transaction attribute (updated naming in web3.py v6+)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print("Transaction sent. Tx hash:", tx_hash.hex())
        print(f"View on block explorer: https://gnosisscan.io/tx/{tx_hash.hex()}")

        # --- Wait for Receipt ---
        print("Waiting for transaction confirmation...")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        # Check if transaction was successful
        if receipt.status == 1:
            print("Swap executed successfully!")
            
            # Calculate gas used in USD (approximate)
            gas_used = receipt.gasUsed
            gas_price_gwei = w3.from_wei(receipt.effectiveGasPrice, 'gwei')
            gas_cost_eth = gas_used * receipt.effectiveGasPrice / 1e18
            print(f"Gas used: {gas_used}")
            print(f"Gas price: {gas_price_gwei} Gwei")
            print(f"Gas cost: {gas_cost_eth:.6f} xDAI")
        else:
            print("Swap failed! Check transaction details on block explorer.")
            
    except Exception as e:
        print(f"Error during transaction: {e}")

if __name__ == "__main__":
    main()
