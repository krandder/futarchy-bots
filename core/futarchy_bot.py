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

class FutarchyBot(BaseBot):
    """Main Futarchy Trading Bot implementation"""
    
    # In futarchy_bot.py, add to the __init__ method:
    def __init__(self, rpc_url=None, verbose=False):
        """Initialize the Futarchy Bot"""
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
        elif token_type == "company":
            token_address = TOKEN_CONFIG["company"]["address"]
            token_name = TOKEN_CONFIG["company"]["name"]
            token_contract = self.gno_token
        else:
            raise ValueError(f"Invalid token type: {token_type}")
        
        # Convert amount to wei
        amount_wei = self.w3.to_wei(amount, 'ether')
        
        # Check balance
        has_balance, actual_balance = self.check_token_balance(token_address, amount_wei)
        if not has_balance:
            print(f"❌ Insufficient {token_name} balance")
            print(f"   Required: {self.w3.from_wei(amount_wei, 'ether')} {token_name}")
            print(f"   Available: {self.w3.from_wei(actual_balance, 'ether')} {token_name}")
            return False
        
        # Approve router to spend tokens
        if not self.approve_token(token_contract, CONTRACT_ADDRESSES["futarchyRouter"], amount_wei):
            return False
        
        print(f"📝 Adding {amount} {token_name} as collateral...")
        
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
            
            print(f"⏳ Collateral transaction sent: {tx_hash.hex()}")
            
            # Wait for transaction confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt['status'] == 1:
                print(f"✅ {amount} {token_name} added as collateral successfully!")
                return True
            else:
                print(f"❌ Adding collateral failed!")
                return False
        
        except Exception as e:
            print(f"❌ Error adding collateral: {e}")
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
    
    def execute_swap(self, token_type, is_buy, amount, is_yes_token=True):
        """
        Execute a swap of tokens using SushiSwap V3.
        
        Args:
            token_type: Token type ('currency' or 'company')
            is_buy: True for buy, False for sell
            amount: Amount to swap
            is_yes_token: True for YES tokens, False for NO tokens
            
        Returns:
            bool: Success or failure
        """
        if self.account is None:
            raise ValueError("No account configured for transactions")
        
        # Convert amount to wei
        amount_wei = self.w3.to_wei(amount, 'ether')
        
        # Determine which tokens to use in the swap
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
        
        # When buying YES GNO tokens, we use YES sDAI tokens as payment
        # When buying NO GNO tokens, we use NO sDAI tokens as payment
        if is_buy:
            # For buying, we need to use the correct YES/NO sDAI token as input
            if is_yes_token:
                # To buy YES GNO, use YES sDAI
                token_in = TOKEN_CONFIG["currency"]["yes_address"]  # YES sDAI
                token_out = yes_token_address  # YES GNO
                print(f"Using YES sDAI tokens to buy YES {token_name} tokens")
            else:
                # To buy NO GNO, use NO sDAI
                token_in = TOKEN_CONFIG["currency"]["no_address"]  # NO sDAI
                token_out = no_token_address  # NO GNO
                print(f"Using NO sDAI tokens to buy NO {token_name} tokens")
        else:
            # For selling, we're selling the token_type's YES/NO tokens to get sDAI
            if is_yes_token:
                token_in = yes_token_address  # YES GNO
                token_out = TOKEN_CONFIG["currency"]["yes_address"]  # YES sDAI
                print(f"Selling YES {token_name} tokens for YES sDAI")
            else:
                token_in = no_token_address  # NO GNO
                token_out = TOKEN_CONFIG["currency"]["no_address"]  # NO sDAI
                print(f"Selling NO {token_name} tokens for NO sDAI")
        
        # Check balance of the token we're using as input
        token_in_contract = self.get_token_contract(token_in)
        token_in_balance = token_in_contract.functions.balanceOf(self.address).call()
        
        print(f"Checking balance for token: {token_in}")
        print(f"Required: {self.w3.from_wei(amount_wei, 'ether')}")
        print(f"Available: {self.w3.from_wei(token_in_balance, 'ether')}")
        
        if token_in_balance < amount_wei:
            print(f"❌ Insufficient token balance for swap")
            return False
        
        # Approve token for SushiSwap
        if not self.approve_token(token_in_contract, CONTRACT_ADDRESSES["sushiswap"], amount_wei):
            return False
        
        # Determine which pool to use based on is_yes_token
        pool_address = POOL_CONFIG_YES["address"] if is_yes_token else POOL_CONFIG_NO["address"]
        
        # Create pool contract
        pool_contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(pool_address),
            abi=UNISWAP_V3_POOL_ABI
        )
        
        # Get token0 and token1 from the pool
        token0 = pool_contract.functions.token0().call()
        token1 = pool_contract.functions.token1().call()
        
        # Determine zeroForOne parameter (if tokenIn is token0, then zeroForOne is true)
        zero_for_one = self.w3.to_checksum_address(token_in) == self.w3.to_checksum_address(token0)
        
        # Set sqrtPriceLimitX96 based on swap direction
        sqrt_price_limit_x96 = MIN_SQRT_RATIO if zero_for_one else MAX_SQRT_RATIO
        
        print(f"📝 Executing swap: {'Buy' if is_buy else 'Sell'} {amount} {'YES' if is_yes_token else 'NO'} {token_name} tokens")
        print(f"Pool address: {pool_address}")
        print(f"Token0: {token0}")
        print(f"Token1: {token1}")
        print(f"Token In: {token_in}")
        print(f"Token Out: {token_out}")
        print(f"ZeroForOne: {zero_for_one}")
        
        try:
            # Build transaction for swap
            swap_tx = self.sushiswap_router.functions.swap(
                self.w3.to_checksum_address(pool_address),  # pool address
                self.address,  # recipient
                zero_for_one,  # zeroForOne
                int(amount_wei),  # amountSpecified
                int(sqrt_price_limit_x96),  # sqrtPriceLimitX96
                b''  # data - empty bytes
            ).build_transaction({
                'from': self.address,
                'nonce': self.w3.eth.get_transaction_count(self.address),
                'gas': 1000000,  # INCREASED gas limit substantially
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.w3.eth.chain_id,
            })
            
            # Try to estimate gas to catch potential issues before sending
            try:
                estimated_gas = self.w3.eth.estimate_gas(swap_tx)
                print(f"Estimated gas for this transaction: {estimated_gas}")
                
                # If estimated gas is more than 80% of our limit, increase limit further
                if estimated_gas > 800000:
                    swap_tx['gas'] = int(estimated_gas * 1.25)  # Add 25% buffer
                    print(f"Increased gas limit to: {swap_tx['gas']}")
            except Exception as gas_error:
                print(f"⚠️ Gas estimation failed: {gas_error}")
                print(f"⚠️ This may indicate the transaction will fail, but proceeding anyway...")
            
            signed_swap_tx = self.w3.eth.account.sign_transaction(swap_tx, self.account.key)
            swap_tx_hash = self.w3.eth.send_raw_transaction(get_raw_transaction(signed_swap_tx))
            
            print(f"⏳ Swap transaction sent: {swap_tx_hash.hex()}")
            
            # Wait for confirmation
            swap_receipt = self.w3.eth.wait_for_transaction_receipt(swap_tx_hash)
            
            if swap_receipt['status'] == 1:
                operation = "bought" if is_buy else "sold"
                token_type_text = "YES" if is_yes_token else "NO"
                print(f"✅ Successfully {operation} {amount} {token_type_text} {token_name} tokens!")
                return True
            else:
                print(f"❌ Swap failed with receipt: {swap_receipt}")
                return False
        
        except Exception as e:
            print(f"❌ Error executing swap: {e}")
            return False
    
    def convert_xdai_to_wxdai(self, amount):
        """
        Convert native XDAI to wrapped XDAI (WXDAI).
        
        Args:
            amount: Amount to convert
            
        Returns:
            bool: Success or failure
        """
        if self.account is None:
            raise ValueError("No account configured for transactions")
        
        # Convert amount to wei
        amount_wei = self.w3.to_wei(amount, 'ether')
        
        # Check if we have enough XDAI
        xdai_balance = self.w3.eth.get_balance(self.address)
        if xdai_balance < amount_wei:
            print(f"❌ Insufficient XDAI balance")
            print(f"   Required: {self.w3.from_wei(amount_wei, 'ether')} XDAI")
            print(f"   Available: {self.w3.from_wei(xdai_balance, 'ether')} XDAI")
            return False
        
        # Create WXDAI contract instance
        wxdai_contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(CONTRACT_ADDRESSES["wxdai"]),
            abi=WXDAI_ABI
        )
        
        print(f"📝 Converting {amount} XDAI to WXDAI...")
        
        try:
            # Build transaction to deposit XDAI into WXDAI contract
            deposit_function = wxdai_contract.functions.deposit()
            
            tx = deposit_function.build_transaction({
                'from': self.address,
                'value': amount_wei,
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.address),
                'chainId': self.w3.eth.chain_id,
            })
            
            # Sign and send transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(get_raw_transaction(signed_tx))
            
            print(f"⏳ WXDAI conversion transaction sent: {tx_hash.hex()}")
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt['status'] == 1:
                print(f"✅ Successfully converted {amount} XDAI to WXDAI")
                return True
            else:
                print(f"❌ XDAI conversion failed")
                return False
        except Exception as e:
            print(f"❌ Error converting XDAI to WXDAI: {e}")
            return False
    
    def convert_wxdai_to_sdai(self, amount):
        """
        Convert WXDAI to SDAI.
        
        Args:
            amount: Amount to convert
            
        Returns:
            bool: Success or failure
        """
        if self.account is None:
            raise ValueError("No account configured for transactions")
        
        # Convert amount to wei
        amount_wei = self.w3.to_wei(amount, 'ether')
        
        # Check WXDAI balance
        wxdai_contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(CONTRACT_ADDRESSES["wxdai"]),
            abi=WXDAI_ABI
        )
        
        wxdai_balance = wxdai_contract.functions.balanceOf(self.address).call()
        if wxdai_balance < amount_wei:
            print(f"❌ Insufficient WXDAI balance")
            print(f"   Required: {self.w3.from_wei(amount_wei, 'ether')} WXDAI")
            print(f"   Available: {self.w3.from_wei(wxdai_balance, 'ether')} WXDAI")
            return False
        
        try:
            print(f"📝 Converting {amount} WXDAI to SDAI...")
            
            # The sDAI contract address
            sdai_address = TOKEN_CONFIG["currency"]["address"]
            
            # First approve the sDAI contract to spend the WXDAI
            if not self.approve_token(wxdai_contract, sdai_address, amount_wei):
                return False
            
            # Now, use the deposit function to convert WXDAI to sDAI
            sdai_contract = self.w3.eth.contract(
                address=self.w3.to_checksum_address(sdai_address),
                abi=SDAI_DEPOSIT_ABI
            )
            
            print(f"📝 Depositing WXDAI to get sDAI...")
            
            # Call the deposit function with amount and receiver address
            deposit_tx = sdai_contract.functions.deposit(
                amount_wei,   # assets amount
                self.address  # receiver address
            ).build_transaction({
                'from': self.address,
                'gas': 500000,  # Increase gas limit
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.address),
                'chainId': self.w3.eth.chain_id,
            })
            
            signed_deposit_tx = self.w3.eth.account.sign_transaction(deposit_tx, self.account.key)
            deposit_tx_hash = self.w3.eth.send_raw_transaction(get_raw_transaction(signed_deposit_tx))
            
            print(f"⏳ sDAI deposit transaction sent: {deposit_tx_hash.hex()}")
            
            # Wait for deposit confirmation
            deposit_receipt = self.w3.eth.wait_for_transaction_receipt(deposit_tx_hash)
            
            if deposit_receipt['status'] == 1:
                print(f"✅ Successfully converted {amount} WXDAI to sDAI")
                return True
            else:
                print(f"❌ sDAI deposit failed with receipt: {deposit_receipt}")
                return False
                
        except Exception as e:
            print(f"❌ Error converting WXDAI to sDAI: {e}")
            return False
    
    def add_sdai_collateral(self, amount):
        """
        Add sDAI as collateral by splitting it into YES and NO tokens.
        
        Args:
            amount: Amount to add
            
        Returns:
            bool: Success or failure
        """
        # This is essentially the same as add_collateral but specifically for sDAI
        return self.add_collateral("currency", amount)
    
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