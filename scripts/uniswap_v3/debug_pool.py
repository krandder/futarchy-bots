import os
import json
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
    {"inputs": [{"internalType": "int24", "name": "tickLower", "type": "int24"}, {"internalType": "int24", "name": "tickUpper", "type": "int24"}], "name": "getPositionLiquidity", "outputs": [{"internalType": "uint128", "name": "liquidity", "type": "uint128"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "tickSpacing", "outputs": [{"internalType": "int24", "name": "", "type": "int24"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "int16", "name": "wordPosition", "type": "int16"}], "name": "tickBitmap", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "int24", "name": "tick", "type": "int24"}], "name": "ticks", "outputs": [{"internalType": "uint128", "name": "liquidityGross", "type": "uint128"}, {"internalType": "int128", "name": "liquidityNet", "type": "int128"}, {"internalType": "uint256", "name": "feeGrowthOutside0X128", "type": "uint256"}, {"internalType": "uint256", "name": "feeGrowthOutside1X128", "type": "uint256"}, {"internalType": "int56", "name": "tickCumulativeOutside", "type": "int56"}, {"internalType": "uint160", "name": "secondsPerLiquidityOutsideX128", "type": "uint160"}, {"internalType": "uint32", "name": "secondsOutside", "type": "uint32"}, {"internalType": "bool", "name": "initialized", "type": "bool"}], "stateMutability": "view", "type": "function"}
]

SUSHISWAP_V3_NFPM_ABI = [
    {"inputs": [], "name": "factory", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}], "name": "positions", "outputs": [{"internalType": "uint96", "name": "nonce", "type": "uint96"}, {"internalType": "address", "name": "operator", "type": "address"}, {"internalType": "address", "name": "token0", "type": "address"}, {"internalType": "address", "name": "token1", "type": "address"}, {"internalType": "uint24", "name": "fee", "type": "uint24"}, {"internalType": "int24", "name": "tickLower", "type": "int24"}, {"internalType": "int24", "name": "tickUpper", "type": "int24"}, {"internalType": "uint128", "name": "liquidity", "type": "uint128"}, {"internalType": "uint256", "name": "feeGrowthInside0LastX128", "type": "uint256"}, {"internalType": "uint256", "name": "feeGrowthInside1LastX128", "type": "uint256"}, {"internalType": "uint128", "name": "tokensOwed0", "type": "uint128"}, {"internalType": "uint128", "name": "tokensOwed1", "type": "uint128"}], "stateMutability": "view", "type": "function"}
]

def get_pool_info(w3, pool_address):
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
    except:
        fee = "Unknown"
    
    try:
        tick_spacing = pool_contract.functions.tickSpacing().call()
    except:
        tick_spacing = "Unknown"
    
    # Get liquidity at current tick
    try:
        current_tick_info = pool_contract.functions.ticks(tick).call()
        liquidity_at_current_tick = current_tick_info[0]  # liquidityGross
    except:
        liquidity_at_current_tick = "Unknown"
    
    return {
        'address': pool_address,
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
        'fee': fee,
        'tickSpacing': tick_spacing,
        'liquidityAtCurrentTick': liquidity_at_current_tick
    }

def get_nfpm_info(w3, nfpm_address):
    """
    Get information about the SushiSwap V3 NonFungiblePositionManager.
    
    Args:
        w3: Web3 instance
        nfpm_address: Address of the NonFungiblePositionManager
        
    Returns:
        dict: NFPM information
    """
    nfpm_contract = w3.eth.contract(
        address=w3.to_checksum_address(nfpm_address),
        abi=SUSHISWAP_V3_NFPM_ABI
    )
    
    try:
        factory = nfpm_contract.functions.factory().call()
    except:
        factory = "Unknown"
    
    return {
        'address': nfpm_address,
        'factory': factory
    }

