import os
import pkg_resources
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv


def setup_web3_connection(rpc_url=None):
    """
    Set up a Web3 connection with appropriate middleware for Gnosis Chain.
    
    Args:
        rpc_url: RPC URL to connect to (will use env var GNOSIS_RPC_URL if not provided)
        
    Returns:
        web3 instance
    """
    # Load environment variables
    load_dotenv()
    
    # Use provided RPC URL or get from environment
    if not rpc_url:
        rpc_url = os.getenv('GNOSIS_RPC_URL')
        
    # If no URL from env, try these endpoints in order
    if not rpc_url:
        rpc_endpoints = [
            'https://rpc.gnosischain.com',       # Official Gnosis RPC
            'https://gnosis.publicnode.com',     # Public Node
            'https://gnosis-mainnet.public.blastapi.io',  # Blast API
            'https://gnosis.drpc.org',           # DRPC
            'https://rpc.ankr.com/gnosis'        # Ankr (last resort)
        ]
        
        # Try each endpoint until one works
        for endpoint in rpc_endpoints:
            try:
                print(f"Trying RPC endpoint: {endpoint}")
                w3 = Web3(Web3.HTTPProvider(endpoint))
                if w3.is_connected():
                    print(f"Connected to Gnosis Chain using {endpoint}")
                    rpc_url = endpoint
                    break
            except Exception as e:
                print(f"Failed to connect to {endpoint}: {e}")
                continue
    
    # If still no URL, use the first one as a fallback
    if not rpc_url:
        print("Warning: Could not find a working RPC endpoint. Using fallback.")
        rpc_url = 'https://rpc.gnosischain.com'
    
    # Create Web3 instance with verify=False to bypass SSL issues if needed
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            print(f"Warning: Connection failed with {rpc_url}. Trying with SSL verification disabled.")
            w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'verify': False}))
    except Exception as e:
        print(f"Error connecting to {rpc_url}: {e}")
        print("Trying with SSL verification disabled.")
        w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'verify': False}))
    
    # Add middleware for Gnosis Chain (PoA network)
    web3_version = pkg_resources.get_distribution("web3").version
    print(f"Using web3.py version: {web3_version}")
    
    # Rest of the middleware setup remains the same...
    
    if int(web3_version.split('.')[0]) >= 7:
        # For web3.py v7+, use ExtraDataToPOAMiddleware
        from web3.middleware import ExtraDataToPOAMiddleware
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        print("Added v7+ PoA middleware (ExtraDataToPOAMiddleware)")
    elif web3_version.startswith('6'):
        try:
            from web3.middleware.geth_poa import geth_poa_middleware
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            print("Added v6 PoA middleware")
        except ImportError:
            print("Couldn't import geth_poa_middleware for web3 v6")
            # Define custom middleware if import fails
            def custom_poa_middleware(make_request, web3):
                def middleware(method, params):
                    if method == 'eth_sendTransaction':
                        params[0].setdefault('extraData', '0x')
                    return make_request(method, params)
                return middleware
            w3.middleware_onion.inject(custom_poa_middleware, layer=0)
            print("Added custom PoA middleware as fallback")
    else:
        try:
            from web3.middleware import geth_poa_middleware
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            print("Added v5 PoA middleware")
        except ImportError:
            print("Couldn't import geth_poa_middleware - using custom middleware")
            # Define custom middleware if import fails
            def custom_poa_middleware(make_request, web3):
                def middleware(method, params):
                    if method == 'eth_sendTransaction':
                        params[0].setdefault('extraData', '0x')
                    return make_request(method, params)
                return middleware
            w3.middleware_onion.inject(custom_poa_middleware, layer=0)
            print("Added custom PoA middleware as fallback")
    
    return w3

def get_account_from_private_key():
    """
    Get account from private key in environment variables.
    
    Returns:
        tuple: (account, address) or (None, None) if no key is available
    """
    # Load environment variables
    load_dotenv()
    
    if os.getenv('PRIVATE_KEY'):
        account = Account.from_key(os.getenv('PRIVATE_KEY'))
        address = account.address
        print(f"🔑 Using account: {address}")
        return account, address
    else:
        print("⚠️ No private key found. Set the PRIVATE_KEY environment variable to enable transactions.")
        return None, None

def get_raw_transaction(signed_tx):
    """
    Get raw transaction bytes from a signed transaction, handling different web3.py versions.
    
    Args:
        signed_tx: A signed transaction
        
    Returns:
        bytes: Raw transaction bytes
    """
    if hasattr(signed_tx, 'rawTransaction'):
        return signed_tx.rawTransaction
    else:
        return signed_tx.raw_transaction
