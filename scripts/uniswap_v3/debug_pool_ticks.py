import os
import json
import argparse
from web3 import Web3
from dotenv import load_dotenv
import math

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
}

# ABIs
ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "payable": False, "stateMutability": "view", "type": "function"}
]

UNISWAP_V3_POOL_ABI = [
    {"inputs": [], "name": "token0", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "token1", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "slot0", "outputs": [{"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"}, {"internalType": "int24", "name": "tick", "type": "int24"}, {"internalType": "uint16", "name": "observationIndex", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"}, {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"}, {"internalType": "bool", "name": "unlocked", "type": "bool"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "fee", "outputs": [{"internalType": "uint24", "name": "", "type": "uint24"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "tickSpacing", "outputs": [{"internalType": "int24", "name": "", "type": "int24"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "int24", "name": "tick", "type": "int24"}], "name": "ticks", "outputs": [{"internalType": "uint128", "name": "liquidityGross", "type": "uint128"}, {"internalType": "int128", "name": "liquidityNet", "type": "int128"}, {"internalType": "uint256", "name": "feeGrowthOutside0X128", "type": "uint256"}, {"internalType": "uint256", "name": "feeGrowthOutside1X128", "type": "uint256"}, {"internalType": "int56", "name": "tickCumulativeOutside", "type": "int56"}, {"internalType": "uint160", "name": "secondsPerLiquidityOutsideX128", "type": "uint160"}, {"internalType": "uint32", "name": "secondsOutside", "type": "uint32"}, {"internalType": "bool", "name": "initialized", "type": "bool"}], "stateMutability": "view", "type": "function"}
]

SUSHISWAP_V3_NFPM_ABI = [
    {"inputs": [], "name": "factory", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}], "name": "positions", "outputs": [{"internalType": "uint96", "name": "nonce", "type": "uint96"}, {"internalType": "address", "name": "operator", "type": "address"}, {"internalType": "address", "name": "token0", "type": "address"}, {"internalType": "address", "name": "token1", "type": "address"}, {"internalType": "uint24", "name": "fee", "type": "uint24"}, {"internalType": "int24", "name": "tickLower", "type": "int24"}, {"internalType": "int24", "name": "tickUpper", "type": "int24"}, {"internalType": "uint128", "name": "liquidity", "type": "uint128"}, {"internalType": "uint256", "name": "feeGrowthInside0LastX128", "type": "uint256"}, {"internalType": "uint256", "name": "feeGrowthInside1LastX128", "type": "uint256"}, {"internalType": "uint128", "name": "tokensOwed0", "type": "uint128"}, {"internalType": "uint128", "name": "tokensOwed1", "type": "uint128"}], "stateMutability": "view", "type": "function"}
]

def get_detailed_pool_info(w3, pool_address):
    """
    Get detailed information about a SushiSwap V3 pool.
    
    Args:
        w3: Web3 instance
        pool_address: Address of the pool
        
    Returns:
        dict: Pool information
    """
    pool_contract = w3.eth.contract(
        address=w3.to_checksum_address(pool_address),
        abi=UNISWAP_V3_POOL_ABI
    )
    
    token0 = pool_contract.functions.token0().call()
    token1 = pool_contract.functions.token1().call()
    slot0 = pool_contract.functions.slot0().call()
    
    sqrt_price_x96 = slot0[0]
    tick = slot0[1]
    
    # Calculate price from sqrtPriceX96
    price = (sqrt_price_x96 ** 2) / (2 ** 192)
    
    # Get token info
    token0_contract = w3.eth.contract(
        address=w3.to_checksum_address(token0),
        abi=ERC20_ABI
    )
    
    token1_contract = w3.eth.contract(
        address=w3.to_checksum_address(token1),
        abi=ERC20_ABI
    )
    
    token0_symbol = token0_contract.functions.symbol().call()
    token1_symbol = token1_contract.functions.symbol().call()
    
    token0_decimals = token0_contract.functions.decimals().call()
    token1_decimals = token1_contract.functions.decimals().call()
    
    # Try to get fee and tick spacing
    try:
        fee = pool_contract.functions.fee().call()
    except Exception as e:
        print(f"Warning: Could not get fee: {e}")
        fee = 3000  # Default to 0.3%
    
    try:
        tick_spacing = pool_contract.functions.tickSpacing().call()
    except Exception as e:
        print(f"Warning: Could not get tickSpacing: {e}")
        # Default tick spacing based on fee
        if fee == 500:
            tick_spacing = 10
        elif fee == 3000:
            tick_spacing = 60
        elif fee == 10000:
            tick_spacing = 200
        else:
            tick_spacing = 60  # Default
    
    # Check if current tick is initialized
    current_tick_initialized = False
    try:
        tick_info = pool_contract.functions.ticks(tick).call()
        current_tick_initialized = tick_info[7]  # initialized boolean
    except Exception as e:
        print(f"Warning: Could not check if current tick is initialized: {e}")
    
    # Calculate nearest initialized ticks
    nearest_initialized_ticks = []
    try:
        # Check ticks around the current tick
        for i in range(-10, 11):
            check_tick = tick + (i * tick_spacing)
            try:
                tick_info = pool_contract.functions.ticks(check_tick).call()
                if tick_info[7]:  # initialized
                    nearest_initialized_ticks.append(check_tick)
            except:
                pass
    except Exception as e:
        print(f"Warning: Error checking nearby ticks: {e}")
    
    # Calculate price range for a few ticks around current tick
    price_ranges = []
    for i in range(-5, 6):
        tick_value = tick + (i * tick_spacing)
        price_value = 1.0001 ** tick_value
        price_ranges.append({
            'tick': tick_value,
            'price': price_value,
            'price_human': f"1 {token0_symbol} = {price_value} {token1_symbol}"
        })
    
    # Calculate valid tick range for adding liquidity
    valid_lower_tick = math.floor(tick / tick_spacing) * tick_spacing
    valid_upper_tick = math.ceil(tick / tick_spacing) * tick_spacing
    
    # If they're the same (current tick is exactly on a tick spacing boundary)
    if valid_lower_tick == valid_upper_tick:
        valid_lower_tick = valid_lower_tick - tick_spacing
    
    return {
        'pool_address': pool_address,
        'token0': {
            'address': token0,
            'symbol': token0_symbol,
            'decimals': token0_decimals
        },
        'token1': {
            'address': token1,
            'symbol': token1_symbol,
            'decimals': token1_decimals
        },
        'sqrtPriceX96': sqrt_price_x96,
        'tick': tick,
        'price': price,  # Price of token1 in terms of token0
        'price_human': f"1 {token0_symbol} = {price} {token1_symbol}",
        'fee': fee,
        'tickSpacing': tick_spacing,
        'current_tick_initialized': current_tick_initialized,
        'nearest_initialized_ticks': nearest_initialized_ticks,
        'price_ranges': price_ranges,
        'recommended_tick_range': {
            'lower': valid_lower_tick,
            'upper': valid_upper_tick + tick_spacing  # Add one more tick spacing for upper bound
        }
    }

def calculate_valid_tick_ranges(current_tick, tick_spacing, range_percentages=[5, 10, 20, 50]):
    """
    Calculate valid tick ranges for different percentage ranges around the current price.
    
    Args:
        current_tick: Current tick of the pool
        tick_spacing: Tick spacing of the pool
        range_percentages: List of percentage ranges to calculate
        
    Returns:
        dict: Valid tick ranges for each percentage
    """
    result = {}
    
    for percentage in range_percentages:
        # Calculate price range
        price_factor = 1 + (percentage / 100)
        
        # Calculate ticks (log base 1.0001 of price)
        tick_lower = math.floor(current_tick - (math.log(price_factor) / math.log(1.0001)))
        tick_upper = math.ceil(current_tick + (math.log(price_factor) / math.log(1.0001)))
        
        # Round to nearest tick spacing
        tick_lower = math.floor(tick_lower / tick_spacing) * tick_spacing
        tick_upper = math.ceil(tick_upper / tick_spacing) * tick_spacing
        
        result[percentage] = {
            'lower': tick_lower,
            'upper': tick_upper
        }
    
    return result

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Debug SushiSwap V3 pool ticks')
    parser.add_argument('--pool', type=str, help='Pool address', default=CONTRACT_ADDRESSES["poolYes"])
    args = parser.parse_args()
    
    # Connect to Gnosis Chain
    rpc_url = os.getenv("RPC_URL", "https://rpc.gnosischain.com")
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    # Check connection
    if not w3.is_connected():
        print("❌ Failed to connect to the blockchain")
        return
    
    print(f"✅ Connected to {rpc_url}")
    
    # Get pool information
    pool_address = args.pool
    pool_info = get_detailed_pool_info(w3, pool_address)
    
    # Print pool information
    print("\n=== Pool Information ===")
    print(f"Pool Address: {pool_info['pool_address']}")
    print(f"Token0: {pool_info['token0']['symbol']} ({pool_info['token0']['address']})")
    print(f"Token1: {pool_info['token1']['symbol']} ({pool_info['token1']['address']})")
    print(f"Current Price: {pool_info['price_human']}")
    print(f"Current Tick: {pool_info['tick']}")
    print(f"Fee: {pool_info['fee'] / 10000}%")
    print(f"Tick Spacing: {pool_info['tickSpacing']}")
    
    # Print tick information
    print("\n=== Tick Information ===")
    print(f"Current Tick Initialized: {pool_info['current_tick_initialized']}")
    print(f"Nearest Initialized Ticks: {pool_info['nearest_initialized_ticks']}")
    
    # Print recommended tick range
    print("\n=== Recommended Tick Range for Adding Liquidity ===")
    print(f"Lower Tick: {pool_info['recommended_tick_range']['lower']}")
    print(f"Upper Tick: {pool_info['recommended_tick_range']['upper']}")
    
    # Calculate and print valid tick ranges for different percentages
    valid_ranges = calculate_valid_tick_ranges(pool_info['tick'], pool_info['tickSpacing'])
    print("\n=== Valid Tick Ranges for Different Price Ranges ===")
    for percentage, range_info in valid_ranges.items():
        print(f"±{percentage}% Price Range: {range_info['lower']} to {range_info['upper']}")
    
    # Print price ranges for nearby ticks
    print("\n=== Price at Nearby Ticks ===")
    for price_range in pool_info['price_ranges']:
        print(f"Tick {price_range['tick']}: {price_range['price_human']}")
    
    # Print example command for adding liquidity
    token0_symbol = pool_info['token0']['symbol']
    token1_symbol = pool_info['token1']['symbol']
    
    print("\n=== Example Command for Adding Liquidity ===")
    print(f"python fix_liquidity_core.py --token0 0.01 --token1 1.0 --pool {pool_address} --range 10 --slippage 0.5")
    print(f"This will add 0.01 {token0_symbol} and 1.0 {token1_symbol} with a ±10% price range.")

if __name__ == "__main__":
    main() 