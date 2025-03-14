import os
import json
import argparse
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
CONTRACT_ADDRESSES = {
    "baseCurrencyToken": "0xaf204776c7245bF4147c2612BF6e5972Ee483701",  # SDAI
    "baseCompanyToken": "0x9C58BAcC331c9aa871AFD802DB6379a98e80CEdb",  # GNO
    "currencyYesToken": "0x493A0D1c776f8797297Aa8B34594fBd0A7F8968a",  # sDAI YES
    "currencyNoToken": "0xE1133Ef862f3441880adADC2096AB67c63f6E102",
    "companyYesToken": "0x177304d505eCA60E1aE0dAF1bba4A4c4181dB8Ad",  # GNO YES
    "companyNoToken": "0xf1B3E5Ffc0219A4F8C0ac69EC98C97709EdfB6c9",
    "wagno": "0x7c16f0185a26db0ae7a9377f23bc18ea7ce5d644",
    "poolYes": "0x9a14d28909f42823ee29847f87a15fb3b6e8aed3",
    "sushiswapNFPM": "0xaB235da7f52d35fb4551AfBa11BFB56e18774A65",  # SushiSwap V3 NonFungiblePositionManager
    "sushiswapFactory": "0xf78031CBCA409F2FB6876BDFDBc1b2df24cF9bEf",  # SushiSwap V3 Factory
}

