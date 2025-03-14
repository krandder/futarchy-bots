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
}

# ABIs
SUSHISWAP_V3_NFPM_ABI = [
    {"inputs": [{"internalType": "address", "name": "token0", "type": "address"}, {"internalType": "address", "name": "token1", "type": "address"}, {"internalType": "uint24", "name": "fee", "type": "uint24"}, {"internalType": "int24", "name": "tickLower", "type": "int24"}, {"internalType": "int24", "name": "tickUpper", "type": "int24"}, {"internalType": "uint256", "name": "amount0Desired", "type": "uint256"}, {"internalType": "uint256", "name": "amount1Desired", "type": "uint256"}, {"internalType": "uint256", "name": "amount0Min", "type": "uint256"}, {"internalType": "uint256", "name": "amount1Min", "type": "uint256"}, {"internalType": "address", "name": "recipient", "type": "address"}, {"internalType": "uint256", "name": "deadline", "type": "uint256"}], "name": "mint", "outputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}, {"internalType": "uint128", "name": "liquidity", "type": "uint128"}, {"internalType": "uint256", "name": "amount0", "type": "uint256"}, {"internalType": "uint256", "name": "amount1", "type": "uint256"}], "stateMutability": "payable", "type": "function"},
]

UNISWAP_V3_POOL_ABI = [
    {"inputs": [], "name": "token0", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "token1", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "slot0", "outputs": [{"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"}, {"internalType": "int24", "name": "tick", "type": "int24"}, {"internalType": "uint16", "name": "observationIndex", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"}, {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"}, {"internalType": "bool", "name": "unlocked", "type": "bool"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "fee", "outputs": [{"internalType": "uint24", "name": "", "type": "uint24"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "tickSpacing", "outputs": [{"internalType": "int24", "name": "", "type": "int24"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "int24", "name": "tick", "type": "int24"}], "name": "ticks", "outputs": [{"internalType": "uint128", "name": "liquidityGross", "type": "uint128"}, {"internalType": "int128", "name": "liquidityNet", "type": "int128"}, {"internalType": "uint256", "name": "feeGrowthOutside0X128", "type": "uint256"}, {"internalType": "uint256", "name": "feeGrowthOutside1X128", "type": "uint256"}, {"internalType": "int56", "name": "tickCumulativeOutside", "type": "int56"}, {"internalType": "uint160", "name": "secondsPerLiquidityOutsideX128", "type": "uint160"}, {"internalType": "uint32", "name": "secondsOutside", "type": "uint32"}, {"internalType": "bool", "name": "initialized", "type": "bool"}], "stateMutability": "view", "type": "function"}
]

def debug_mint_transaction(w3, pool_address, token0, token1, fee, tick_lower, tick_upper, amount0_desired, amount1_desired, amount0_min, amount1_min, recipient, deadline, sender):
    """
    Debug a mint transaction by simulating it with eth_call.
    
    Args:
        w3: Web3 instance
        pool_address: Address of the pool
        token0: Address of token0
        token1: Address of token1
        fee: Fee tier
        tick_lower: Lower tick
        tick_upper: Upper tick
        amount0_desired: Amount of token0 desired
        amount1_desired: Amount of token1 desired
        amount0_min: Minimum amount of token0
        amount1_min: Minimum amount of token1
        recipient: Address of the recipient
        deadline: Transaction deadline
        sender: Address of the sender
        
    Returns:
        str: Error message or success
    """
    nfpm_address = CONTRACT_ADDRESSES["sushiswapNFPM"]
    nfpm_contract = w3.eth.contract(
        address=w3.to_checksum_address(nfpm_address),
        abi=SUSHISWAP_V3_NFPM_ABI
    )
    
    # Check if ticks are initialized
    pool_contract = w3.eth.contract(
        address=w3.to_checksum_address(pool_address),
        abi=UNISWAP_V3_POOL_ABI
    )
    
    # Check if the ticks are initialized
    try:
        tick_lower_info = pool_contract.functions.ticks(tick_lower).call()
        tick_upper_info = pool_contract.functions.ticks(tick_upper).call()
        
        print(f"Tick Lower ({tick_lower}) Initialized: {tick_lower_info[7]}")
        print(f"Tick Upper ({tick_upper}) Initialized: {tick_upper_info[7]}")
    except Exception as e:
        print(f"Error checking ticks: {e}")
    
    # Build the transaction data
    mint_data = nfpm_contract.encodeABI(
        fn_name="mint",
        args=[
            token0,
            token1,
            fee,
            tick_lower,
            tick_upper,
            amount0_desired,
            amount1_desired,
            amount0_min,
            amount1_min,
            recipient,
            deadline
        ]
    )
    
    # Try to simulate the transaction with eth_call
    try:
        # First try with a normal eth_call
        result = w3.eth.call({
            'from': sender,
            'to': nfpm_address,
            'data': mint_data,
            'value': 0
        })
        
        print(f"Transaction would succeed!")
        return "Success"
    except Exception as e:
        error_message = str(e)
        print(f"Transaction would fail: {error_message}")
        
        # Try to extract more detailed error information
        try:
            # Some providers return error data in a specific format
            if "revert" in error_message.lower():
                # Try to extract the revert reason
                if "execution reverted:" in error_message:
                    revert_reason = error_message.split("execution reverted:")[1].strip()
                    return f"Revert reason: {revert_reason}"
                else:
                    # Try to use debug_traceCall if available
                    try:
                        trace_result = w3.provider.make_request(
                            "debug_traceCall",
                            [{
                                'from': sender,
                                'to': nfpm_address,
                                'data': mint_data,
                                'value': 0
                            }, "latest", {"tracer": "callTracer"}]
                        )
                        
                        return f"Trace result: {json.dumps(trace_result, indent=2)}"
                    except Exception as trace_error:
                        return f"Could not get detailed trace: {trace_error}"
        except Exception as extract_error:
            return f"Error extracting detailed error information: {extract_error}"
        
        return f"Error: {error_message}"

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Debug a mint transaction')
    parser.add_argument('--pool', type=str, help='Pool address', default=CONTRACT_ADDRESSES["poolYes"])
    parser.add_argument('--token0', type=float, help='Amount of token0 to add', default=0.01)
    parser.add_argument('--token1', type=float, help='Amount of token1 to add', default=1.7)
    parser.add_argument('--range', type=float, help='Price range percentage (e.g., 10 for ±10%%)', default=15.0)
    args = parser.parse_args()
    
    # Connect to Gnosis Chain
    rpc_url = os.getenv("RPC_URL", "https://rpc.gnosischain.com")
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    # Check connection
    if not w3.is_connected():
        print("❌ Failed to connect to the blockchain")
        return
    
    print(f"✅ Connected to {rpc_url}")
    
    # Get account from private key
    private_key = os.getenv("PRIVATE_KEY")
    if not private_key:
        print("❌ No private key found in .env file")
        return
    
    account = w3.eth.account.from_key(private_key)
    address = account.address
    print(f"📝 Using account: {address}")
    
    # Get pool information
    pool_address = args.pool
    pool_contract = w3.eth.contract(
        address=w3.to_checksum_address(pool_address),
        abi=UNISWAP_V3_POOL_ABI
    )
    
    token0 = pool_contract.functions.token0().call()
    token1 = pool_contract.functions.token1().call()
    slot0 = pool_contract.functions.slot0().call()
    fee = pool_contract.functions.fee().call()
    tick_spacing = pool_contract.functions.tickSpacing().call()
    
    current_tick = slot0[1]
    
    print(f"Pool Information:")
    print(f"  Token0: {token0}")
    print(f"  Token1: {token1}")
    print(f"  Current Tick: {current_tick}")
    print(f"  Tick Spacing: {tick_spacing}")
    print(f"  Fee: {fee}")
    
    # Calculate tick range
    import math
    price_range_percentage = args.range
    price_factor = 1 + (price_range_percentage / 100)
    
    tick_lower_raw = current_tick - (math.log(price_factor) / math.log(1.0001))
    tick_upper_raw = current_tick + (math.log(price_factor) / math.log(1.0001))
    
    tick_lower = math.floor(tick_lower_raw / tick_spacing) * tick_spacing
    tick_upper = math.ceil(tick_upper_raw / tick_spacing) * tick_spacing
    
    print(f"Calculated Tick Range: {tick_lower} to {tick_upper}")
    
    # Check if the ticks are initialized
    try:
        for tick in [tick_lower, tick_upper]:
            try:
                tick_info = pool_contract.functions.ticks(tick).call()
                print(f"Tick {tick} is initialized: {tick_info[7]}")
            except Exception as e:
                print(f"Error checking tick {tick}: {e}")
                print(f"This tick may not be initialized")
    except Exception as e:
        print(f"Error checking ticks: {e}")
    
    # Try different tick ranges
    print("\nTrying different tick ranges to find initialized ticks...")
    
    # Check a range of ticks around the current tick
    initialized_ticks = []
    for i in range(-100, 101, tick_spacing):
        try:
            tick = current_tick + i
            tick_info = pool_contract.functions.ticks(tick).call()
            if tick_info[7]:  # initialized
                initialized_ticks.append(tick)
                print(f"Tick {tick} is initialized")
        except Exception:
            pass
    
    if initialized_ticks:
        print(f"\nFound {len(initialized_ticks)} initialized ticks")
        
        # Find nearest initialized ticks for lower and upper bounds
        lower_ticks = [t for t in initialized_ticks if t <= current_tick]
        upper_ticks = [t for t in initialized_ticks if t > current_tick]
        
        if lower_ticks:
            nearest_lower = max(lower_ticks)
            print(f"Nearest initialized tick below current: {nearest_lower}")
        else:
            nearest_lower = None
            print("No initialized ticks below current tick")
        
        if upper_ticks:
            nearest_upper = min(upper_ticks)
            print(f"Nearest initialized tick above current: {nearest_upper}")
        else:
            nearest_upper = None
            print("No initialized ticks above current tick")
        
        if nearest_lower is not None and nearest_upper is not None:
            print(f"\nRecommended tick range: {nearest_lower} to {nearest_upper}")
            tick_lower = nearest_lower
            tick_upper = nearest_upper
    else:
        print("No initialized ticks found")
    
    # Set up transaction parameters
    token0_amount = args.token0
    token1_amount = args.token1
    
    # Get token decimals
    from web3.contract import Contract
    ERC20_ABI = [{"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "payable": False, "stateMutability": "view", "type": "function"}]
    
    token0_contract = w3.eth.contract(address=w3.to_checksum_address(token0), abi=ERC20_ABI)
    token1_contract = w3.eth.contract(address=w3.to_checksum_address(token1), abi=ERC20_ABI)
    
    token0_decimals = token0_contract.functions.decimals().call()
    token1_decimals = token1_contract.functions.decimals().call()
    
    # Convert amounts to wei
    token0_amount_wei = int(token0_amount * (10 ** token0_decimals))
    token1_amount_wei = int(token1_amount * (10 ** token1_decimals))
    
    # Set minimum amounts (0.5% slippage)
    slippage_factor = 0.995
    amount0_min = int(token0_amount_wei * slippage_factor)
    amount1_min = int(token1_amount_wei * slippage_factor)
    
    # Set deadline (30 minutes from now)
    import time
    deadline = int(time.time() + 1800)
    
    print(f"\nDebug Parameters:")
    print(f"  Token0 Amount: {token0_amount} ({token0_amount_wei} wei)")
    print(f"  Token1 Amount: {token1_amount} ({token1_amount_wei} wei)")
    print(f"  Tick Range: {tick_lower} to {tick_upper}")
    
    # Debug the mint transaction
    result = debug_mint_transaction(
        w3=w3,
        pool_address=pool_address,
        token0=token0,
        token1=token1,
        fee=fee,
        tick_lower=tick_lower,
        tick_upper=tick_upper,
        amount0_desired=token0_amount_wei,
        amount1_desired=token1_amount_wei,
        amount0_min=amount0_min,
        amount1_min=amount1_min,
        recipient=address,
        deadline=deadline,
        sender=address
    )
    
    print(f"\nDebug Result: {result}")

if __name__ == "__main__":
    main() 