"""
Web3 utility functions for connecting to the blockchain.
"""

import os
from web3 import Web3, HTTPProvider

def setup_web3_connection():
    """
    Set up a connection to the Gnosis Chain.
    
    Returns:
        Web3: A Web3 instance connected to the Gnosis Chain.
    """
    # Try to get RPC URL from environment variable
    rpc_url = os.environ.get('GNOSIS_RPC_URL', 'https://rpc.gnosischain.com')
    
    # Create Web3 instance
    w3 = Web3(HTTPProvider(rpc_url))
    
    # Check connection
    if not w3.is_connected():
        raise ConnectionError(f"Failed to connect to Gnosis Chain at {rpc_url}")
    
    return w3

def simulate_transaction_with_eth_call(w3, contract_address, contract_abi, function_name, function_args, from_address=None):
    """
    Simulate a transaction using eth_call to get the exact output amount.
    
    Args:
        w3: Web3 instance
        contract_address: Address of the contract
        contract_abi: ABI of the contract
        function_name: Name of the function to call
        function_args: Arguments to pass to the function
        from_address: Address to use as the sender (default: zero address)
        
    Returns:
        Any: The result of the function call
    """
    if from_address is None:
        from_address = "0x0000000000000000000000000000000000000000"
    
    try:
        # Create contract instance
        contract = w3.eth.contract(
            address=w3.to_checksum_address(contract_address),
            abi=contract_abi
        )
        
        # Get the function from the contract
        contract_function = getattr(contract.functions, function_name)
        
        # Build the transaction
        tx = contract_function(*function_args).build_transaction({
            'from': w3.to_checksum_address(from_address),
            'gas': 5000000,
            'gasPrice': w3.eth.gas_price,
            'value': 0,
            'nonce': 0,  # Doesn't matter for eth_call
        })
        
        # Simulate the transaction using eth_call
        result = w3.eth.call(tx)
        
        # Decode the result using the contract's function
        decoded_result = contract_function(*function_args).call({
            'from': w3.to_checksum_address(from_address)
        })
        
        return decoded_result
        
    except Exception as e:
        print(f"Error simulating transaction {function_name}: {e}")
        import traceback
        traceback.print_exc()
        return None 