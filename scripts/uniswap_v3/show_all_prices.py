#!/usr/bin/env python3
"""
Script to show current prices from all three pools (YES, NO, and Balancer)
in terms of sDAI per GNO.
"""

import os
import sys
import json
import requests
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
from price_impact.config.constants import BALANCER_CONFIG, TOKEN_CONFIG
from config.constants import CONTRACT_ADDRESSES

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Load environment variables
load_dotenv()

# Constants
UNISWAP_V3_BRIDGE_URL = "http://localhost:3001"
RPC_URL = os.getenv("RPC_URL", "https://rpc.ankr.com/gnosis")
COWSWAP_API_URL = "https://api.cow.fi/xdai"  # Gnosis Chain (Production)

# Pool and token addresses (checksum format)
w3_temp = Web3()
POOL_YES = w3_temp.to_checksum_address("0x9a14d28909f42823ee29847f87a15fb3b6e8aed3")
POOL_NO = w3_temp.to_checksum_address("0x6E33153115Ab58dab0e0F1E3a2ccda6e67FA5cD7")
BALANCER_POOL = w3_temp.to_checksum_address(BALANCER_CONFIG["pool_address"])

# Token addresses for CoW Swap
SDAI_ADDRESS = TOKEN_CONFIG["currency"]["address"]  # sDAI on Gnosis Chain
GNO_ADDRESS = TOKEN_CONFIG["company"]["address"]    # GNO on Gnosis Chain

def setup_web3():
    """Initialize Web3"""
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        raise Exception("Failed to connect to Gnosis Chain")
    return w3

def calculate_price_from_sqrt_price_x96(sqrt_price_x96, token0_decimals, token1_decimals):
    """Calculate price from sqrtPriceX96"""
    # Convert sqrtPriceX96 to a decimal
    sqrt_price = int(sqrt_price_x96) / (1 << 96)
    price = sqrt_price * sqrt_price
    
    # Adjust for decimals
    decimal_adjustment = 10 ** (token1_decimals - token0_decimals)
    price = price * decimal_adjustment
    
    return price

def get_uniswap_v3_pool_price(pool_address):
    """Get price from a Uniswap V3 pool in terms of sDAI per GNO"""
    response = requests.get(f"{UNISWAP_V3_BRIDGE_URL}/api/pool/{pool_address}")
    if response.status_code != 200:
        raise Exception(f"Failed to get pool info: {response.text}")
    
    pool_info = response.json()
    sqrt_price_x96 = int(pool_info["sqrtPriceX96"])
    price = calculate_price_from_sqrt_price_x96(
        sqrt_price_x96,
        pool_info["token0"]["decimals"],
        pool_info["token1"]["decimals"]
    )
    
    # Price is in terms of token1/token0
    # We want sDAI/GNO, so:
    # - If sDAI is token0 and GNO is token1: need to invert
    # - If GNO is token0 and sDAI is token1: price is already correct
    # - If sDAI is token1 and GNO is token0: need to invert
    # - If GNO is token1 and sDAI is token0: price is already correct
    token0_symbol = pool_info["token0"]["symbol"]
    token1_symbol = pool_info["token1"]["symbol"]
    
    if ("sDAI" in token0_symbol and "GNO" in token1_symbol) or \
       ("GNO" in token1_symbol and "sDAI" in token0_symbol):
        # Need to invert to get sDAI/GNO
        price = 1 / price
    
    return price, token0_symbol, token1_symbol

def get_wagno_to_gno_rate(w3):
    """Get the conversion rate from waGNO to GNO using the ERC4626 interface"""
    # Load ERC4626 ABI
    abi = json.loads('[{"inputs":[{"internalType":"uint256","name":"shares","type":"uint256"}],"name":"convertToAssets","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]')
    
    # Get waGNO contract with checksum address
    wagno_contract = w3.eth.contract(
        address=w3.to_checksum_address(TOKEN_CONFIG["wagno"]["address"]), 
        abi=abi
    )
    
    try:
        # Query conversion rate for 1 waGNO
        one_wagno = 10 ** 18  # 1 token with 18 decimals
        gno_amount = wagno_contract.functions.convertToAssets(one_wagno).call()
        return gno_amount / one_wagno
    except Exception as e:
        print(f"Error getting waGNO to GNO rate: {e}")
        return 1.0  # Fallback to 1:1 ratio