def calculate_tick_for_price(price):
    """
    Calculate the tick for a given price.
    
    Args:
        price: The price to calculate the tick for
        
    Returns:
        int: The tick corresponding to the price
    """
    # Tick = log(price) / log(1.0001)
    return int(math.log(price) / math.log(1.0001))

def main():
    # Connect to Gnosis Chain
    rpc_url = os.getenv("RPC_URL", "https://rpc.gnosischain.com")
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    # Check connection
    if not w3.is_connected():
        print("❌ Failed to connect to the blockchain")
        return
    
    print(f"✅ Connected to {rpc_url}")
    
    # Get pool information
    pool_address = CONTRACT_ADDRESSES["poolYes"]
    pool_info = get_pool_info(w3, pool_address)
    
    print("\n=== SushiSwap YES Pool Information ===")
    print(f"Pool Address: {pool_info['address']}")
    print(f"Token0: {pool_info['token0']['symbol']} ({pool_info['token0']['address']})")
    print(f"Token1: {pool_info['token1']['symbol']} ({pool_info['token1']['address']})")
    
    # Calculate and display price in both directions
    if pool_info['token0']['address'].lower() == CONTRACT_ADDRESSES["companyYesToken"].lower():
        # GNO YES is token0, sDAI YES is token1
        gno_to_sdai_price = 1 / pool_info['price']
        print(f"Current Price: 1 {pool_info['token0']['symbol']} = {gno_to_sdai_price} {pool_info['token1']['symbol']}")
    else:
        # sDAI YES is token0, GNO YES is token1
        sdai_to_gno_price = pool_info['price']
        print(f"Current Price: 1 {pool_info['token1']['symbol']} = {sdai_to_gno_price} {pool_info['token0']['symbol']}")
    
    print(f"Current Tick: {pool_info['tick']}")
    print(f"Fee: {pool_info['fee']}")
    print(f"Tick Spacing: {pool_info['tickSpacing']}")
    print(f"Liquidity at Current Tick: {pool_info['liquidityAtCurrentTick']}")
    
    # Get NFPM information
    nfpm_address = CONTRACT_ADDRESSES["sushiswapNFPM"]
    nfpm_info = get_nfpm_info(w3, nfpm_address)
    
    print("\n=== SushiSwap V3 NonFungiblePositionManager Information ===")
    print(f"NFPM Address: {nfpm_info['address']}")
    print(f"Factory: {nfpm_info['factory']}")
    
    # Calculate ticks for different price ratios
    print("\n=== Tick Calculations for Different Price Ratios ===")
    
    # Determine which token is GNO YES
    if pool_info['token0']['address'].lower() == CONTRACT_ADDRESSES["companyYesToken"].lower():
        # GNO YES is token0, sDAI YES is token1
        # For token0/token1 price, we need the reciprocal of our ratio
        for ratio in [100, 150, 169, 200]:
            target_price = 1 / ratio
            target_tick = calculate_tick_for_price(target_price)
            print(f"Price Ratio 1 GNO YES = {ratio} sDAI YES => Tick: {target_tick}")
    else:
        # sDAI YES is token0, GNO YES is token1
        for ratio in [100, 150, 169, 200]:
            target_price = ratio
            target_tick = calculate_tick_for_price(target_price)
            print(f"Price Ratio 1 GNO YES = {ratio} sDAI YES => Tick: {target_tick}")
    
    # Calculate valid tick ranges
    if pool_info['tickSpacing'] != "Unknown":
        tick_spacing = int(pool_info['tickSpacing'])
        current_tick = pool_info['tick']
        
        print("\n=== Valid Tick Ranges Around Current Price ===")
        for range_size in [5, 10, 20]:
            tick_lower = math.floor((current_tick - (range_size * tick_spacing)) / tick_spacing) * tick_spacing
            tick_upper = math.ceil((current_tick + (range_size * tick_spacing)) / tick_spacing) * tick_spacing
            print(f"Range Size: ±{range_size} tick spacings => Tick Range: {tick_lower} to {tick_upper}")

if __name__ == "__main__":
    main() 