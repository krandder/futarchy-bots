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
    {"inputs": [], "name": "slot0", "outputs": [{"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"}, {"internalType": "int24", "name": "tick", "type": "int24"}, {"internalType": "uint16", "name": "observationIndex", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"}, {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"}, {"internalType": "bool", "name": "unlocked", "type": "bool"}], "stateMutability": "view", "type": "function"}
]

SUSHISWAP_V3_NFPM_ABI = [
    {"inputs": [{"internalType": "address", "name": "token0", "type": "address"}, {"internalType": "address", "name": "token1", "type": "address"}, {"internalType": "uint24", "name": "fee", "type": "uint24"}, {"internalType": "int24", "name": "tickLower", "type": "int24"}, {"internalType": "int24", "name": "tickUpper", "type": "int24"}, {"internalType": "uint256", "name": "amount0Desired", "type": "uint256"}, {"internalType": "uint256", "name": "amount1Desired", "type": "uint256"}, {"internalType": "uint256", "name": "amount0Min", "type": "uint256"}, {"internalType": "uint256", "name": "amount1Min", "type": "uint256"}, {"internalType": "address", "name": "recipient", "type": "address"}, {"internalType": "uint256", "name": "deadline", "type": "uint256"}], "name": "mint", "outputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}, {"internalType": "uint128", "name": "liquidity", "type": "uint128"}, {"internalType": "uint256", "name": "amount0", "type": "uint256"}, {"internalType": "uint256", "name": "amount1", "type": "uint256"}], "stateMutability": "payable", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}], "name": "positions", "outputs": [{"internalType": "uint96", "name": "nonce", "type": "uint96"}, {"internalType": "address", "name": "operator", "type": "address"}, {"internalType": "address", "name": "token0", "type": "address"}, {"internalType": "address", "name": "token1", "type": "address"}, {"internalType": "uint24", "name": "fee", "type": "uint24"}, {"internalType": "int24", "name": "tickLower", "type": "int24"}, {"internalType": "int24", "name": "tickUpper", "type": "int24"}, {"internalType": "uint128", "name": "liquidity", "type": "uint128"}, {"internalType": "uint256", "name": "feeGrowthInside0LastX128", "type": "uint256"}, {"internalType": "uint256", "name": "feeGrowthInside1LastX128", "type": "uint256"}, {"internalType": "uint128", "name": "tokensOwed0", "type": "uint128"}, {"internalType": "uint128", "name": "tokensOwed1", "type": "uint128"}], "stateMutability": "view", "type": "function"}
]

def get_pool_info(w3, pool_address):
    """
    Get information about a SushiSwap V3 pool.
    
    Args:
        w3: Web3 instance
        pool_address: Address of the pool
        
    Returns:
        dict: Pool information including token0, token1, and current price
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
    
    return {
        'token0': token0,
        'token1': token1,
        'sqrtPriceX96': sqrt_price_x96,
        'tick': tick,
        'price': price  # Price of token1 in terms of token0
    }

def calculate_tick_range(current_tick, price_range_percentage):
    """
    Calculate tick range based on current tick and desired price range percentage.
    
    Args:
        current_tick: Current tick of the pool
        price_range_percentage: Percentage range around current price (e.g., 10 for ±10%)
        
    Returns:
        tuple: (tick_lower, tick_upper)
    """
    # Calculate price range
    price_factor = 1 + (price_range_percentage / 100)
    
    # Calculate ticks (log base 1.0001 of price)
    tick_spacing = 60  # Common tick spacing for 0.3% fee tier
    
    # Calculate lower and upper ticks based on price range
    tick_lower = math.floor(current_tick - (math.log(price_factor) / math.log(1.0001)))
    tick_upper = math.ceil(current_tick + (math.log(price_factor) / math.log(1.0001)))
    
    # Round to nearest tick spacing
    tick_lower = math.floor(tick_lower / tick_spacing) * tick_spacing
    tick_upper = math.ceil(tick_upper / tick_spacing) * tick_spacing
    
    return (tick_lower, tick_upper)

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

def add_liquidity_to_yes_pool(w3, gno_yes_amount, sdai_yes_amount, price_range_percentage=10, slippage_percentage=0.5, account=None, custom_price_ratio=None):
    """
    Add liquidity to the SushiSwap YES pool.
    
    Args:
        w3: Web3 instance
        gno_yes_amount: Amount of GNO YES tokens to add (in ether units)
        sdai_yes_amount: Amount of sDAI YES tokens to add (in ether units)
        price_range_percentage: Percentage range around current price (e.g., 10 for ±10%)
        slippage_percentage: Slippage tolerance percentage
        account: Account to use for signing
        custom_price_ratio: Custom price ratio to use (e.g., 100 for 1 GNO YES = 100 sDAI YES)
        
    Returns:
        dict: Information about the created position or None if failed
    """
    if account is None:
        raise ValueError("No account configured for transactions")
    
    # Convert amounts to wei
    gno_yes_amount_wei = w3.to_wei(gno_yes_amount, 'ether')
    sdai_yes_amount_wei = w3.to_wei(sdai_yes_amount, 'ether')
    
    try:
        # Get pool information
        pool_address = CONTRACT_ADDRESSES["poolYes"]
        pool_info = get_pool_info(w3, pool_address)
        token0 = pool_info['token0']
        token1 = pool_info['token1']
        current_tick = pool_info['tick']
        
        # Calculate tick range based on price range percentage or custom price ratio
        if custom_price_ratio is not None:
            # For Uniswap V3 style pools, we need to be careful with the tick range
            # Let's use a more conservative approach and stay closer to the current market price
            
            # Determine which token is GNO YES
            if token0.lower() == CONTRACT_ADDRESSES["companyYesToken"].lower():
                # GNO YES is token0, sDAI YES is token1
                # Current price is in terms of token1/token0
                current_price_ratio = 1 / pool_info['price']
                print(f"Current price ratio: 1 GNO YES = {current_price_ratio} sDAI YES")
                
                # Use a wider range that includes both the current price and our target price
                # This ensures we're not too far from the market
                tick_spacing = 60  # Common tick spacing for 0.3% fee tier
                
                # Set the lower bound to be slightly below the current tick
                tick_lower = current_tick - (10 * tick_spacing)  # Go down by 10 tick spacings
                
                # Set the upper bound to be slightly above the current tick
                tick_upper = current_tick + (10 * tick_spacing)  # Go up by 10 tick spacings
            else:
                # sDAI YES is token0, GNO YES is token1
                # Current price is in terms of token0/token1
                current_price_ratio = pool_info['price']
                print(f"Current price ratio: 1 GNO YES = {current_price_ratio} sDAI YES")
                
                # Use a wider range that includes both the current price and our target price
                # This ensures we're not too far from the market
                tick_spacing = 60  # Common tick spacing for 0.3% fee tier
                
                # Set the lower bound to be slightly below the current tick
                tick_lower = current_tick - (10 * tick_spacing)  # Go down by 10 tick spacings
                
                # Set the upper bound to be slightly above the current tick
                tick_upper = current_tick + (10 * tick_spacing)  # Go up by 10 tick spacings
        else:
            # Use standard price range around current price
            tick_lower, tick_upper = calculate_tick_range(current_tick, price_range_percentage)
        
        print(f"📝 Adding liquidity to SushiSwap V3 YES pool")
        print(f"Pool address: {pool_address}")
        print(f"Token0: {token0}")
        print(f"Token1: {token1}")
        print(f"Amount0: {w3.from_wei(gno_yes_amount_wei, 'ether')} GNO YES")
        print(f"Amount1: {w3.from_wei(sdai_yes_amount_wei, 'ether')} sDAI YES")
        print(f"Current tick: {current_tick}")
        print(f"Tick range: {tick_lower} to {tick_upper}")
        
        # Calculate minimum amounts based on slippage
        slippage_factor = 1 - (slippage_percentage / 100)
        amount0_min = int(gno_yes_amount_wei * slippage_factor)
        amount1_min = int(sdai_yes_amount_wei * slippage_factor)
        
        # Approve tokens for the NonFungiblePositionManager
        nfpm_address = CONTRACT_ADDRESSES["sushiswapNFPM"]
        
        # Determine which token is token0 and token1
        if token0.lower() == CONTRACT_ADDRESSES["companyYesToken"].lower():
            # GNO YES is token0
            if not approve_token(w3, CONTRACT_ADDRESSES["companyYesToken"], nfpm_address, gno_yes_amount_wei, account):
                return None
            
            if not approve_token(w3, CONTRACT_ADDRESSES["currencyYesToken"], nfpm_address, sdai_yes_amount_wei, account):
                return None
                
            amount0_desired = gno_yes_amount_wei
            amount1_desired = sdai_yes_amount_wei
        else:
            # sDAI YES is token0
            if not approve_token(w3, CONTRACT_ADDRESSES["currencyYesToken"], nfpm_address, sdai_yes_amount_wei, account):
                return None
            
            if not approve_token(w3, CONTRACT_ADDRESSES["companyYesToken"], nfpm_address, gno_yes_amount_wei, account):
                return None
                
            amount0_desired = sdai_yes_amount_wei
            amount1_desired = gno_yes_amount_wei
            
            # Swap min amounts too
            amount0_min, amount1_min = amount1_min, amount0_min
        
        # Set deadline (30 minutes from now)
        deadline = int(time.time() + 1800)
        
        # Determine fee tier (0.3% is common, represented as 3000)
        fee = 3000
        
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
            amount0_desired,  # amount0Desired
            amount1_desired,  # amount1Desired
            amount0_min,  # amount0Min
            amount1_min,  # amount1Min
            account.address,  # recipient
            deadline  # deadline
        ).build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 1000000,
            'gasPrice': w3.eth.gas_price,
            'chainId': w3.eth.chain_id,
            'value': 0  # No ETH sent with transaction
        })
        
        # Try to estimate gas to catch potential issues before sending
        try:
            estimated_gas = w3.eth.estimate_gas(mint_tx)
            print(f"Estimated gas for this transaction: {estimated_gas}")
            
            # If estimated gas is more than 80% of our limit, increase limit further
            if estimated_gas > 800000:
                mint_tx['gas'] = int(estimated_gas * 1.25)  # Add 25% buffer
                print(f"Increased gas limit to: {mint_tx['gas']}")
        except Exception as gas_error:
            print(f"⚠️ Gas estimation failed: {gas_error}")
            print(f"⚠️ This may indicate the transaction will fail, but proceeding anyway...")
            
            # Increase gas limit significantly for failed estimations
            mint_tx['gas'] = 2000000
            print(f"Setting gas limit to: {mint_tx['gas']}")
        
        signed_mint_tx = w3.eth.account.sign_transaction(mint_tx, account.key)
        mint_tx_hash = w3.eth.send_raw_transaction(signed_mint_tx.raw_transaction)
        
        print(f"⏳ Mint transaction sent: {mint_tx_hash.hex()}")
        
        # Wait for confirmation
        mint_receipt = w3.eth.wait_for_transaction_receipt(mint_tx_hash)
        
        if mint_receipt['status'] == 1:
            print(f"✅ Liquidity added successfully!")
            
            # Parse the logs to get the token ID and other information
            # This is a simplified approach - in production, you'd want to decode the logs properly
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
    parser = argparse.ArgumentParser(description='Add liquidity to SushiSwap YES pool')
    parser.add_argument('--gno', type=float, help='Amount of GNO YES tokens to add', default=0.01)
    parser.add_argument('--sdai', type=float, help='Amount of sDAI YES tokens to add', default=1.0)
    parser.add_argument('--range', type=float, help='Price range percentage (e.g., 10 for ±10%%)', default=10.0)
    parser.add_argument('--slippage', type=float, help='Slippage tolerance percentage', default=0.5)
    parser.add_argument('--yes', action='store_true', help='Skip confirmation prompt')
    parser.add_argument('--price-ratio', type=float, help='Custom price ratio (e.g., 100 for 1 GNO YES = 100 sDAI YES)')
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
    
    # Check balances
    gno_yes_contract = w3.eth.contract(
        address=w3.to_checksum_address(CONTRACT_ADDRESSES["companyYesToken"]),
        abi=ERC20_ABI
    )
    
    sdai_yes_contract = w3.eth.contract(
        address=w3.to_checksum_address(CONTRACT_ADDRESSES["currencyYesToken"]),
        abi=ERC20_ABI
    )
    
    gno_yes_balance = gno_yes_contract.functions.balanceOf(address).call()
    sdai_yes_balance = sdai_yes_contract.functions.balanceOf(address).call()
    
    gno_yes_balance_eth = w3.from_wei(gno_yes_balance, 'ether')
    sdai_yes_balance_eth = w3.from_wei(sdai_yes_balance, 'ether')
    
    print(f"\n=== Available Balances ===")
    print(f"GNO YES: {gno_yes_balance_eth}")
    print(f"sDAI YES: {sdai_yes_balance_eth}")
    
    # Get pool information to determine the optimal ratio
    pool_address = CONTRACT_ADDRESSES["poolYes"]
    pool_info = get_pool_info(w3, pool_address)
    
    # Determine which token is token0 and token1
    token0 = pool_info['token0']
    token1 = pool_info['token1']
    
    if token0.lower() == CONTRACT_ADDRESSES["companyYesToken"].lower():
        # GNO YES is token0, sDAI YES is token1
        current_price = pool_info['price']  # Price of sDAI YES in terms of GNO YES
        print(f"\nCurrent pool price: 1 GNO YES = {1/current_price} sDAI YES")
    else:
        # sDAI YES is token0, GNO YES is token1
        current_price = pool_info['price']  # Price of GNO YES in terms of sDAI YES
        print(f"\nCurrent pool price: 1 GNO YES = {current_price} sDAI YES")
    
    # Use command line arguments
    gno_yes_amount = args.gno
    sdai_yes_amount = args.sdai
    price_range = args.range
    slippage = args.slippage
    custom_price_ratio = args.price_ratio
    
    # Calculate the actual price ratio we're using
    actual_ratio = sdai_yes_amount / gno_yes_amount
    print(f"Your liquidity ratio: 1 GNO YES = {actual_ratio} sDAI YES")
    
    # Check if amounts are valid
    if gno_yes_amount <= 0 or sdai_yes_amount <= 0:
        print("❌ Amounts must be greater than 0")
        return
    
    if gno_yes_amount > gno_yes_balance_eth:
        print(f"❌ Not enough GNO YES tokens. Available: {gno_yes_balance_eth}")
        return
    
    if sdai_yes_amount > sdai_yes_balance_eth:
        print(f"❌ Not enough sDAI YES tokens. Available: {sdai_yes_balance_eth}")
        return
    
    # Confirm with user
    print(f"\n=== Transaction Summary ===")
    print(f"Adding liquidity to SushiSwap YES pool:")
    print(f"  - {gno_yes_amount} GNO YES")
    print(f"  - {sdai_yes_amount} sDAI YES")
    if custom_price_ratio:
        print(f"Custom price ratio: 1 GNO YES = {custom_price_ratio} sDAI YES")
    else:
        print(f"Price range: ±{price_range}%")
    print(f"Slippage tolerance: {slippage}%")
    
    if not args.yes:
        confirm = input("\nConfirm transaction? (y/n): ").lower() == 'y'
        if not confirm:
            print("Transaction cancelled")
            return
    
    # Add liquidity
    result = add_liquidity_to_yes_pool(
        w3=w3,
        gno_yes_amount=gno_yes_amount,
        sdai_yes_amount=sdai_yes_amount,
        price_range_percentage=price_range,
        slippage_percentage=slippage,
        account=account,
        custom_price_ratio=custom_price_ratio
    )
    
    if result:
        print("\n=== Transaction Successful ===")
        if 'tokenId' in result:
            print(f"Position NFT ID: {result['tokenId']}")
        if 'liquidity' in result:
            print(f"Liquidity: {result['liquidity']}")
        print("✅ Successfully added liquidity to SushiSwap YES pool!")
    else:
        print("\n=== Transaction Failed ===")
        print("❌ Failed to add liquidity to SushiSwap YES pool")

if __name__ == "__main__":
    main() 