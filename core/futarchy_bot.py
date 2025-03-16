import time
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web3 import Web3
from config.constants import (
    CONTRACT_ADDRESSES, TOKEN_CONFIG, POOL_CONFIG_YES, POOL_CONFIG_NO,
    UNISWAP_V3_POOL_ABI, SUSHISWAP_V3_ROUTER_ABI, FUTARCHY_ROUTER_ABI,
    SDAI_RATE_PROVIDER_ABI, WXDAI_ABI, SDAI_DEPOSIT_ABI, MIN_SQRT_RATIO, MAX_SQRT_RATIO,
    COWSWAP_API_URL
)
from utils.web3_utils import get_raw_transaction
from exchanges.cowswap import CowSwapExchange
from core.base_bot import BaseBot
from exchanges.aave_balancer import AaveBalancerHandler
from exchanges.sushiswap import SushiSwapExchange

class FutarchyBot(BaseBot):
    """Main Futarchy Trading Bot implementation"""
    
    # In futarchy_bot.py, add to the __init__ method:
    def __init__(self, rpc_url=None, verbose=False):
        """Initialize the Futarchy Bot"""
        self.verbose = verbose
        
        # Use default RPC URL if none provided
        if not rpc_url:
            rpc_url = os.environ.get('RPC_URL', 'https://gnosis-mainnet.public.blastapi.io')
        
        super().__init__(rpc_url)
        
        # Initialize contract instances
        self.initialize_contracts()
        
        # Initialize exchange handlers
        self.cowswap = CowSwapExchange(self)
        
        # Initialize Aave/Balancer handler
        self.aave_balancer = AaveBalancerHandler(self)
        
        # Store current strategy
        self.current_strategy = None
    
    def initialize_contracts(self):
        """Initialize all contract instances"""
        # ERC20 token contracts
        self.sdai_token = self.get_token_contract(TOKEN_CONFIG["currency"]["address"])
        self.gno_token = self.get_token_contract(TOKEN_CONFIG["company"]["address"])
        self.sdai_yes_token = self.get_token_contract(TOKEN_CONFIG["currency"]["yes_address"])
        self.sdai_no_token = self.get_token_contract(TOKEN_CONFIG["currency"]["no_address"])
        self.gno_yes_token = self.get_token_contract(TOKEN_CONFIG["company"]["yes_address"])
        self.gno_no_token = self.get_token_contract(TOKEN_CONFIG["company"]["no_address"])
        self.wagno_token = self.get_token_contract(TOKEN_CONFIG["wagno"]["address"])
        
        # Pool contracts
        self.yes_pool = self.w3.eth.contract(
            address=self.w3.to_checksum_address(POOL_CONFIG_YES["address"]),
            abi=UNISWAP_V3_POOL_ABI
        )
        self.no_pool = self.w3.eth.contract(
            address=self.w3.to_checksum_address(POOL_CONFIG_NO["address"]),
            abi=UNISWAP_V3_POOL_ABI
        )
        
        # Futarchy router contract
        self.futarchy_router = self.w3.eth.contract(
            address=self.w3.to_checksum_address(CONTRACT_ADDRESSES["futarchyRouter"]),
            abi=FUTARCHY_ROUTER_ABI
        )
        
        # SushiSwap V3 router contract
        self.sushiswap_router = self.w3.eth.contract(
            address=self.w3.to_checksum_address(CONTRACT_ADDRESSES["sushiswap"]),
            abi=SUSHISWAP_V3_ROUTER_ABI
        )
        
        # SDAI rate provider contract
        self.sdai_rate_provider = self.w3.eth.contract(
            address=self.w3.to_checksum_address(CONTRACT_ADDRESSES["sdaiRateProvider"]),
            abi=SDAI_RATE_PROVIDER_ABI
        )
    
    def get_balances(self, address=None):
        """
        Get all token balances for an address.
        
        Args:
            address: Address to check (defaults to self.address)
            
        Returns:
            dict: Token balances
        """
        if address is None:
            if self.address is None:
                raise ValueError("No address provided")
            address = self.address
        
        address = self.w3.to_checksum_address(address)
        
        # Get token balances
        sdai_balance = self.sdai_token.functions.balanceOf(address).call()
        gno_balance = self.gno_token.functions.balanceOf(address).call()
        sdai_yes_balance = self.sdai_yes_token.functions.balanceOf(address).call()
        sdai_no_balance = self.sdai_no_token.functions.balanceOf(address).call()
        gno_yes_balance = self.gno_yes_token.functions.balanceOf(address).call()
        gno_no_balance = self.gno_no_token.functions.balanceOf(address).call()
        wagno_balance = self.wagno_token.functions.balanceOf(address).call()
        
        # Format balances
        balances = {
            "currency": {
                "wallet": self.w3.from_wei(sdai_balance, 'ether'),
                "yes": self.w3.from_wei(sdai_yes_balance, 'ether'),
                "no": self.w3.from_wei(sdai_no_balance, 'ether'),
            },
            "company": {
                "wallet": self.w3.from_wei(gno_balance, 'ether'),
                "yes": self.w3.from_wei(gno_yes_balance, 'ether'),
                "no": self.w3.from_wei(gno_no_balance, 'ether'),
            },
            "wagno": {
                "wallet": self.w3.from_wei(wagno_balance, 'ether')
            }
        }
        
        return balances
    
    def print_balances(self, balances=None):
        """
        Print balances in a formatted way.
        
        Args:
            balances: Balance dict (will fetch if None)
        """
        if balances is None:
            balances = self.get_balances()
        
        print("\n=== Token Balances ===")
        
        print(f"\n🟢 {TOKEN_CONFIG['currency']['name']} (Currency):")
        print(f"  Wallet: {balances['currency']['wallet']:.6f}")
        print(f"  YES Tokens: {balances['currency']['yes']:.6f}")
        print(f"  NO Tokens: {balances['currency']['no']:.6f}")
        
        print(f"\n🔵 {TOKEN_CONFIG['company']['name']} (Company):")
        print(f"  Wallet: {balances['company']['wallet']:.6f}")
        print(f"  YES Tokens: {balances['company']['yes']:.6f}")
        print(f"  NO Tokens: {balances['company']['no']:.6f}")
        
        print(f"\n🟣 {TOKEN_CONFIG['wagno']['name']} (Wrapped GNO):")
        print(f"  Wallet: {balances['wagno']['wallet']:.6f}")
    
    def get_yes_token_price_ratio(self):
        """
        Calculate the YES token price ratio (probability).
        
        Returns:
            float: Price ratio between 0 and 1
        """
        try:
            # Use the YES pool to determine the price ratio
            yes_slot0 = self.yes_pool.functions.slot0().call()
            yes_sqrt_price = int(yes_slot0[0])
            
            # Calculate the raw price from sqrtPriceX96
            yes_raw_price = (yes_sqrt_price ** 2) / (2 ** 192)
            
            # In the YES pool, depending on the token order, this might need to be inverted
            price_ratio = 1 / yes_raw_price if POOL_CONFIG_YES["tokenCompanySlot"] == 1 else yes_raw_price
            
            # For a prediction market, the price should be between 0 and 1
            # If it's outside this range, normalize it
            normalized_ratio = max(0, min(1, price_ratio))
                
            return normalized_ratio
        
        except Exception as e:
            print(f"❌ Error calculating YES token price ratio: {e}")
            return 0.5  # Default to 50% if calculation fails
    
    def get_market_prices(self):
        """
        Get market prices and probabilities.
        
        Returns:
            dict: Market price information
        """
        try:
            # Get slot0 data from pools
            yes_slot0 = self.yes_pool.functions.slot0().call()
            no_slot0 = self.no_pool.functions.slot0().call()
            
            # Calculate prices from sqrtPriceX96
            yes_sqrt_price = int(yes_slot0[0])
            no_sqrt_price = int(no_slot0[0])
            
            yes_raw_price = (yes_sqrt_price ** 2) / (2 ** 192)
            no_raw_price = (no_sqrt_price ** 2) / (2 ** 192)
            
            # Adjust based on token slot
            yes_company_price = 1 / yes_raw_price if POOL_CONFIG_YES["tokenCompanySlot"] == 1 else yes_raw_price
            no_company_price = 1 / no_raw_price if POOL_CONFIG_NO["tokenCompanySlot"] == 1 else no_raw_price
            
            # Try to get GNO/SDAI price from CowSwap
            gno_spot_price = self.get_gno_sdai_price()
            
            # Get YES token price ratio as probability directly
            try:
                event_probability = self.get_yes_token_price_ratio()
            except Exception as prob_err:
                print(f"❌ Error calculating event probability: {prob_err}")
                event_probability = 0.5  # Default to 50% as fallback
            
            return {
                "yes_company_price": yes_company_price,
                "no_company_price": no_company_price,
                "gno_spot_price": gno_spot_price,  # GNO price in SDAI
                "event_probability": event_probability
            }
        except Exception as e:
            print(f"❌ Error getting market prices: {e}")
            return None
    
    def get_gno_sdai_price(self):
        """
        Get the GNO/sDAI price from CoW Swap.
        
        Returns:
            float: GNO price in SDAI, or a default value if estimation fails
        """
        try:
            # Try getting price from CoW Swap API directly
            print("Requesting GNO/sDAI price from CoW Swap...")
            import requests  # Import here to avoid global import issues
            
            sell_token = TOKEN_CONFIG["currency"]["address"]  # sDAI
            buy_token = TOKEN_CONFIG["company"]["address"]    # GNO
            sell_amount = "1000000000000000000"  # 1 sDAI
            
            quote_url = f"{COWSWAP_API_URL}/api/v1/quote"
            quote_data = {
                "sellToken": sell_token,
                "buyToken": buy_token,
                "sellAmountBeforeFee": sell_amount,
                "from": self.address,
                "kind": "sell"
            }
            
            response = requests.post(quote_url, json=quote_data)
            if response.status_code == 200:
                quote_result = response.json()
                if "quote" in quote_result:
                    quote = quote_result["quote"]
                    if "sellAmount" in quote and "buyAmount" in quote:
                        sell_amount = int(quote["sellAmount"])
                        buy_amount = int(quote["buyAmount"])
                        if sell_amount > 0 and buy_amount > 0:
                            # Calculate price: sDAI per GNO
                            sdai_per_gno = sell_amount / buy_amount
                            print(f"GNO price from CoW Swap: {sdai_per_gno} sDAI per GNO")
                            return sdai_per_gno
            
            # If we reach here, API fetch failed, use fallback
            print("⚠️ Using fallback price estimation from YES pool")
            yes_slot0 = self.yes_pool.functions.slot0().call()
            yes_sqrt_price = int(yes_slot0[0])
            yes_raw_price = (yes_sqrt_price ** 2) / (2 ** 192)
            yes_company_price = 1 / yes_raw_price if POOL_CONFIG_YES["tokenCompanySlot"] == 1 else yes_raw_price
            
            return yes_company_price
                
        except Exception as e:
            print(f"❌ Error getting GNO/sDAI price: {e}")
            import traceback
            traceback.print_exc()
            
            # Return a default value instead of None to avoid formatting errors
            return 100.0  # Default fallback value
    
    def print_market_prices(self, prices=None):
        """
        Print market prices and probabilities.
        
        Args:
            prices: Price dict (will fetch if None)
        """
        if prices is None:
            prices = self.get_market_prices()
            if prices is None:
                print("❌ Failed to get market prices")
                return
        
        print("\n=== Market Prices & Probability ===")
        print(f"YES GNO Price: {prices['yes_company_price']:.6f}")
        print(f"NO GNO Price: {prices['no_company_price']:.6f}")
        print(f"GNO Spot Price (SDAI): {prices['gno_spot_price']:.6f}")
        print(f"Event Probability: {prices['event_probability']:.2%}")
    
    def add_collateral(self, token_type, amount):
        """
        Add collateral by splitting positions.
        
        Args:
            token_type: Token type ('currency' or 'company')
            amount: Amount to add
            
        Returns:
            bool: Success or failure
        """
        if self.account is None:
            raise ValueError("No account configured for transactions")
        
        # Get token address based on type
        if token_type == "currency":
            token_address = TOKEN_CONFIG["currency"]["address"]
            token_name = TOKEN_CONFIG["currency"]["name"]
            token_contract = self.sdai_token
            yes_token_address = TOKEN_CONFIG["currency"]["yes_address"]
            no_token_address = TOKEN_CONFIG["currency"]["no_address"]
        elif token_type == "company":
            token_address = TOKEN_CONFIG["company"]["address"]
            token_name = TOKEN_CONFIG["company"]["name"]
            token_contract = self.gno_token
            yes_token_address = TOKEN_CONFIG["company"]["yes_address"]
            no_token_address = TOKEN_CONFIG["company"]["no_address"]
        else:
            raise ValueError(f"Invalid token type: {token_type}")
        
        if self.verbose:
            print("\nContract Addresses:")
            print(f"Base Token ({token_name}): {token_address}")
            print(f"{token_name} YES: {yes_token_address}")
            print(f"{token_name} NO: {no_token_address}")
            print(f"Futarchy Router: {CONTRACT_ADDRESSES['futarchyRouter']}")
            print(f"Market: {CONTRACT_ADDRESSES['market']}\n")
        
        # Convert amount to wei
        amount_wei = self.w3.to_wei(amount, 'ether')
        
        # Check balance with more detailed output
        has_balance, actual_balance = self.check_token_balance(token_address, amount_wei)
        print(f"\nCurrent Balances:")
        print(f"{token_name}: {self.w3.from_wei(actual_balance, 'ether')} ({actual_balance} wei)")
        print(f"Amount to split: {amount} {token_name} ({amount_wei} wei)\n")
        
        if not has_balance:
            print(f"❌ Insufficient {token_name} balance")
            print(f"   Required: {self.w3.from_wei(amount_wei, 'ether')} {token_name}")
            print(f"   Available: {self.w3.from_wei(actual_balance, 'ether')} {token_name}")
            return False
        
        # Check and display allowance
        allowance = token_contract.functions.allowance(
            self.address,
            CONTRACT_ADDRESSES["futarchyRouter"]
        ).call()
        print(f"{token_name} allowance for Router: {self.w3.from_wei(allowance, 'ether')} {token_name}")
        
        # Approve router to spend tokens
        if allowance < amount_wei:
            print(f"Approving {token_name} for Router...")
            if not self.approve_token(token_contract, CONTRACT_ADDRESSES["futarchyRouter"], amount_wei):
                return False
        else:
            print(f"✅ {token_name} already approved for Router")
        
        print(f"\n📝 Splitting {amount} {token_name} into YES/NO tokens...")
        
        try:
            # Build transaction
            tx = self.futarchy_router.functions.splitPosition(
                self.w3.to_checksum_address(CONTRACT_ADDRESSES["market"]),
                self.w3.to_checksum_address(token_address),
                amount_wei
            ).build_transaction({
                'from': self.address,
                'nonce': self.w3.eth.get_transaction_count(self.address),
                'gas': 500000,  # Higher gas limit for complex operation
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.w3.eth.chain_id,
            })
            
            # Sign and send transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(get_raw_transaction(signed_tx))
            
            print(f"\n⏳ Split transaction sent: {tx_hash.hex()}")
            print(f"Transaction: https://gnosisscan.io/tx/{tx_hash.hex()}")
            
            # Wait for transaction confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt['status'] == 1:
                # Check new balances
                yes_token = self.get_token_contract(yes_token_address)
                no_token = self.get_token_contract(no_token_address)
                
                yes_balance = yes_token.functions.balanceOf(self.address).call()
                no_balance = no_token.functions.balanceOf(self.address).call()
                
                print(f"\n✅ Successfully split {token_name} into conditional tokens!")
                print(f"New balances:")
                print(f"{token_name} YES: {self.w3.from_wei(yes_balance, 'ether')}")
                print(f"{token_name} NO: {self.w3.from_wei(no_balance, 'ether')}")
                return True
            else:
                print(f"❌ Split transaction failed!")
                print(f"Check transaction details at: https://blockscout.com/xdai/mainnet/tx/{tx_hash.hex()}")
                return False
                
        except Exception as e:
            print(f"❌ Error splitting {token_name} into conditional tokens: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def remove_collateral(self, token_type, amount):
        """
        Remove collateral by merging positions.
        
        Args:
            token_type: Token type ('currency' or 'company')
            amount: Amount to remove
            
        Returns:
            bool: Success or failure
        """
        if self.account is None:
            raise ValueError("No account configured for transactions")
        
        # Get token addresses based on type
        if token_type == "currency":
            base_token_address = TOKEN_CONFIG["currency"]["address"]
            yes_token_address = TOKEN_CONFIG["currency"]["yes_address"]
            no_token_address = TOKEN_CONFIG["currency"]["no_address"]
            token_name = TOKEN_CONFIG["currency"]["name"]
        elif token_type == "company":
            base_token_address = TOKEN_CONFIG["company"]["address"]
            yes_token_address = TOKEN_CONFIG["company"]["yes_address"]
            no_token_address = TOKEN_CONFIG["company"]["no_address"]
            token_name = TOKEN_CONFIG["company"]["name"]
        else:
            raise ValueError(f"Invalid token type: {token_type}")
        
        # Convert amount to wei
        amount_wei = self.w3.to_wei(amount, 'ether')
        
        # Check if there are enough YES and NO tokens
        yes_token = self.get_token_contract(yes_token_address)
        no_token = self.get_token_contract(no_token_address)
        
        yes_balance = yes_token.functions.balanceOf(self.address).call()
        no_balance = no_token.functions.balanceOf(self.address).call()
        
        if yes_balance < amount_wei or no_balance < amount_wei:
            print(f"❌ Insufficient YES/NO token balance for merge")
            print(f"   Required: {self.w3.from_wei(amount_wei, 'ether')} each")
            print(f"   Available: YES={self.w3.from_wei(yes_balance, 'ether')}, NO={self.w3.from_wei(no_balance, 'ether')}")
            return False
        
        # Approve YES and NO tokens for the router
        if not self.approve_token(yes_token, CONTRACT_ADDRESSES["futarchyRouter"], amount_wei):
            return False
            
        if not self.approve_token(no_token, CONTRACT_ADDRESSES["futarchyRouter"], amount_wei):
            return False
        
        print(f"📝 Removing {amount} {token_name} collateral...")
        
        try:
            # Build transaction
            tx = self.futarchy_router.functions.mergePositions(
                self.w3.to_checksum_address(CONTRACT_ADDRESSES["market"]),
                self.w3.to_checksum_address(base_token_address),
                amount_wei
            ).build_transaction({
                'from': self.address,
                'nonce': self.w3.eth.get_transaction_count(self.address),
                'gas': 500000,  # Higher gas limit for complex operation
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.w3.eth.chain_id,
            })
            
            # Sign and send transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(get_raw_transaction(signed_tx))
            
            print(f"⏳ Merge collateral transaction sent: {tx_hash.hex()}")
            
            # Wait for transaction confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt['status'] == 1:
                print(f"✅ {amount} {token_name} collateral removed successfully!")
                return True
            else:
                print(f"❌ Removing collateral failed!")
                return False
        
        except Exception as e:
            print(f"❌ Error removing collateral: {e}")
            return False
    
    def execute_swap(self, token_in, token_out, amount, slippage_percentage=0.5):
        """
        Execute a swap between tokens.
        
        Args:
            token_in: Address of token to sell
            token_out: Address of token to buy
            amount: Amount to swap in wei
            slippage_percentage: Slippage tolerance percentage
            
        Returns:
            bool: Success or failure
        """
        # Determine if this is a YES or NO token
        is_yes_token = token_in == TOKEN_CONFIG["company"]["yes_address"] or token_out == TOKEN_CONFIG["company"]["yes_address"]
        is_no_token = token_in == TOKEN_CONFIG["company"]["no_address"] or token_out == TOKEN_CONFIG["company"]["no_address"]
        
        # Determine which pool to use
        if is_yes_token:
            pool_address = CONTRACT_ADDRESSES["poolYes"]
        elif is_no_token:
            pool_address = CONTRACT_ADDRESSES["poolNo"]
        else:
            # For other tokens, use Balancer
            return self.execute_balancer_swap(token_in, token_out, amount, slippage_percentage)
        
        # Determine if this is a zero_for_one swap
        pool_contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(pool_address),
            abi=UNISWAP_V3_POOL_ABI
        )
        
        token0 = pool_contract.functions.token0().call()
        zero_for_one = token_in.lower() == token0.lower()
        
        # Execute swap using SushiSwap
        sushiswap = SushiSwapExchange(self)
        return sushiswap.swap(pool_address, token_in, token_out, amount, zero_for_one)
    
    def add_liquidity_v3(self, pool_address, token0_amount, token1_amount, price_range_percentage=10, slippage_percentage=0.5):
        """
        Add concentrated liquidity to a SushiSwap V3 pool.
        
        Args:
            pool_address: Address of the pool
            token0_amount: Amount of token0 to add (in wei)
            token1_amount: Amount of token1 to add (in wei)
            price_range_percentage: Percentage range around current price (e.g., 10 for ±10%)
            slippage_percentage: Slippage tolerance percentage
            
        Returns:
            dict: Information about the created position or None if failed
        """
        sushiswap = SushiSwapExchange(self)
        return sushiswap.add_liquidity(pool_address, token0_amount, token1_amount, price_range_percentage, slippage_percentage)
    
    def increase_liquidity_v3(self, token_id, token0_amount, token1_amount, slippage_percentage=0.5):
        """
        Increase liquidity in an existing SushiSwap V3 position.
        
        Args:
            token_id: ID of the position NFT
            token0_amount: Amount of token0 to add (in wei)
            token1_amount: Amount of token1 to add (in wei)
            slippage_percentage: Slippage tolerance percentage
            
        Returns:
            bool: Success or failure
        """
        sushiswap = SushiSwapExchange(self)
        return sushiswap.increase_liquidity(token_id, token0_amount, token1_amount, slippage_percentage)
    
    def decrease_liquidity_v3(self, token_id, liquidity_percentage, slippage_percentage=0.5):
        """
        Decrease liquidity in an existing SushiSwap V3 position.
        
        Args:
            token_id: ID of the position NFT
            liquidity_percentage: Percentage of liquidity to remove (0-100)
            slippage_percentage: Slippage tolerance percentage
            
        Returns:
            dict: Amounts of token0 and token1 received, or None if failed
        """
        sushiswap = SushiSwapExchange(self)
        return sushiswap.decrease_liquidity(token_id, liquidity_percentage, slippage_percentage)
    
    def collect_fees_v3(self, token_id):
        """
        Collect accumulated fees from a SushiSwap V3 position.
        
        Args:
            token_id: ID of the position NFT
            
        Returns:
            dict: Amounts of token0 and token1 collected, or None if failed
        """
        sushiswap = SushiSwapExchange(self)
        return sushiswap.collect_fees(token_id)
    
    def get_position_info_v3(self, token_id):
        """
        Get detailed information about a SushiSwap V3 position.
        
        Args:
            token_id: ID of the position NFT
            
        Returns:
            dict: Position information
        """
        sushiswap = SushiSwapExchange(self)
        return sushiswap.get_position_info(token_id)
    
    def add_liquidity_to_yes_pool(self, gno_amount, sdai_amount, price_range_percentage=10, slippage_percentage=0.5):
        """
        Add concentrated liquidity to the YES pool.
        
        Args:
            gno_amount: Amount of GNO YES tokens to add (in ether units)
            sdai_amount: Amount of sDAI YES tokens to add (in ether units)
            price_range_percentage: Percentage range around current price (e.g., 10 for ±10%)
            slippage_percentage: Slippage tolerance percentage
            
        Returns:
            dict: Information about the created position or None if failed
        """
        # Convert amounts to wei
        gno_amount_wei = self.w3.to_wei(gno_amount, 'ether')
        sdai_amount_wei = self.w3.to_wei(sdai_amount, 'ether')
        
        # Get YES pool address
        pool_address = CONTRACT_ADDRESSES["poolYes"]
        
        # Get pool information to determine token0 and token1
        pool_contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(pool_address),
            abi=UNISWAP_V3_POOL_ABI
        )
        
        token0 = pool_contract.functions.token0().call()
        token1 = pool_contract.functions.token1().call()
        
        # Determine which token is GNO YES and which is sDAI YES
        if token0.lower() == TOKEN_CONFIG["company"]["yes_address"].lower():
            token0_amount = gno_amount_wei
            token1_amount = sdai_amount_wei
        else:
            token0_amount = sdai_amount_wei
            token1_amount = gno_amount_wei
        
        # Add liquidity
        return self.add_liquidity_v3(pool_address, token0_amount, token1_amount, price_range_percentage, slippage_percentage)
    
    def add_liquidity_to_no_pool(self, gno_amount, sdai_amount, price_range_percentage=10, slippage_percentage=0.5):
        """
        Add concentrated liquidity to the NO pool.
        
        Args:
            gno_amount: Amount of GNO NO tokens to add (in ether units)
            sdai_amount: Amount of sDAI NO tokens to add (in ether units)
            price_range_percentage: Percentage range around current price (e.g., 10 for ±10%)
            slippage_percentage: Slippage tolerance percentage
            
        Returns:
            dict: Information about the created position or None if failed
        """
        # Convert amounts to wei
        gno_amount_wei = self.w3.to_wei(gno_amount, 'ether')
        sdai_amount_wei = self.w3.to_wei(sdai_amount, 'ether')
        
        # Get NO pool address
        pool_address = CONTRACT_ADDRESSES["poolNo"]
        
        # Get pool information to determine token0 and token1
        pool_contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(pool_address),
            abi=UNISWAP_V3_POOL_ABI
        )
        
        token0 = pool_contract.functions.token0().call()
        token1 = pool_contract.functions.token1().call()
        
        # Determine which token is GNO NO and which is sDAI NO
        if token0.lower() == TOKEN_CONFIG["company"]["no_address"].lower():
            token0_amount = gno_amount_wei
            token1_amount = sdai_amount_wei
        else:
            token0_amount = sdai_amount_wei
            token1_amount = gno_amount_wei
        
        # Add liquidity
        return self.add_liquidity_v3(pool_address, token0_amount, token1_amount, price_range_percentage, slippage_percentage)
    
    def swap_sdai_to_gno_via_cowswap(self, amount, min_buy_amount=None):
        """
        Swap sDAI for GNO using CoW Swap.
        
        Args:
            amount: Amount of sDAI to sell in ether units
            min_buy_amount: Minimum amount of GNO to buy in ether units (optional)
            
        Returns:
            str: Order UID if successful, None otherwise
        """
        if self.account is None:
            print("❌ No account configured for transactions")
            return None
        
        print(f"\n--- Starting CoW Swap: {amount} sDAI to GNO ---")
        
        # Convert amount to wei
        amount_wei = self.w3.to_wei(amount, 'ether')
        
        # Get token addresses
        sdai_address = TOKEN_CONFIG["currency"]["address"]
        gno_address = TOKEN_CONFIG["company"]["address"]
        
        print(f"SDAI Address: {sdai_address}")
        print(f"GNO Address: {gno_address}")
        
        # Calculate minimum buy amount if not provided
        if min_buy_amount is None:
            # Fetch current price and apply 2% slippage
            try:
                prices = self.get_market_prices()
                if prices and prices.get("gno_spot_price"):
                    # Expected GNO amount = sDAI amount / GNO price
                    expected_gno = float(amount) / prices["gno_spot_price"]
                    # Apply 2% slippage
                    min_buy_amount = expected_gno * 0.98
                    print(f"Calculated min buy amount: {min_buy_amount} GNO (with 2% slippage)")
                else:
                    # Fallback: assume a very conservative estimate
                    min_buy_amount = float(amount) / 200
                    print(f"Using fallback min buy amount: {min_buy_amount} GNO")
            except Exception as e:
                print(f"Error calculating min buy amount: {e}")
                min_buy_amount = float(amount) / 200  # Conservative fallback
        
        min_buy_amount_wei = self.w3.to_wei(min_buy_amount, 'ether')
        
        print(f"Amount: {amount} sDAI ({amount_wei} wei)")
        print(f"Min buy amount: {min_buy_amount} GNO ({min_buy_amount_wei} wei)")
        
        # First approve CoW Swap settlement contract
        print(f"Approving CoW Swap settlement contract: {CONTRACT_ADDRESSES['cowSettlement']}")
        approval_result = self.approve_token(self.sdai_token, CONTRACT_ADDRESSES["cowSettlement"], amount_wei)
        
        if not approval_result:
            print("❌ Failed to approve sDAI for CoW Swap")
            return None
        
        print("✅ Approval successful")
        
        # Try to create and submit an order
        try:
            # Create and sign the order
            print(f"📝 Creating CoW Swap order to swap {amount} sDAI for minimum {min_buy_amount} GNO...")
            order = self.cowswap.create_order(
                sell_token=sdai_address,
                buy_token=gno_address,
                sell_amount=amount_wei,
                buy_amount_min=min_buy_amount_wei
            )
            
            if not order:
                print("❌ Failed to create CoW Swap order")
                print("Trying simplified order creation...")
                order = self.cowswap.create_simple_order(
                    sell_token=sdai_address,
                    buy_token=gno_address,
                    sell_amount=amount_wei,
                    buy_amount_min=min_buy_amount_wei
                )
                
            if not order:
                print("❌ All order creation methods failed")
                return None
                
            print(f"✅ Order created: {order}")
            
            # Submit the order
            print(f"📝 Submitting order to CoW Swap...")
            order_uid = self.cowswap.submit_order(order)
            if not order_uid:
                print("❌ Failed to submit CoW Swap order")
                return None
            
            print(f"✅ CoW Swap order submitted! Your order may take some time to execute.")
            print(f"   You can check the status of your order with order UID: {order_uid}")
            print(f"   Explorer URL: https://explorer.cow.fi/orders/{order_uid}?tab=overview&network=xdai")
            
            # Optionally, check the initial status
            print("Checking initial order status...")
            status = self.cowswap.check_order_status(order_uid)
            
            print(f"--- CoW Swap trade completed successfully ---\n")
            return order_uid
            
        except Exception as e:
            print(f"❌ Error swapping sDAI to GNO via CoW Swap: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def swap_gno_to_sdai_via_cowswap(self, amount, min_buy_amount=None):
        """
        Swap GNO for sDAI using CoW Swap.
        
        Args:
            amount: Amount of GNO to sell in ether units
            min_buy_amount: Minimum amount of sDAI to buy in ether units (optional)
            
        Returns:
            str: Order UID if successful, None otherwise
        """
        if self.account is None:
            raise ValueError("No account configured for transactions")
        
        # Convert amount to wei
        amount_wei = self.w3.to_wei(amount, 'ether')
        
        # Check GNO balance
        has_balance, gno_balance = self.check_token_balance(TOKEN_CONFIG["company"]["address"], amount_wei)
        if not has_balance:
            print(f"❌ Insufficient GNO balance")
            print(f"   Required: {self.w3.from_wei(amount_wei, 'ether')} GNO")
            print(f"   Available: {self.w3.from_wei(gno_balance, 'ether')} GNO")
            return None
        
        # Get token addresses
        sdai_address = TOKEN_CONFIG["currency"]["address"]
        gno_address = TOKEN_CONFIG["company"]["address"]
        
        # Calculate minimum buy amount if not provided
        if min_buy_amount is None:
            # Fetch current price and apply 2% slippage
            try:
                prices = self.get_market_prices()
                if prices and prices.get("gno_spot_price"):
                    # Expected sDAI amount = GNO amount * GNO price
                    expected_sdai = float(amount) * prices["gno_spot_price"]
                    # Apply 2% slippage
                    min_buy_amount = expected_sdai * 0.98
                    print(f"Calculated min buy amount: {min_buy_amount} sDAI (with 2% slippage)")
                else:
                    # Fallback: assume a conservative estimate
                    min_buy_amount = float(amount) * 80
                    print(f"Using fallback min buy amount: {min_buy_amount} sDAI")
            except Exception as e:
                print(f"Error calculating min buy amount: {e}")
                min_buy_amount = float(amount) * 80  # Conservative fallback
        
        min_buy_amount_wei = self.w3.to_wei(min_buy_amount, 'ether')
        
        # First approve CoW Swap settlement contract
        if not self.approve_token(self.gno_token, CONTRACT_ADDRESSES["cowSettlement"], amount_wei):
            return None
        
        try:
            # Create and sign the order
            print(f"📝 Creating CoW Swap order to swap {amount} GNO for minimum {min_buy_amount} sDAI...")
            order = self.cowswap.create_order(
                sell_token=gno_address,
                buy_token=sdai_address,
                sell_amount=amount_wei,
                buy_amount_min=min_buy_amount_wei
            )
            
            if not order:
                print("❌ Failed to create CoW Swap order")
                return None
            
            # Submit the order
            order_uid = self.cowswap.submit_order(order)
            if not order_uid:
                print("❌ Failed to submit CoW Swap order")
                return None
            
            print(f"✅ CoW Swap order submitted! Your order may take some time to execute.")
            print(f"   You can check the status of your order with order UID: {order_uid}")
            
            # Optionally, check the initial status
            status = self.cowswap.check_order_status(order_uid)
            
            return order_uid
            
        except Exception as e:
            print(f"❌ Error swapping GNO to sDAI via CoW Swap: {e}")
            return None
    
    def check_cow_swap_order(self):
        """
        Check status of a CoW Swap order.
        
        Returns:
            dict: Order status information
        """
        order_uid = input("Enter the CoW Swap order UID to check: ")
        return self.cowswap.check_order_status(order_uid)
    
    def run_strategy(self, strategy_func):
        """
        Run a trading strategy.
        
        Args:
            strategy_func: Strategy function that takes the bot as an argument
            
        Returns:
            Any value returned by the strategy function
        """
        if not callable(strategy_func):
            print("❌ Strategy must be a callable function")
            return None
        
        self.current_strategy = strategy_func.__name__ if hasattr(strategy_func, "__name__") else "custom_strategy"
        print(f"🚀 Running strategy: {self.current_strategy}")
        
        try:
            return strategy_func(self)
        except Exception as e:
            print(f"❌ Error executing strategy: {e}")
            return None

    def test_cowswap_signing(self):
        """Test CowSwap signing capabilities and available libraries"""
        # First test available libraries
        test_libraries = self.cowswap.test_libraries()
        
        # Now let's test different signing approaches
        print("\n===== TESTING DIFFERENT SIGNING APPROACHES =====")
        
        # Test 1: Basic personal_sign (ethsign)
        print("\nTest 1: Basic personal_sign (ethsign)")
        try:
            from eth_account.messages import encode_defunct
            
            test_message = "This is a test message for CoW Swap signing"
            message = encode_defunct(text=test_message)
            
            signature = self.w3.eth.account.sign_message(
                message, 
                private_key=self.account.key
            ).signature.hex()
            
            if not signature.startswith('0x'):
                signature = '0x' + signature
                
            print(f"Message: {test_message}")
            print(f"Signature: {signature}")
            
            # Verify the signature
            from eth_account.messages import _hash_eip191_message
            message_hash = _hash_eip191_message(message)
            recovered_address = self.w3.eth.account.recover_message(
                message,
                signature=signature
            )
            
            print(f"Message hash: {message_hash.hex()}")
            print(f"Recovered address: {recovered_address}")
            print(f"Expected address: {self.address}")
            print(f"Match: {recovered_address.lower() == self.address.lower()}")
            
        except Exception as e:
            print(f"❌ Error testing personal_sign: {e}")
        
        # Test 2: Get signing hash from CoW Swap API and sign it directly
        print("\nTest 2: Get and sign CoW Swap order hash")
        try:
            # Get a test quote
            sell_token = self.sdai_token.address
            buy_token = self.gno_token.address
            sell_amount = self.w3.to_wei(0.1, 'ether')  # 0.1 sDAI
            
            quote_result = self.cowswap.get_quote(sell_token, buy_token, sell_amount)
            if not quote_result:
                print("❌ Failed to get test quote")
            else:
                # Try to manually craft EIP-712 hash based on order details
                quote = quote_result["quote"]
                order_id = quote_result.get("id")
                
                print(f"Quote ID: {order_id}")
                print(f"Sell token: {quote['sellToken']}")
                print(f"Buy token: {quote['buyToken']}")
                print(f"Sell amount: {quote['sellAmount']}")
                print(f"Buy amount: {quote['buyAmount']}")
                
                from eth_utils import keccak, to_bytes, to_hex
                
                # Create order information string
                order_info = f"{self.address}:{quote['sellToken']}:{quote['buyToken']}:{quote['sellAmount']}:{quote['buyAmount']}:{quote['validTo']}"
                print(f"Order info string: {order_info}")
                
                # Hash the order info
                order_hash = keccak(to_bytes(text=order_info))
                print(f"Order hash: 0x{order_hash.hex()}")
                
                # Sign the hash
                message = encode_defunct(order_hash)
                signature = self.w3.eth.account.sign_message(
                    message,
                    private_key=self.account.key
                ).signature.hex()
                
                if not signature.startswith('0x'):
                    signature = '0x' + signature
                    
                print(f"Signature: {signature}")
                
                # Create test order
                test_order = {
                    "sellToken": quote["sellToken"],
                    "buyToken": quote["buyToken"],
                    "sellAmount": quote["sellAmount"],
                    "buyAmount": quote["buyAmount"],
                    "validTo": quote["validTo"],
                    "appData": quote["appData"],
                    "feeAmount": quote["feeAmount"],
                    "kind": quote["kind"],
                    "partiallyFillable": quote["partiallyFillable"],
                    "receiver": self.address if quote.get("receiver") is None else quote["receiver"],
                    "from": self.address,
                    "sellTokenBalance": quote["sellTokenBalance"],
                    "buyTokenBalance": quote["buyTokenBalance"],
                    "signingScheme": "ethsign",
                    "signature": signature
                }
                
                print(f"Test order: {test_order}")
                
                # Don't actually submit this test order
                # Just print it for debugging
        
        except Exception as e:
            print(f"❌ Error testing order hash signing: {e}")
            import traceback
            traceback.print_exc()
        
        print("===== END OF SIGNING TESTS =====\n")
        
        return test_libraries