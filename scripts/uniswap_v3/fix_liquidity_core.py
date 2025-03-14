import os
import json
import time
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
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": False, "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "payable": False, "stateMutability": "nonpayable", "type": "function"},
    {"constant": True, "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "payable": False, "stateMutability": "view", "type": "function"}
]

UNISWAP_V3_POOL_ABI = [
    {"inputs": [], "name": "token0", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "token1", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "slot0", "outputs": [{"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"}, {"internalType": "int24", "name": "tick", "type": "int24"}, {"internalType": "uint16", "name": "observationIndex", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"}, {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"}, {"internalType": "bool", "name": "unlocked", "type": "bool"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "fee", "outputs": [{"internalType": "uint24", "name": "", "type": "uint24"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "tickSpacing", "outputs": [{"internalType": "int24", "name": "", "type": "int24"}], "stateMutability": "view", "type": "function"}
]

SUSHISWAP_V3_NFPM_ABI = [
    {"inputs": [{"internalType": "address", "name": "token0", "type": "address"}, {"internalType": "address", "name": "token1", "type": "address"}, {"internalType": "uint24", "name": "fee", "type": "uint24"}, {"internalType": "int24", "name": "tickLower", "type": "int24"}, {"internalType": "int24", "name": "tickUpper", "type": "int24"}, {"internalType": "uint256", "name": "amount0Desired", "type": "uint256"}, {"internalType": "uint256", "name": "amount1Desired", "type": "uint256"}, {"internalType": "uint256", "name": "amount0Min", "type": "uint256"}, {"internalType": "uint256", "name": "amount1Min", "type": "uint256"}, {"internalType": "address", "name": "recipient", "type": "address"}, {"internalType": "uint256", "name": "deadline", "type": "uint256"}], "name": "mint", "outputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}, {"internalType": "uint128", "name": "liquidity", "type": "uint128"}, {"internalType": "uint256", "name": "amount0", "type": "uint256"}, {"internalType": "uint256", "name": "amount1", "type": "uint256"}], "stateMutability": "payable", "type": "function"},
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
    
    # Get fee and tick spacing
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
    
    # Check for initialized ticks
    initialized_ticks = []
    try:
        # Check a wide range of ticks around the current tick
        for i in range(-100, 101, tick_spacing):
            check_tick = tick + i
            try:
                tick_info = pool_contract.functions.ticks(check_tick).call()
                if tick_info[7]:  # initialized
                    initialized_ticks.append(check_tick)
            except:
                pass
    except Exception as e:
        print(f"Warning: Error checking nearby ticks: {e}")
    
    # If no initialized ticks found, use MIN_TICK and MAX_TICK
    if not initialized_ticks:
        print("No initialized ticks found. Using MIN_TICK and MAX_TICK.")
        # These are the minimum and maximum tick values for Uniswap V3
        MIN_TICK = -887272
        MAX_TICK = 887272
        
        # Adjust to be multiples of tick spacing
        MIN_TICK = math.ceil(MIN_TICK / tick_spacing) * tick_spacing
        MAX_TICK = math.floor(MAX_TICK / tick_spacing) * tick_spacing
        
        initialized_ticks = [MIN_TICK, MAX_TICK]
    
    return {
        'token0': token0,
        'token1': token1,
        'sqrtPriceX96': sqrt_price_x96,
        'tick': tick,
        'price': price,  # Price of token1 in terms of token0
        'fee': fee,
        'tickSpacing': tick_spacing,
        'initialized_ticks': initialized_ticks
    }

def calculate_tick_range(current_tick, price_range_percentage, tick_spacing, initialized_ticks=None):
    """
    Calculate tick range based on current tick and desired price range percentage.
    If initialized_ticks is provided, will use the nearest initialized ticks.
    
    Args:
        current_tick: Current tick of the pool
        price_range_percentage: Percentage range around current price (e.g., 10 for ±10%)
        tick_spacing: The tick spacing of the pool
        initialized_ticks: List of initialized ticks
        
    Returns:
        tuple: (tick_lower, tick_upper)
    """
    # Calculate price range
    price_factor = 1 + (price_range_percentage / 100)
    
    # Calculate ticks (log base 1.0001 of price)
    tick_lower_raw = current_tick - (math.log(price_factor) / math.log(1.0001))
    tick_upper_raw = current_tick + (math.log(price_factor) / math.log(1.0001))
    
    # Round to nearest tick spacing
    tick_lower = math.floor(tick_lower_raw / tick_spacing) * tick_spacing
    tick_upper = math.ceil(tick_upper_raw / tick_spacing) * tick_spacing
    
    # If initialized ticks are provided, use them
    if initialized_ticks:
        # Find nearest initialized tick below tick_lower
        lower_candidates = [t for t in initialized_ticks if t <= tick_lower]
        if lower_candidates:
            tick_lower = max(lower_candidates)
        
        # Find nearest initialized tick above tick_upper
        upper_candidates = [t for t in initialized_ticks if t >= tick_upper]
        if upper_candidates:
            tick_upper = min(upper_candidates)
    
    return (tick_lower, tick_upper)

def approve_token(w3, token_address, spender_address, amount, account):
    """
    Approve tokens for spending.
    
    Args:
        w3: Web3 instance
        token_address: Address of the token to approve
        spender_address: Address of the spender
        amount: Amount to approve
        account: Account to use for signing
        
    Returns:
        bool: Success or failure
    """
    token_contract = w3.eth.contract(
        address=w3.to_checksum_address(token_address),
        abi=ERC20_ABI
    )
    
    # Check current allowance
    current_allowance = token_contract.functions.allowance(
        account.address,
        spender_address
    ).call()
    
    if current_allowance >= amount:
        print(f"✅ Allowance already sufficient: {w3.from_wei(current_allowance, 'ether')}")
        return True
    
    try:
        # First set allowance to 0 (to handle some tokens that require this)
        if current_allowance > 0:
            print(f"Setting allowance to 0 first...")
            reset_tx = token_contract.functions.approve(
                spender_address,
                0
            ).build_transaction({
                'from': account.address,
                'nonce': w3.eth.get_transaction_count(account.address),
                'gas': 100000,
                'gasPrice': w3.eth.gas_price,
                'chainId': w3.eth.chain_id,
            })
            
            signed_tx = w3.eth.account.sign_transaction(reset_tx, account.key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt['status'] != 1:
                print(f"❌ Failed to reset allowance")
                return False
        
        # Build transaction for approval
        approve_tx = token_contract.functions.approve(
            spender_address,
            amount
        ).build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
            'chainId': w3.eth.chain_id,
        })
        
        # Sign and send transaction
        signed_tx = w3.eth.account.sign_transaction(approve_tx, account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print(f"⏳ Approval transaction sent: {tx_hash.hex()}")
        
        # Wait for confirmation
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt['status'] == 1:
            print(f"✅ Approval successful!")
            return True
        else:
            print(f"❌ Approval failed with receipt: {receipt}")
            return False
    
    except Exception as e:
        print(f"❌ Error approving token: {e}")
        return False

def add_liquidity_to_pool(w3, pool_address, token0_amount, token1_amount, price_range_percentage=10, slippage_percentage=0.5, account=None):
    """
    Add liquidity to a SushiSwap V3 pool with proper tick alignment.
    
    Args:
        w3: Web3 instance
        pool_address: Address of the pool
        token0_amount: Amount of token0 to add (in ether units)
        token1_amount: Amount of token1 to add (in ether units)
        price_range_percentage: Percentage range around current price (e.g., 10 for ±10%)
        slippage_percentage: Slippage tolerance percentage
        account: Account to use for signing
        
    Returns:
        dict: Information about the created position or None if failed
    """
    if account is None:
        raise ValueError("No account configured for transactions")
    
    try:
        # Get pool information
        pool_info = get_pool_info(w3, pool_address)
        token0 = pool_info['token0']
        token1 = pool_info['token1']
        current_tick = pool_info['tick']
        tick_spacing = pool_info['tickSpacing']
        fee = pool_info['fee']
        initialized_ticks = pool_info.get('initialized_ticks', [])
        
        print(f"Pool Information:")
        print(f"  Token0: {token0}")
        print(f"  Token1: {token1}")
        print(f"  Current Tick: {current_tick}")
        print(f"  Tick Spacing: {tick_spacing}")
        print(f"  Fee: {fee}")
        print(f"  Initialized Ticks: {initialized_ticks[:10]}...")
        
        # Get token information
        token0_contract = w3.eth.contract(address=w3.to_checksum_address(token0), abi=ERC20_ABI)
        token1_contract = w3.eth.contract(address=w3.to_checksum_address(token1), abi=ERC20_ABI)
        
        token0_decimals = token0_contract.functions.decimals().call()
        token1_decimals = token1_contract.functions.decimals().call()
        
        token0_symbol = token0_contract.functions.symbol().call()
        token1_symbol = token1_contract.functions.symbol().call()
        
        print(f"  Token0 Symbol: {token0_symbol}, Decimals: {token0_decimals}")
        print(f"  Token1 Symbol: {token1_symbol}, Decimals: {token1_decimals}")
        
        # Convert amounts to wei based on token decimals
        token0_amount_wei = int(token0_amount * (10 ** token0_decimals))
        token1_amount_wei = int(token1_amount * (10 ** token1_decimals))
        
        # Calculate tick range based on price range percentage and initialized ticks
        tick_lower, tick_upper = calculate_tick_range(
            current_tick, 
            price_range_percentage, 
            tick_spacing,
            initialized_ticks
        )
        
        # Ensure tick_lower < tick_upper
        if tick_lower >= tick_upper:
            print(f"Warning: tick_lower ({tick_lower}) >= tick_upper ({tick_upper})")
            # Use a wider range
            tick_lower = min(initialized_ticks) if initialized_ticks else -887272
            tick_upper = max(initialized_ticks) if initialized_ticks else 887272
            print(f"Using wider range: {tick_lower} to {tick_upper}")
        
        print(f"\nAdding Liquidity:")
        print(f"  Amount0: {token0_amount} {token0_symbol} ({token0_amount_wei} wei)")
        print(f"  Amount1: {token1_amount} {token1_symbol} ({token1_amount_wei} wei)")
        print(f"  Tick Range: {tick_lower} to {tick_upper}")
        print(f"  Current Tick: {current_tick}")
        
        # Calculate minimum amounts based on slippage
        slippage_factor = 1 - (slippage_percentage / 100)
        amount0_min = int(token0_amount_wei * slippage_factor)
        amount1_min = int(token1_amount_wei * slippage_factor)
        
        # Approve tokens for the NonFungiblePositionManager
        nfpm_address = CONTRACT_ADDRESSES["sushiswapNFPM"]
        
        if not approve_token(w3, token0, nfpm_address, token0_amount_wei, account):
            return None
        
        if not approve_token(w3, token1, nfpm_address, token1_amount_wei, account):
            return None
        
        # Set deadline (30 minutes from now)
        deadline = int(time.time() + 1800)
        
        # Initialize NonFungiblePositionManager contract
        nfpm_contract = w3.eth.contract(
            address=w3.to_checksum_address(nfpm_address),
            abi=SUSHISWAP_V3_NFPM_ABI
        )
        
        # Build transaction for minting a new position
        mint_tx = nfpm_contract.functions.mint(
            token0,  # token0
            token1,  # token1
            fee,  # fee
            tick_lower,  # tickLower
            tick_upper,  # tickUpper
            token0_amount_wei,  # amount0Desired
            token1_amount_wei,  # amount1Desired
            amount0_min,  # amount0Min
            amount1_min,  # amount1Min
            account.address,  # recipient
            deadline  # deadline
        ).build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 2000000,  # Higher gas limit
            'gasPrice': w3.eth.gas_price,
            'chainId': w3.eth.chain_id,
            'value': 0  # No ETH sent with transaction
        })
        
        # Try to estimate gas to catch potential issues before sending
        try:
            estimated_gas = w3.eth.estimate_gas(mint_tx)
            print(f"Estimated gas for this transaction: {estimated_gas}")
            
            # If estimated gas is more than 80% of our limit, increase limit further
            if estimated_gas > 1600000:
                mint_tx['gas'] = int(estimated_gas * 1.25)  # Add 25% buffer
                print(f"Increased gas limit to: {mint_tx['gas']}")
        except Exception as gas_error:
            print(f"⚠️ Gas estimation failed: {gas_error}")
            print(f"⚠️ This may indicate the transaction will fail, but proceeding anyway...")
            
            # Increase gas limit significantly for failed estimations
            mint_tx['gas'] = 3000000
            print(f"Setting gas limit to: {mint_tx['gas']}")
        
        # Print the transaction details for debugging
        print("\nTransaction Details:")
        print(f"  From: {mint_tx['from']}")
        print(f"  To: {nfpm_address}")
        print(f"  Gas: {mint_tx['gas']}")
        print(f"  Gas Price: {mint_tx['gasPrice']}")
        print(f"  Nonce: {mint_tx['nonce']}")
        print(f"  Chain ID: {mint_tx['chainId']}")
        print(f"  Value: {mint_tx['value']}")
        print(f"  Function: mint")
        print(f"  Parameters:")
        print(f"    token0: {token0}")
        print(f"    token1: {token1}")
        print(f"    fee: {fee}")
        print(f"    tickLower: {tick_lower}")
        print(f"    tickUpper: {tick_upper}")
        print(f"    amount0Desired: {token0_amount_wei}")
        print(f"    amount1Desired: {token1_amount_wei}")
        print(f"    amount0Min: {amount0_min}")
        print(f"    amount1Min: {amount1_min}")
        print(f"    recipient: {account.address}")
        print(f"    deadline: {deadline}")
        
        signed_mint_tx = w3.eth.account.sign_transaction(mint_tx, account.key)
        mint_tx_hash = w3.eth.send_raw_transaction(signed_mint_tx.raw_transaction)
        
        print(f"\n⏳ Mint transaction sent: {mint_tx_hash.hex()}")
        
        # Wait for confirmation
        mint_receipt = w3.eth.wait_for_transaction_receipt(mint_tx_hash)
        
        if mint_receipt['status'] == 1:
            print(f"✅ Liquidity added successfully!")
            
            # Parse the logs to get the token ID and other information
            token_id = None
            try:
                # Try to get the token ID from the receipt logs
                for log in mint_receipt['logs']:
                    if log['address'].lower() == nfpm_address.lower():
                        # This is likely the Transfer event for the NFT
                        token_id = int(log['topics'][3].hex(), 16)
                        break
            except Exception as log_error:
                print(f"⚠️ Error parsing logs: {log_error}")
            
            if token_id:
                print(f"Position NFT ID: {token_id}")
                
                # Get position details
                try:
                    position = nfpm_contract.functions.positions(token_id).call()
                    
                    return {
                        'tokenId': token_id,
                        'token0': position[2],
                        'token1': position[3],
                        'fee': position[4],
                        'tickLower': position[5],
                        'tickUpper': position[6],
                        'liquidity': position[7]
                    }
                except Exception as pos_error:
                    print(f"⚠️ Error getting position details: {pos_error}")
                    return {'tokenId': token_id}
            else:
                print("⚠️ Could not find token ID in transaction logs")
                return {'success': True}
        else:
            print(f"❌ Adding liquidity failed with receipt: {mint_receipt}")
            return None
    
    except Exception as e:
        print(f"❌ Error adding liquidity: {e}")
        return None

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Add liquidity to SushiSwap V3 pool')
    parser.add_argument('--token0', type=float, help='Amount of token0 to add', default=0.01)
    parser.add_argument('--token1', type=float, help='Amount of token1 to add', default=1.0)
    parser.add_argument('--pool', type=str, help='Pool address', default=CONTRACT_ADDRESSES["poolYes"])
    parser.add_argument('--range', type=float, help='Price range percentage (e.g., 10 for ±10%%)', default=10.0)
    parser.add_argument('--slippage', type=float, help='Slippage tolerance percentage', default=0.5)
    parser.add_argument('--yes', action='store_true', help='Skip confirmation prompt')
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
    pool_info = get_pool_info(w3, pool_address)
    
    # Get token information
    token0 = pool_info['token0']
    token1 = pool_info['token1']
    
    token0_contract = w3.eth.contract(address=w3.to_checksum_address(token0), abi=ERC20_ABI)
    token1_contract = w3.eth.contract(address=w3.to_checksum_address(token1), abi=ERC20_ABI)
    
    token0_symbol = token0_contract.functions.symbol().call()
    token1_symbol = token1_contract.functions.symbol().call()
    
    token0_decimals = token0_contract.functions.decimals().call()
    token1_decimals = token1_contract.functions.decimals().call()
    
    # Check balances
    token0_balance = token0_contract.functions.balanceOf(address).call()
    token1_balance = token1_contract.functions.balanceOf(address).call()
    
    token0_balance_human = token0_balance / (10 ** token0_decimals)
    token1_balance_human = token1_balance / (10 ** token1_decimals)
    
    print(f"\n=== Available Balances ===")
    print(f"{token0_symbol}: {token0_balance_human}")
    print(f"{token1_symbol}: {token1_balance_human}")
    
    # Use command line arguments
    token0_amount = args.token0
    token1_amount = args.token1
    price_range = args.range
    slippage = args.slippage
    
    # Check if amounts are valid
    if token0_amount <= 0 or token1_amount <= 0:
        print("❌ Amounts must be greater than 0")
        return
    
    if token0_amount > token0_balance_human:
        print(f"❌ Not enough {token0_symbol} tokens. Available: {token0_balance_human}")
        return
    
    if token1_amount > token1_balance_human:
        print(f"❌ Not enough {token1_symbol} tokens. Available: {token1_balance_human}")
        return
    
    # Confirm with user
    print(f"\n=== Transaction Summary ===")
    print(f"Adding liquidity to pool {pool_address}:")
    print(f"  - {token0_amount} {token0_symbol}")
    print(f"  - {token1_amount} {token1_symbol}")
    print(f"Price range: ±{price_range}%")
    print(f"Slippage tolerance: {slippage}%")
    
    if not args.yes:
        confirm = input("\nConfirm transaction? (y/n): ").lower() == 'y'
        if not confirm:
            print("Transaction cancelled")
            return
    
    # Add liquidity
    result = add_liquidity_to_pool(
        w3=w3,
        pool_address=pool_address,
        token0_amount=token0_amount,
        token1_amount=token1_amount,
        price_range_percentage=price_range,
        slippage_percentage=slippage,
        account=account
    )
    
    if result:
        print("\n=== Transaction Successful ===")
        if 'tokenId' in result:
            print(f"Position NFT ID: {result['tokenId']}")
        if 'liquidity' in result:
            print(f"Liquidity: {result['liquidity']}")
        print("✅ Successfully added liquidity to pool!")
    else:
        print("\n=== Transaction Failed ===")
        print("❌ Failed to add liquidity to pool")

if __name__ == "__main__":
    main() 