def get_balancer_pool_price(w3, pool_address):
    """Get price from Balancer pool"""
    # Load Balancer pool ABI (for weighted pool)
    router_abi = json.loads('[{"inputs":[{"components":[{"internalType":"address","name":"tokenIn","type":"address"},{"components":[{"internalType":"address","name":"pool","type":"address"},{"internalType":"address","name":"tokenOut","type":"address"},{"internalType":"bool","name":"isBuffer","type":"bool"}],"internalType":"struct IRouter.Step[]","name":"steps","type":"tuple[]"},{"internalType":"uint256","name":"exactAmountIn","type":"uint256"},{"internalType":"uint256","name":"minAmountOut","type":"uint256"}],"internalType":"struct IRouter.SwapExactIn[]","name":"swaps","type":"tuple[]"},{"internalType":"address","name":"sender","type":"address"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"querySwapExactIn","outputs":[{"internalType":"uint256[]","name":"amountsOut","type":"uint256[]"}],"stateMutability":"view","type":"function"}]')
    
    try:
        # Get batch router contract
        router_contract = w3.eth.contract(
            address=w3.to_checksum_address(CONTRACT_ADDRESSES["batchRouter"]), 
            abi=router_abi
        )
        
        # Query a small amount to get price
        one_sdai_wei = w3.to_wei(1, 'ether')
        
        # Define swap parameters
        swap_params = [{
            "tokenIn": w3.to_checksum_address(TOKEN_CONFIG["currency"]["address"]),  # sDAI
            "steps": [{
                "pool": w3.to_checksum_address(pool_address),
                "tokenOut": w3.to_checksum_address(TOKEN_CONFIG["wagno"]["address"]),  # waGNO
                "isBuffer": False
            }],
            "exactAmountIn": one_sdai_wei,
            "minAmountOut": 0
        }]
        
        # Query the swap
        amounts_out = router_contract.functions.querySwapExactIn(
            swap_params,
            w3.to_checksum_address("0x0000000000000000000000000000000000000000"),
            "0x"
        ).call()
        
        # Calculate price (sDAI per waGNO)
        amount_out = float(w3.from_wei(amounts_out[0], 'ether'))
        price_sdai_to_wagno = 1 / amount_out if amount_out != 0 else float('inf')
        
        # Get waGNO to GNO conversion rate
        wagno_to_gno_rate = get_wagno_to_gno_rate(w3)
        gno_price = price_sdai_to_wagno * wagno_to_gno_rate
        
        # Print intermediate values
        print("\nBalancer Pool Price Calculation:")
        print(f"1. For 1 sDAI input, get {amount_out:.6f} waGNO")
        print(f"2. Therefore, 1 waGNO = {price_sdai_to_wagno:.6f} sDAI")
        print(f"3. waGNO to GNO rate: 1 waGNO = {wagno_to_gno_rate:.6f} GNO")
        print(f"4. Final price: {price_sdai_to_wagno:.6f} sDAI/waGNO * {wagno_to_gno_rate:.6f} waGNO/GNO = {gno_price:.6f} sDAI/GNO")
        
        return gno_price
    except Exception as e:
        print(f"Error getting Balancer pool price: {e}")
        
        # Let's try to get more information about the pool
        try:
            # Load ERC20 ABI to get token info
            erc20_abi = json.loads('[{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"}]')
            
            # Get token contracts with checksum addresses
            sdai_contract = w3.eth.contract(
                address=w3.to_checksum_address(TOKEN_CONFIG["currency"]["address"]), 
                abi=erc20_abi
            )
            wagno_contract = w3.eth.contract(
                address=w3.to_checksum_address(TOKEN_CONFIG["wagno"]["address"]), 
                abi=erc20_abi
            )
            
            # Get token symbols and decimals
            sdai_symbol = sdai_contract.functions.symbol().call()
            wagno_symbol = wagno_contract.functions.symbol().call()
            sdai_decimals = sdai_contract.functions.decimals().call()
            wagno_decimals = wagno_contract.functions.decimals().call()
            
            print(f"\nPool info:")
            print(f"Pool address: {pool_address}")
            print(f"Token0: {sdai_symbol} ({TOKEN_CONFIG['currency']['address']}) - {sdai_decimals} decimals")
            print(f"Token1: {wagno_symbol} ({TOKEN_CONFIG['wagno']['address']}) - {wagno_decimals} decimals")
            print(f"Batch router: {CONTRACT_ADDRESSES['batchRouter']}")
            
            # Try to get pool type
            try:
                pool_type_abi = json.loads('[{"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"}]')
                pool_type_contract = w3.eth.contract(
                    address=w3.to_checksum_address(pool_address),
                    abi=pool_type_abi
                )
                pool_type = pool_type_contract.functions.name().call()
                print(f"Pool type: {pool_type}")
            except Exception as e3:
                print(f"Error getting pool type: {e3}")
        except Exception as e2:
            print(f"Error getting pool info: {e2}")
        
        return None

def show_all_prices():
    """Show prices from all three pools"""
    w3 = setup_web3()
    
    print("\nCurrent Prices (in sDAI per GNO):")
    print("-" * 50)
    print("Note: All prices are in terms of sDAI per GNO")
    print()
    
    try:
        # Get YES pool price
        yes_price, yes_token0, yes_token1 = get_uniswap_v3_pool_price(POOL_YES)
        print(f"YES Pool:     {yes_price:>12.6f} sDAI-YES/GNO-YES")
    except Exception as e:
        print(f"Error getting YES pool price: {e}")
    
    try:
        # Get NO pool price
        no_price, no_token0, no_token1 = get_uniswap_v3_pool_price(POOL_NO)
        print(f"NO Pool:      {no_price:>12.6f} sDAI-NO/GNO-NO")
    except Exception as e:
        print(f"Error getting NO pool price: {e}")
    
    try:
        # Get Balancer spot price
        spot_price = get_balancer_pool_price(w3, BALANCER_POOL)
        if spot_price:
            print(f"Balancer:     {spot_price:>12.6f} sDAI/GNO")
    except Exception as e:
        print(f"Error getting Balancer pool price: {e}")

if __name__ == "__main__":
    try:
        show_all_prices()
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1) 