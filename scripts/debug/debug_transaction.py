import os
import json
import argparse
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def debug_transaction(w3, tx_hash):
    """
    Debug a transaction to get the exact error message.
    
    Args:
        w3: Web3 instance
        tx_hash: Transaction hash to debug
        
    Returns:
        dict: Debug information
    """
    # Get transaction receipt
    receipt = w3.eth.get_transaction_receipt(tx_hash)
    
    # Get transaction
    tx = w3.eth.get_transaction(tx_hash)
    
    # Try to get debug trace
    debug_trace = None
    try:
        debug_trace = w3.provider.make_request("debug_traceTransaction", [tx_hash, {"tracer": "callTracer"}])
    except Exception as e:
        print(f"Warning: Could not get debug trace: {e}")
    
    # Try to get revert reason
    revert_reason = None
    try:
        # Replay the transaction with eth_call to get the revert reason
        call_params = {
            'from': tx['from'],
            'to': tx['to'],
            'data': tx['input'],
            'value': tx['value'],
            'gas': tx['gas'],
            'gasPrice': tx['gasPrice'],
        }
        
        # Try to execute the transaction with eth_call
        w3.eth.call(call_params, tx['blockNumber'] - 1)
    except Exception as e:
        # Extract the revert reason from the error message
        revert_reason = str(e)
    
    return {
        'transaction': {
            'hash': tx_hash,
            'from': tx['from'],
            'to': tx['to'],
            'value': tx['value'],
            'gas': tx['gas'],
            'gasPrice': tx['gasPrice'],
            'nonce': tx['nonce'],
            'input': tx['input'],
        },
        'receipt': {
            'status': receipt['status'],
            'gasUsed': receipt['gasUsed'],
            'logs': receipt['logs'],
        },
        'debug_trace': debug_trace,
        'revert_reason': revert_reason,
    }

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Debug a transaction')
    parser.add_argument('tx_hash', type=str, help='Transaction hash to debug')
    args = parser.parse_args()
    
    # Connect to Gnosis Chain
    rpc_url = os.getenv("RPC_URL", "https://rpc.gnosischain.com")
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    # Check connection
    if not w3.is_connected():
        print("❌ Failed to connect to the blockchain")
        return
    
    print(f"✅ Connected to {rpc_url}")
    
    # Debug transaction
    tx_hash = args.tx_hash
    debug_info = debug_transaction(w3, tx_hash)
    
    # Print debug information
    print("\n=== Transaction Information ===")
    print(f"Hash: {debug_info['transaction']['hash']}")
    print(f"From: {debug_info['transaction']['from']}")
    print(f"To: {debug_info['transaction']['to']}")
    print(f"Value: {debug_info['transaction']['value']}")
    print(f"Gas: {debug_info['transaction']['gas']}")
    print(f"Gas Price: {debug_info['transaction']['gasPrice']}")
    print(f"Nonce: {debug_info['transaction']['nonce']}")
    
    print("\n=== Receipt Information ===")
    print(f"Status: {debug_info['receipt']['status']}")
    print(f"Gas Used: {debug_info['receipt']['gasUsed']}")
    print(f"Logs: {len(debug_info['receipt']['logs'])}")
    
    print("\n=== Revert Reason ===")
    print(debug_info['revert_reason'])
    
    print("\n=== Debug Trace ===")
    if debug_info['debug_trace']:
        print(json.dumps(debug_info['debug_trace'], indent=2))
    else:
        print("No debug trace available")

if __name__ == "__main__":
    main() 