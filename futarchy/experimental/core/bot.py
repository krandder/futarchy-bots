"""
Core Bot Implementation for the Futarchy Trading Bot.

This module is currently in EXPERIMENTAL status.
Contains the main bot implementation with all trading functionality.
"""

import time
import sys
import os
from decimal import Decimal
from web3 import Web3

# Import experimental config
from futarchy.experimental.config import (
    # Network
    DEFAULT_RPC_URLS,
    COWSWAP_API_URL,
    
    # Contracts
    CONTRACT_ADDRESSES,
    CONTRACT_WARNINGS,
    
    # Pools
    POOL_CONFIG_YES,
    POOL_CONFIG_NO,
    BALANCER_CONFIG,
    MIN_SQRT_RATIO,
    MAX_SQRT_RATIO,
    UNISWAP_V3_CONFIG,
    
    # Tokens
    TOKEN_CONFIG,
    DEFAULT_SWAP_CONFIG,
    DEFAULT_PERMIT_CONFIG
)

# Import experimental ABIs
from futarchy.experimental.config.abis import (
    ERC20_ABI,
    UNISWAP_V3_POOL_ABI,
    UNISWAP_V3_PASSTHROUGH_ROUTER_ABI,
    SUSHISWAP_V3_ROUTER_ABI,
    BALANCER_VAULT_ABI,
    BALANCER_BATCH_ROUTER_ABI,
    FUTARCHY_ROUTER_ABI,
    SDAI_RATE_PROVIDER_ABI,
    WXDAI_ABI,
    SDAI_DEPOSIT_ABI
)

class FutarchyBot:
    """Main Futarchy Trading Bot implementation"""
    
    def __init__(self, rpc_url=None, verbose=False):
        """Initialize the Futarchy Bot"""
        self.verbose = verbose
        
        # Use default RPC URL if none provided
        if not rpc_url:
            rpc_url = os.environ.get('RPC_URL', DEFAULT_RPC_URLS[0])
        
        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.w3.is_connected():
            raise ConnectionError(f"Failed to connect to RPC: {rpc_url}")
            
        # Get account from private key if available
        private_key = os.environ.get('PRIVATE_KEY')
        self.address = None
        if private_key:
            account = self.w3.eth.account.from_key(private_key)
            self.address = account.address
        
        # Initialize contract instances
        self.initialize_contracts()
        
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
    
    def get_token_contract(self, address):
        """Get a contract instance for an ERC20 token"""
        return self.w3.eth.contract(
            address=self.w3.to_checksum_address(address),
            abi=ERC20_ABI
        )
    
    def get_balances(self, address=None):
        """
        Get all token balances for an address.
        
        Args:
            address: Address to check (defaults to self.address)
            
        Returns:
            dict: Token balances with exact values (not rounded)
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
        
        # Format balances with exact precision (no rounding)
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
        Print balances in a formatted way with floor rounding to 6 decimal places.
        This ensures that displayed values can be safely used as input amounts.
        
        Args:
            balances: Balance dict (will fetch if None)
        """
        if balances is None:
            balances = self.get_balances()
        
        print("\n=== Token Balances ===")
        
        # Function to floor a number to 6 decimal places
        def floor_to_6(val):
            # Handle scientific notation and regular decimals properly
            if val == 0:
                return 0.0
                
            # Convert to a decimal with proper precision
            from decimal import Decimal, ROUND_DOWN
            d_val = Decimal(str(val))
            
            # Round down to 6 decimal places to ensure no rounding up
            rounded = d_val.quantize(Decimal('0.000001'), rounding=ROUND_DOWN)
            
            # Convert back to float for display
            return float(rounded)
        
        print(f"\n🟢 {TOKEN_CONFIG['currency']['name']} (Currency):")
        print(f"  Wallet: {floor_to_6(balances['currency']['wallet']):.6f}")
        print(f"  YES Tokens: {floor_to_6(balances['currency']['yes']):.6f}")
        print(f"  NO Tokens: {floor_to_6(balances['currency']['no']):.6f}")
        
        print(f"\n🔵 {TOKEN_CONFIG['company']['name']} (Company):")
        print(f"  Wallet: {floor_to_6(balances['company']['wallet']):.6f}")
        print(f"  YES Tokens: {floor_to_6(balances['company']['yes']):.6f}")
        print(f"  NO Tokens: {floor_to_6(balances['company']['no']):.6f}")
        
        print(f"\n🟣 {TOKEN_CONFIG['wagno']['name']} (Wrapped GNO):")
        print(f"  Wallet: {floor_to_6(balances['wagno']['wallet']):.6f}")
    
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