# ABIs
FACTORY_ABI = [
    {"inputs": [{"internalType": "address", "name": "tokenA", "type": "address"}, {"internalType": "address", "name": "tokenB", "type": "address"}, {"internalType": "uint24", "name": "fee", "type": "uint24"}], "name": "getPool", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"}
]

POOL_ABI = [
    {"inputs": [], "name": "token0", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "token1", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "slot0", "outputs": [{"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"}, {"internalType": "int24", "name": "tick", "type": "int24"}, {"internalType": "uint16", "name": "observationIndex", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"}, {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"}, {"internalType": "bool", "name": "unlocked", "type": "bool"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "fee", "outputs": [{"internalType": "uint24", "name": "", "type": "uint24"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "liquidity", "outputs": [{"internalType": "uint128", "name": "", "type": "uint128"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "tickSpacing", "outputs": [{"internalType": "int24", "name": "", "type": "int24"}], "stateMutability": "view", "type": "function"}
]

ERC20_ABI = [
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "payable": False, "stateMutability": "view", "type": "function"}
]

def check_pool_initialization(w3, factory_address, token0_address, token1_address, fee):
    """
    Check if a pool exists and is initialized.
    
    Args:
        w3: Web3 instance
        factory_address: Address of the factory
        token0_address: Address of token0
        token1_address: Address of token1
        fee: Fee tier
        
    Returns:
        dict: Pool information
    """
    # Ensure addresses are checksum addresses
    factory_address = w3.to_checksum_address(factory_address)
    token0_address = w3.to_checksum_address(token0_address)
    token1_address = w3.to_checksum_address(token1_address)
    
    # Initialize factory contract
    factory_contract = w3.eth.contract(
        address=factory_address,
        abi=FACTORY_ABI
    )
    
    # Get token symbols
    token0_contract = w3.eth.contract(
        address=token0_address,
        abi=ERC20_ABI
    )
    
    token1_contract = w3.eth.contract(
        address=token1_address,
        abi=ERC20_ABI
    )
    
    token0_symbol = token0_contract.functions.symbol().call()
    token1_symbol = token1_contract.functions.symbol().call()
    
    # Check if pool exists
    try:
        pool_address = factory_contract.functions.getPool(
            token0_address,
            token1_address,
            fee
        ).call()
        
        if pool_address == '0x0000000000000000000000000000000000000000':
            return {
                'exists': False,
                'token0': {
                    'address': token0_address,
                    'symbol': token0_symbol
                },
                'token1': {
                    'address': token1_address,
                    'symbol': token1_symbol
                },
                'fee': fee
            }
        
        # Pool exists, check if it's initialized
        pool_contract = w3.eth.contract(
            address=pool_address,
            abi=POOL_ABI
        )
        
        # Get pool information
        slot0 = pool_contract.functions.slot0().call()
        liquidity = pool_contract.functions.liquidity().call()
        
        # Check if pool is initialized (has liquidity and a valid price)
        is_initialized = liquidity > 0 and slot0[0] > 0
        
        return {
            'exists': True,
            'address': pool_address,
            'token0': {
                'address': token0_address,
                'symbol': token0_symbol
            },
            'token1': {
                'address': token1_address,
                'symbol': token1_symbol
            },
            'fee': fee,
            'is_initialized': is_initialized,
            'liquidity': liquidity,
            'sqrtPriceX96': slot0[0],
            'tick': slot0[1]
        }
    except Exception as e:
        print(f"Error checking pool: {e}")
        return {
            'exists': False,
            'error': str(e),
            'token0': {
                'address': token0_address,
                'symbol': token0_symbol
            },
            'token1': {
                'address': token1_address,
                'symbol': token1_symbol
            },
            'fee': fee
        }

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Check if a pool exists and is initialized')
    parser.add_argument('--token0', type=str, help='Address of token0', default=CONTRACT_ADDRESSES["companyYesToken"])
    parser.add_argument('--token1', type=str, help='Address of token1', default=CONTRACT_ADDRESSES["currencyYesToken"])
    parser.add_argument('--fee', type=int, help='Fee tier (e.g., 500, 3000, 10000)', default=100)
    parser.add_argument('--factory', type=str, help='Address of the factory', default=CONTRACT_ADDRESSES["sushiswapFactory"])
    parser.add_argument('--pool', type=str, help='Address of the pool (optional)', default=None)
    args = parser.parse_args()
    
    # Connect to Gnosis Chain
    rpc_url = os.getenv("RPC_URL", "https://rpc.gnosischain.com")
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    # Check connection
    if not w3.is_connected():
        print("❌ Failed to connect to the blockchain")
        return
    
    print(f"✅ Connected to {rpc_url}")
    
    # If pool address is provided, check that pool directly
    if args.pool:
        pool_address = w3.to_checksum_address(args.pool)
        pool_contract = w3.eth.contract(
            address=pool_address,
            abi=POOL_ABI
        )
        
        # Get pool information
        token0 = pool_contract.functions.token0().call()
        token1 = pool_contract.functions.token1().call()
        fee = pool_contract.functions.fee().call()
        slot0 = pool_contract.functions.slot0().call()
        liquidity = pool_contract.functions.liquidity().call()
        tick_spacing = pool_contract.functions.tickSpacing().call()
        
        # Get token symbols
        token0_contract = w3.eth.contract(
            address=token0,
            abi=ERC20_ABI
        )
        
        token1_contract = w3.eth.contract(
            address=token1,
            abi=ERC20_ABI
        )
        
        token0_symbol = token0_contract.functions.symbol().call()
        token1_symbol = token1_contract.functions.symbol().call()
        
        # Check if pool is initialized (has liquidity and a valid price)
        is_initialized = liquidity > 0 and slot0[0] > 0
        
        print("\n=== Pool Information ===")
        print(f"Pool Address: {pool_address}")
        print(f"Token0: {token0_symbol} ({token0})")
        print(f"Token1: {token1_symbol} ({token1})")
        print(f"Fee: {fee / 10000}%")
        print(f"Tick Spacing: {tick_spacing}")
        print(f"Current Tick: {slot0[1]}")
        print(f"Liquidity: {liquidity}")
        print(f"Initialized: {is_initialized}")
        
        # Check if the pool exists in the factory
        factory_contract = w3.eth.contract(
            address=w3.to_checksum_address(args.factory),
            abi=FACTORY_ABI
        )
        
        try:
            factory_pool_address = factory_contract.functions.getPool(
                token0,
                token1,
                fee
            ).call()
            
            print(f"\nPool in Factory: {factory_pool_address}")
            print(f"Matches Provided Pool: {factory_pool_address.lower() == pool_address.lower()}")
        except Exception as e:
            print(f"\nError checking pool in factory: {e}")
    else:
        # Check if pool exists and is initialized
        pool_info = check_pool_initialization(
            w3,
            args.factory,
            args.token0,
            args.token1,
            args.fee
        )
        
        if pool_info['exists']:
            print("\n=== Pool Information ===")
            print(f"Pool Address: {pool_info['address']}")
            print(f"Token0: {pool_info['token0']['symbol']} ({pool_info['token0']['address']})")
            print(f"Token1: {pool_info['token1']['symbol']} ({pool_info['token1']['address']})")
            print(f"Fee: {pool_info['fee'] / 10000}%")
            print(f"Initialized: {pool_info['is_initialized']}")
            print(f"Liquidity: {pool_info['liquidity']}")
            print(f"Current Tick: {pool_info['tick']}")
        else:
            print("\n=== Pool Information ===")
            print(f"Pool does not exist for:")
            print(f"Token0: {pool_info['token0']['symbol']} ({pool_info['token0']['address']})")
            print(f"Token1: {pool_info['token1']['symbol']} ({pool_info['token1']['address']})")
            print(f"Fee: {pool_info['fee'] / 10000}%")
            
            if 'error' in pool_info:
                print(f"Error: {pool_info['error']}")

if __name__ == "__main__":
    main() 