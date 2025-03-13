import json
import os
from web3 import Web3
from pathlib import Path

# --- Configuration ---
# Load configuration from environment variables with defaults
RPC_URL = os.environ.get('GNOSIS_RPC_URL', 'https://gnosis-mainnet.public.blastapi.io')
ROUTER_ADDRESS = Web3.to_checksum_address(os.environ.get('BATCH_ROUTER_ADDRESS', '0xe2fa4e1d17725e72dcdAfe943Ecf45dF4B9E285b'))
PRIVATE_KEY = os.environ.get('PRIVATE_KEY')

# Token addresses - configurable via environment variables
TOKEN_IN_ADDRESS = os.environ.get('TOKEN_IN_ADDRESS', '0xaf204776c7245bf4147c2612bf6e5972ee483701')  # Default to sDAI
TOKEN_OUT_ADDRESS = os.environ.get('TOKEN_OUT_ADDRESS', '0x7c16f0185a26db0ae7a9377f23bc18ea7ce5d644')  # Default to waGNO
POOL_ADDRESS = os.environ.get('POOL_ADDRESS', '0xd1d7fa8871d84d0e77020fc28b7cd5718c446522')  # Default to sDAI-waGNO pool

# Token names for display
TOKEN_IN_NAME = os.environ.get('TOKEN_IN_NAME', 'sDAI')
TOKEN_OUT_NAME = os.environ.get('TOKEN_OUT_NAME', 'waGNO')

# Amount to swap - configurable via environment variable
# Default is 0.0001 tokens with 18 decimals
DEFAULT_AMOUNT = 100000000000000  # 0.0001 tokens with 18 decimals
AMOUNT_TO_SWAP = int(os.environ.get('AMOUNT_TO_SWAP', DEFAULT_AMOUNT))

# Chain ID for Gnosis Chain is 100
CHAIN_ID = int(os.environ.get('CHAIN_ID', '100'))

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
    if not PRIVATE_KEY:
        print("Error: Private key not set. Please set the PRIVATE_KEY environment variable.")
        return
        
    account = w3.eth.account.from_key(PRIVATE_KEY)
    sender_address = account.address
    print("Using account:", sender_address)

    # --- Instantiate the Router Contract ---
    router = w3.eth.contract(address=ROUTER_ADDRESS, abi=abi)

    # --- Convert addresses to checksum format ---
    token_in = Web3.to_checksum_address(TOKEN_IN_ADDRESS)
    token_out = Web3.to_checksum_address(TOKEN_OUT_ADDRESS)
    pool = Web3.to_checksum_address(POOL_ADDRESS)

    print(f"\nSwap Configuration:")
    print(f"Token In: {TOKEN_IN_NAME} ({token_in})")
    print(f"Token Out: {TOKEN_OUT_NAME} ({token_out})")
    print(f"Pool: {pool}")
    print(f"Amount to swap: {AMOUNT_TO_SWAP} ({w3.from_wei(AMOUNT_TO_SWAP, 'ether')} {TOKEN_IN_NAME})")
    
    # --- Define Swap Parameters ---
    # Simplified: Only one step from token_in to token_out
    paths = [
        {
            "tokenIn": token_in,
            "steps": [
                {
                    "pool": pool,
                    "tokenOut": token_out,
                    "isBuffer": False
                }
            ],
            "exactAmountIn": AMOUNT_TO_SWAP,
            "minAmountOut": 0  # Set very low for testing purposes
        }
    ]
    
    # First query to see expected output
    print("\nQuerying expected swap output...")
    try:
        expected_output = router.functions.querySwapExactIn(
            paths,
            sender_address,
            '0x'  # empty user data
        ).call()
        
        print(f"Expected output: {expected_output}")
        if expected_output and expected_output[0]:
            expected_amount = expected_output[0][0]
            print(f"Expected {TOKEN_OUT_NAME} output: {w3.from_wei(expected_amount, 'ether')} {TOKEN_OUT_NAME}")
            
            # Set minAmountOut to 80% of expected output
            min_amount_out = int(expected_amount * 0.8)
            paths[0]["minAmountOut"] = min_amount_out
            print(f"Setting minAmountOut to 80% of expected: {w3.from_wei(min_amount_out, 'ether')} {TOKEN_OUT_NAME}")
        else:
            print("Warning: Could not determine expected output. Proceeding with zero minAmountOut.")
    except Exception as e:
        print(f"Error during query: {e}")
        # Still proceed with the swap, but with zero minAmountOut
        print("Proceeding with zero minAmountOut")
    
    deadline = w3.eth.get_block('latest')['timestamp'] + (60 * 60)  # 1 hour from now
    wethIsEth = False  # Not using ETH directly
    userData = b""  # no additional data

    try:
        # --- Build the Transaction ---
        # Get current gas price with a small buffer for faster inclusion
        gas_price = int(w3.eth.gas_price * 1.1)
        
        print("\nBuilding transaction...")
        tx = router.functions.swapExactIn(
            paths, 
            deadline, 
            wethIsEth, 
            userData
        ).build_transaction({
            "chainId": CHAIN_ID,
            "from": sender_address,
            "nonce": w3.eth.get_transaction_count(sender_address),
            "gas": 1000000,  # Higher gas limit
            "gasPrice": gas_price,
            "value": 0  # no ETH sent since wethIsEth is false
        })

        print("Transaction built successfully")

        # --- Sign the Transaction ---
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)

        # --- Send the Transaction ---
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_hash_hex = tx_hash.hex()
        print("Transaction sent. Tx hash:", tx_hash_hex)
        print(f"View on block explorer: https://gnosisscan.io/tx/{tx_hash_hex}")

        # --- Wait for Receipt ---
        print("Waiting for transaction confirmation...")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        # Check if transaction was successful
        if receipt.status == 1:
            print("✅ Swap executed successfully!")
            
            # Calculate gas used in USD (approximate)
            gas_used = receipt.gasUsed
            gas_price_gwei = w3.from_wei(receipt.effectiveGasPrice, 'gwei')
            gas_cost_eth = gas_used * receipt.effectiveGasPrice / 1e18
            print(f"Gas used: {gas_used}")
            print(f"Gas price: {gas_price_gwei} Gwei")
            print(f"Gas cost: {gas_cost_eth:.6f} xDAI")
        else:
            print("❌ Swap failed! Check transaction details on block explorer.")
            print(f"Transaction hash: {tx_hash_hex}")
            print(f"Gas used: {receipt.gasUsed}")
            
    except Exception as e:
        print(f"Error during transaction: {e}")

if __name__ == "__main__":
    main()
