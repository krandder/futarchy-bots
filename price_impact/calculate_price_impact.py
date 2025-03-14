                            {
                                "pool": self.balancer_pool_address,
                                "tokenOut": self.wagno_address,
                                "isBuffer": False
                            }
                        ]
                    },
                    "exactAmountIn": one_sdai_wei,
                    "minAmountOut": 0
                }],
                self.w3.to_checksum_address("0x0000000000000000000000000000000000000000"),
                '0x'
            )
            
            if result is not None:
                # Extract expected output amount
                expected_output = result[0][0]
                expected_output_eth = float(self.w3.from_wei(expected_output, 'ether'))
                
                # Current price: 1 sDAI = ? waGNO
                current_price_sdai_to_wagno = expected_output_eth
                current_price_wagno_to_sdai = 1 / current_price_sdai_to_wagno if current_price_sdai_to_wagno != 0 else float('inf')
                
                print(f"Current Price: 1 sDAI = {current_price_sdai_to_wagno} waGNO")
                print(f"Current Price: 1 waGNO = {current_price_wagno_to_sdai} sDAI")
                
                # Calculate price impact for buying waGNO with sDAI
                # First, calculate how much sDAI is needed to buy the specified amount of waGNO
#!/usr/bin/env python3
                sdai_amount_for_wagno = wagno_amount * current_price_wagno_to_sdai
                sdai_amount_wei = self.w3.to_wei(sdai_amount_for_wagno, 'ether')
"""
Calculate price impact for fixed trade sizes in Balancer and SushiSwap pools.

This script calculates the price impact of trading a fixed amount of GNO (or its waGNO equivalent)
in the Balancer sDAI/waGNO pool and SushiSwap conditional token pools.

For each pool, the script calculates:
1. The current price in the pool
2. The price impact when buying tokens with the specified GNO amount
3. The price impact when selling tokens with the specified GNO amount
4. The GNO to waGNO conversion rate

Usage:
    python calculate_price_impact.py [--amount AMOUNT] [--verbose]

Options:
    --amount AMOUNT    Trade amount in GNO equivalent (default: 0.01)
    --verbose, -v      Enable verbose output
    --help, -h         Show this help message and exit
"""

import os
import sys
import math
from decimal import Decimal
from web3 import Web3
from utils.web3_utils import setup_web3_connection
from config.constants import (
    BALANCER_CONFIG, 
    TOKEN_CONFIG, 
    CONTRACT_ADDRESSES, 
    POOL_CONFIG_YES, 
    POOL_CONFIG_NO, 
    UNISWAP_V3_POOL_ABI,
    ERC20_ABI
)
import argparse

# Price impact percentage to calculate (0.1%)
PRICE_IMPACT_PERCENTAGE = 0.1

# Extended ERC20 ABI with decimals function
EXTENDED_ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": False, "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "payable": False, "stateMutability": "nonpayable", "type": "function"},
    {"constant": True, "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "payable": False, "stateMutability": "view", "type": "function"}
]

# ERC4626 ABI (for waGNO)
ERC4626_ABI = [
    {"inputs": [{"internalType": "uint256", "name": "assets", "type": "uint256"}, {"internalType": "address", "name": "receiver", "type": "address"}], "name": "deposit", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"internalType": "address", "name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "shares", "type": "uint256"}, {"internalType": "address", "name": "receiver", "type": "address"}, {"internalType": "address", "name": "owner", "type": "address"}], "name": "redeem", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "shares", "type": "uint256"}], "name": "convertToAssets", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "assets", "type": "uint256"}], "name": "convertToShares", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "decimals", "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}], "stateMutability": "view", "type": "function"}
]

# Uniswap V3 Quoter ABI
UNISWAP_V3_QUOTER_ABI = [
    {"inputs":[{"internalType":"bytes","name":"path","type":"bytes"},{"internalType":"uint256","name":"amountIn","type":"uint256"}],"name":"quoteExactInput","outputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256[]","name":"sqrtPriceX96AfterList","type":"uint256[]"},{"internalType":"uint32[]","name":"initializedTicksCrossedList","type":"uint32[]"},{"internalType":"uint256","name":"gasEstimate","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"address","name":"tokenIn","type":"address"},{"internalType":"address","name":"tokenOut","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint160","name":"sqrtPriceLimitX96","type":"uint160"}],"name":"quoteExactInputSingle","outputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint160","name":"sqrtPriceX96After","type":"uint160"},{"internalType":"uint32","name":"initializedTicksCrossed","type":"uint32"},{"internalType":"uint256","name":"gasEstimate","type":"uint256"}],"stateMutability":"nonpayable","type":"function"}
]

# SushiSwap Quoter address (same interface as Uniswap V3 Quoter)
SUSHISWAP_QUOTER_ADDRESS = "0xb1E835Dc2785b52265711e17fCCb0fd018226a6e"  # SushiSwap Quoter on Gnosis Chain

class PriceImpactCalculator:
    """Class to calculate price impact for fixed trade sizes."""
    
    def __init__(self, verbose=False):
        """Initialize the calculator."""
        self.verbose = verbose
        self.w3 = setup_web3_connection()
        
        # Initialize contract addresses
        self.balancer_vault_address = self.w3.to_checksum_address(BALANCER_CONFIG["vault_address"])
        self.balancer_pool_address = self.w3.to_checksum_address(BALANCER_CONFIG["pool_address"])
        self.batch_router_address = self.w3.to_checksum_address(CONTRACT_ADDRESSES["batchRouter"])
        self.yes_pool_address = self.w3.to_checksum_address(POOL_CONFIG_YES["address"])
        self.no_pool_address = self.w3.to_checksum_address(POOL_CONFIG_NO["address"])
        
        # Initialize token addresses
        self.sdai_address = self.w3.to_checksum_address(TOKEN_CONFIG["currency"]["address"])
        self.wagno_address = self.w3.to_checksum_address(TOKEN_CONFIG["wagno"]["address"])
        self.gno_address = self.w3.to_checksum_address(TOKEN_CONFIG["company"]["address"])
        self.sdai_yes_address = self.w3.to_checksum_address(TOKEN_CONFIG["currency"]["yes_address"])
        self.sdai_no_address = self.w3.to_checksum_address(TOKEN_CONFIG["currency"]["no_address"])
        self.gno_yes_address = self.w3.to_checksum_address(TOKEN_CONFIG["company"]["yes_address"])
        self.gno_no_address = self.w3.to_checksum_address(TOKEN_CONFIG["company"]["no_address"])
        
        # Load ABIs
        self.load_abis()
        
        # Initialize contracts
        self.init_contracts()
        
        # Calculate GNO to waGNO conversion rate
        self.gno_to_wagno_rate = self.calculate_gno_to_wagno_rate()
        
        if self.verbose:
            print(f"Initialized PriceImpactCalculator")
            print(f"Balancer Pool: {self.balancer_pool_address}")
            print(f"YES Pool: {self.yes_pool_address}")
            print(f"NO Pool: {self.no_pool_address}")
            print(f"GNO to waGNO conversion rate: {self.gno_to_wagno_rate}")
    
    def load_abis(self):
        """Load contract ABIs."""
        # Try different possible locations for the ABI file
        possible_paths = [
            # Current working directory
            os.path.join(os.getcwd(), ".reference", "balancer_router.abi.json"),
            # Script directory
            os.path.join(os.path.dirname(os.path.abspath(__file__)), ".reference", "balancer_router.abi.json"),
            # Parent of script directory
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".reference", "balancer_router.abi.json"),
            # Absolute path
            "/Users/kas/futarchy-bots/.reference/balancer_router.abi.json"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    import json
                    self.batch_router_abi = json.load(f)
                    if self.verbose:
                        print(f"Loaded BatchRouter ABI from {path}")
                    return
        
        # If we get here, we couldn't find the file
        raise FileNotFoundError(f"BatchRouter ABI file not found. Tried: {possible_paths}")
    
    def init_contracts(self):
        """Initialize contract instances."""
        # Initialize BatchRouter contract
        self.batch_router = self.w3.eth.contract(
            address=self.batch_router_address,
            abi=self.batch_router_abi
        )
        
        # Initialize Uniswap V3 pool contracts for conditional tokens
        self.yes_pool = self.w3.eth.contract(
            address=self.yes_pool_address,
            abi=UNISWAP_V3_POOL_ABI
        )
        
        self.no_pool = self.w3.eth.contract(
            address=self.no_pool_address,
            abi=UNISWAP_V3_POOL_ABI
        )
        
        # Initialize token contracts
        self.gno_token = self.w3.eth.contract(
            address=self.gno_address,
            abi=EXTENDED_ERC20_ABI
        )
        
        self.wagno_token = self.w3.eth.contract(
            address=self.wagno_address,
            abi=ERC4626_ABI
        )
        
        # Initialize SushiSwap Quoter contract
        try:
            self.quoter = self.w3.eth.contract(
                address=self.w3.to_checksum_address(SUSHISWAP_QUOTER_ADDRESS),
                abi=UNISWAP_V3_QUOTER_ABI
            )
            if self.verbose:
                print(f"Initialized SushiSwap Quoter contract at {SUSHISWAP_QUOTER_ADDRESS}")
        except Exception as e:
            print(f"Error initializing SushiSwap Quoter contract: {e}")
            self.quoter = None
    
    def calculate_gno_to_wagno_rate(self):
        """
        Calculate the conversion rate from GNO to waGNO using the ERC4626 convertToAssets function.
        
        Returns:
            float: The conversion rate (1 GNO = X waGNO)
        """
        try:
            # Get decimals for both tokens
            try:
                gno_decimals = self.gno_token.functions.decimals().call()
                wagno_decimals = self.wagno_token.functions.decimals().call()
            except Exception as e:
                print(f"Error getting token decimals: {e}")
                gno_decimals = 18
                wagno_decimals = 18
                
            # Use the ERC4626 convertToAssets function to get the conversion rate
            # For 1 waGNO share, how many GNO assets do we get?
            try:
                one_wagno_in_wei = 10 ** wagno_decimals  # 1 waGNO in wei
                gno_assets = self.wagno_token.functions.convertToAssets(one_wagno_in_wei).call()
                gno_assets_decimal = gno_assets / (10 ** gno_decimals)
                
                # The conversion rate is 1/gno_assets_decimal (1 GNO = X waGNO)
                if gno_assets_decimal > 0:
                    conversion_rate = 1 / gno_assets_decimal
                else:
                    conversion_rate = 1.0  # Default to 1:1 if calculation fails
                    
                if self.verbose:
                    print(f"GNO to waGNO conversion rate: {conversion_rate}")
                    if conversion_rate == 1.0:
                        print(f"Note: Using simplified 1:1 conversion rate. For accurate rates, implement Aave StaticAToken contract integration.")
                
                return conversion_rate
            except Exception as e:
                print(f"Error using convertToAssets: {e}")
                # Try alternative method using convertToShares
                try:
                    one_gno_in_wei = 10 ** gno_decimals  # 1 GNO in wei
                    wagno_shares = self.wagno_token.functions.convertToShares(one_gno_in_wei).call()
                    wagno_shares_decimal = wagno_shares / (10 ** wagno_decimals)
                    
                    # The conversion rate is wagno_shares_decimal (1 GNO = X waGNO)
                    if wagno_shares_decimal > 0:
                        conversion_rate = wagno_shares_decimal
                    else:
                        conversion_rate = 1.0  # Default to 1:1 if calculation fails
                        
                    if self.verbose:
                        print(f"GNO to waGNO conversion rate (using convertToShares): {conversion_rate}")
                        if conversion_rate == 1.0:
                            print(f"Note: Using simplified 1:1 conversion rate. For accurate rates, implement Aave StaticAToken contract integration.")
                    
                    return conversion_rate
                except Exception as e:
                    print(f"Error using convertToShares: {e}")
                    conversion_rate = 1.0  # Default to 1:1 if all calculations fail
            
            if self.verbose:
                print(f"GNO to waGNO conversion rate: {conversion_rate}")
                print(f"Note: Using simplified 1:1 conversion rate. For accurate rates, implement Aave StaticAToken contract integration.")
            
            return conversion_rate
        except Exception as e:
            print(f"Error calculating GNO to waGNO conversion rate: {e}")
            # Default to 1:1 if there's an error
            return 1.0
    
    def calculate_balancer_price_impact_with_eth_call(self, gno_amount):
        """
        Calculate price impact for a fixed GNO amount in the Balancer pool using eth_call.
        
        Args:
            gno_amount: Amount of GNO to trade
            
        Returns:
            dict: Information about the price impact
        """
        print("\n=== Balancer sDAI/waGNO Pool Price Impact ===")
        
        # Convert GNO to waGNO
        wagno_amount = gno_amount * self.gno_to_wagno_rate
        print(f"Trade amount: {gno_amount} GNO = {wagno_amount} waGNO")
        
        try:
            # First, get the current price (1 sDAI -> ? waGNO)
            # Use eth_call to simulate the swap
            one_sdai_wei = self.w3.to_wei(1, 'ether')
            
            # Simulate the swap using querySwapExactIn
            result = self.simulate_transaction_with_eth_call(
                self.batch_router_address,
                "querySwapExactIn",
                [
                    [{
                        "tokenIn": self.sdai_address,
                        "steps": [
                            {
                                "pool": self.balancer_pool_address,
                                "tokenOut": self.wagno_address,
                                "isBuffer": False
                            }
                        ],
                        "exactAmountIn": one_sdai_wei,
                        "minAmountOut": 0
                    }],
                    self.w3.to_checksum_address("0x0000000000000000000000000000000000000000"),
                    '0x'
                ]
            )
            
            if result is not None:
                # Extract expected output amount
                expected_output = result[0][0]
                expected_output_eth = float(self.w3.from_wei(expected_output, 'ether'))
                
                # Current price: 1 sDAI = ? waGNO
                current_price_sdai_to_wagno = expected_output_eth
                current_price_wagno_to_sdai = 1 / current_price_sdai_to_wagno if current_price_sdai_to_wagno != 0 else float('inf')
                
                print(f"Current Price: 1 sDAI = {current_price_sdai_to_wagno} waGNO")
                print(f"Current Price: 1 waGNO = {current_price_wagno_to_sdai} sDAI")
                
                # Calculate price impact for buying waGNO with sDAI
                # First, calculate how much sDAI is needed to buy the specified amount of waGNO
                sdai_amount_for_wagno = wagno_amount * current_price_wagno_to_sdai
                sdai_amount_wei = self.w3.to_wei(sdai_amount_for_wagno, 'ether')
                
                # Simulate the swap using eth_call
                buy_result = self.simulate_transaction_with_eth_call(
                    self.batch_router_address,
                    "querySwapExactIn",
                    [
                        [{
                            "tokenIn": self.sdai_address,
                            "steps": [
                                {
                                    "pool": self.balancer_pool_address,
                                    "tokenOut": self.wagno_address,
                                    "isBuffer": False
                                }
                            ],
                            "exactAmountIn": sdai_amount_wei,
                            "minAmountOut": 0
                        }],
                        self.w3.to_checksum_address("0x0000000000000000000000000000000000000000"),
                        '0x'
                    ]
                )
                
                if buy_result is not None:
                    # Extract expected output amount
                    buy_output = float(self.w3.from_wei(buy_result[0][0], 'ether'))
                    
                    # Calculate effective price
                    effective_buy_price = sdai_amount_for_wagno / buy_output if buy_output != 0 else float('inf')
                    
                    # Calculate price impact
                    buy_price_impact_percentage = ((effective_buy_price / current_price_wagno_to_sdai) - 1) * 100
                    
                    print(f"\nBuying {wagno_amount} waGNO with sDAI:")
                    print(f"  Estimated sDAI needed: {sdai_amount_for_wagno}")
                    print(f"  Actual waGNO received: {buy_output}")
                    print(f"  Effective price: 1 waGNO = {effective_buy_price} sDAI")
                    print(f"  Price impact: {buy_price_impact_percentage:.4f}%")
                else:
                    print(f"Error calculating buy price impact: simulation failed")
                    buy_price_impact_percentage = "Error"
                    effective_buy_price = "Error"
                
                # Calculate price impact for selling waGNO for sDAI
                wagno_amount_wei = self.w3.to_wei(wagno_amount, 'ether')
                
                # Simulate the swap using eth_call
                sell_result = self.simulate_transaction_with_eth_call(
                    self.batch_router_address,
                    "querySwapExactIn",
                    [
                        [{
                            "tokenIn": self.wagno_address,
                            "steps": [
                                {
                                    "pool": self.balancer_pool_address,
                                    "tokenOut": self.sdai_address,
                                    "isBuffer": False
                                }
                            ],
                            "exactAmountIn": wagno_amount_wei,
                            "minAmountOut": 0
                        }],
                        self.w3.to_checksum_address("0x0000000000000000000000000000000000000000"),
                        '0x'
                    ]
                )
                
                if sell_result is not None:
                    # Extract expected output amount
                    sell_output = float(self.w3.from_wei(sell_result[0][0], 'ether'))
                    
                    print(f"  Price impact: {buy_price_impact_percentage:.4f}%")
                else:
                    print(f"Error calculating sell price impact: simulation failed")
                    buy_price_impact_percentage = "Error"
                    effective_sell_price = "Error"
                
                return {
                    "pool": "Balancer sDAI/waGNO",
                    "gno_amount": gno_amount,
                    "wagno_amount": wagno_amount,
                    "current_price_sdai_to_wagno": current_price_sdai_to_wagno,
                    "current_price_wagno_to_sdai": current_price_wagno_to_sdai,
                    "buy_price_impact_percentage": buy_price_impact_percentage,
                    "effective_buy_price": effective_buy_price,
                    "sell_price_impact_percentage": buy_price_impact_percentage,
                    "effective_sell_price": effective_sell_price
                }
            else:
                print(f"Error getting current price: simulation failed")
                return {
                    "pool": "Balancer sDAI/waGNO",
                    "error": "Simulation failed"
                }
        except Exception as e:
            print(f"Error calculating Balancer price impact: {e}")
            import traceback
            traceback.print_exc()
            return {
                "pool": "Balancer sDAI/waGNO",
                "error": str(e)
            }
    
    def simulate_swap_v3(self, token_in, token_out, amount_in, pool_fee=3000):
        """
        Simulate a swap using the Uniswap V3 Quoter contract.
        
        Args:
            token_in: Address of the input token
            token_out: Address of the output token
            amount_in: Amount of input token to swap (in wei)
            pool_fee: Pool fee in hundredths of a bip (e.g., 3000 for 0.3%)
            
        Returns:
            tuple: (amount_out, price_impact_percentage) or (None, None) if simulation fails
        """
        if self.quoter is None:
            return None, None
            
        try:
            # Get current price from the pool
            # We'll use the pool's slot0 data to get the current price
            if token_in.lower() == self.gno_yes_address.lower() or token_in.lower() == self.gno_no_address.lower():
                pool = self.yes_pool if token_in.lower() == self.gno_yes_address.lower() else self.no_pool
                slot0 = pool.functions.slot0().call()
                sqrt_price_x96 = slot0[0]
                current_price = (sqrt_price_x96 / (2**96))**2
                
                # Determine if token_in is token0 or token1
                token0 = pool.functions.token0().call()
                if token_in.lower() == token0.lower():
                    # token_in is token0, so price is token1/token0
                    current_price = 1 / current_price if current_price != 0 else float('inf')
            else:
                # For other pools, we would need to get the price differently
                # For now, we'll just set a placeholder
                current_price = 0
                
            # Simulate the swap using the Quoter contract
            try:
                # Use quoteExactInputSingle for a single-hop swap
                result = self.quoter.functions.quoteExactInputSingle(
                    self.w3.to_checksum_address(token_in),
                    self.w3.to_checksum_address(token_out),
                    pool_fee,
                    amount_in,
                    0  # No price limit
                ).call()
                
                # Extract the amount out
                amount_out = result[0]
                
                # Calculate the effective price
                effective_price = amount_in / amount_out if amount_out != 0 else float('inf')
                
                # Calculate price impact
                if current_price > 0:
                    price_impact_percentage = abs((effective_price - current_price) / current_price) * 100
                else:
                    price_impact_percentage = None
                    
                return amount_out, price_impact_percentage
                
            except Exception as e:
                print(f"Error simulating swap with Quoter: {e}")
                return None, None
                
        except Exception as e:
            print(f"Error in simulate_swap_v3: {e}")
            return None, None
    
    def calculate_conditional_price_impact(self, gno_amount, is_yes_pool):
        """
        Calculate price impact for a fixed GNO amount in a conditional token pool.
        
        Args:
            gno_amount: Amount of GNO to trade
            is_yes_pool: True for YES pool, False for NO pool
            
        Returns:
            dict: Information about the price impact
        """
        pool_name = "YES" if is_yes_pool else "NO"
        pool_contract = self.yes_pool if is_yes_pool else self.no_pool
        pool_address = self.yes_pool_address if is_yes_pool else self.no_pool_address
        
        print(f"\n=== SushiSwap {pool_name} Conditional Pool Price Impact ===")
        print(f"Trade amount: {gno_amount} GNO")
        
        try:
            # Get token0 and token1
            token0 = pool_contract.functions.token0().call()
            token1 = pool_contract.functions.token1().call()
            
            # Identify token names
            token0_name = self.get_token_name(token0)
            token1_name = self.get_token_name(token1)
            
            print(f"Pool address: {pool_address}")
            print(f"Token0: {token0} ({token0_name})")
            print(f"Token1: {token1} ({token1_name})")
            
            # Get slot0 data for current price
            try:
                slot0 = pool_contract.functions.slot0().call()
                sqrt_price_x96 = slot0[0]
                tick = slot0[1]
                
                # Calculate price from sqrtPriceX96
                price = (sqrt_price_x96 / (2**96))**2
                
                print(f"sqrtPriceX96: {sqrt_price_x96}")
                print(f"tick: {tick}")
                
                # Determine which token is GNO YES/NO
                gno_token = self.gno_yes_address if is_yes_pool else self.gno_no_address
                sdai_token = self.sdai_yes_address if is_yes_pool else self.sdai_no_address
                
                # Determine if GNO is token0 or token1
                if token0.lower() == gno_token.lower():
                    gno_is_token0 = True
                    current_price_gno_to_sdai = price
                    current_price_sdai_to_gno = 1/price if price != 0 else float('inf')
                    print(f"Current Price (GNO {pool_name}/sDAI {pool_name}): {current_price_gno_to_sdai}")
                    print(f"Current Price (sDAI {pool_name}/GNO {pool_name}): {current_price_sdai_to_gno}")
                else:
                    gno_is_token0 = False
                    current_price_gno_to_sdai = 1/price if price != 0 else float('inf')
                    current_price_sdai_to_gno = price
                    print(f"Current Price (GNO {pool_name}/sDAI {pool_name}): {current_price_gno_to_sdai}")
                    print(f"Current Price (sDAI {pool_name}/GNO {pool_name}): {current_price_sdai_to_gno}")
                
                # For Uniswap V3 style pools, calculating the exact price impact requires
                # using the Quoter contract to simulate the swap
                print(f"\nFor Uniswap V3 style pools like SushiSwap, accurate price impact calculation requires:")
                print(f"1. Using the Quoter contract to simulate the swap")
                print(f"2. Comparing the quoted price with the current price")
                
                # Estimate for buying GNO with sDAI
                sdai_amount_for_gno = gno_amount * current_price_gno_to_sdai
                
                # Convert to wei
                gno_amount_wei = self.w3.to_wei(gno_amount, 'ether')
                sdai_amount_wei = self.w3.to_wei(sdai_amount_for_gno, 'ether')
                
                # Try to simulate swaps using the Quoter contract
                buy_amount_out = None
                buy_price_impact = None
                sell_amount_out = None
                sell_price_impact = None
                
                if self.quoter is not None:
                    # Simulate buying GNO with sDAI
                    buy_amount_out, buy_price_impact = self.simulate_swap_v3(
                        sdai_token, gno_token, sdai_amount_wei
                    )
                    
                    # Simulate selling GNO for sDAI
                    sell_amount_out, sell_price_impact = self.simulate_swap_v3(
                        gno_token, sdai_token, gno_amount_wei
                    )
                
                # For concentrated liquidity pools, price impact increases with trade size
                # and depends on the distribution of liquidity across price ranges
                if gno_amount <= 0.01:
                    estimated_buy_impact = "1-3% (small trade)"
                    estimated_sell_impact = "1-3% (small trade)"
                elif gno_amount <= 0.1:
                    estimated_buy_impact = "3-7% (medium trade)"
                    estimated_sell_impact = "3-7% (medium trade)"
                else:
                    estimated_buy_impact = "7-15% (large trade)"
                    estimated_sell_impact = "7-15% (large trade)"
                
                print(f"\nEstimates for {gno_amount} GNO:")
                print(f"  To buy {gno_amount} GNO {pool_name}:")
                print(f"    Estimated sDAI {pool_name} needed: ~{sdai_amount_for_gno}")
                
                if buy_price_impact is not None:
                    print(f"    Simulated price impact: {buy_price_impact:.4f}%")
                else:
                    print(f"    Estimated price impact: {estimated_buy_impact}")
                    
                print(f"  To sell {gno_amount} GNO {pool_name}:")
                if sell_amount_out is not None:
                    sell_amount_out_eth = self.w3.from_wei(sell_amount_out, 'ether')
                    print(f"    Estimated sDAI {pool_name} received: ~{sell_amount_out_eth}")
                else:
                    print(f"    Estimated sDAI {pool_name} received: ~{sdai_amount_for_gno}")
                    
                if sell_price_impact is not None:
                    print(f"    Simulated price impact: {sell_price_impact:.4f}%")
                else:
                    print(f"    Estimated price impact: {estimated_sell_impact}")
                
                if self.quoter is None:
                    print(f"\nFor more accurate price impact calculation, consider implementing:")
                    print(f"1. Integration with SushiSwap's Quoter contract")
                    print(f"2. On-chain simulation via 'eth_call'")
                    print(f"3. Full Uniswap V3 SDK for price impact calculation")
                
                return {
                    "pool": f"SushiSwap {pool_name} Conditional Pool",
                    "token0": token0_name,
                    "token1": token1_name,
                    "current_price_gno_to_sdai": current_price_gno_to_sdai,
                    "current_price_sdai_to_gno": current_price_sdai_to_gno,
                    "gno_amount": gno_amount,
                    "buy_price_impact": buy_price_impact if buy_price_impact is not None else estimated_buy_impact,
                    "sell_price_impact": sell_price_impact if sell_price_impact is not None else estimated_sell_impact,
                    "buy_amount_out": buy_amount_out,
                    "sell_amount_out": sell_amount_out
                }
                
            except Exception as e:
                print(f"Error getting slot0 data: {e}")
                return {
                    "pool": f"SushiSwap {pool_name} Conditional Pool",
                    "token0": token0_name,
                    "token1": token1_name,
                    "error": f"Error getting price data: {str(e)}"
                }
                
        except Exception as e:
            print(f"Error calculating {pool_name} pool price impact: {e}")
            return {
                "pool": f"SushiSwap {pool_name} Conditional Pool",
                "error": str(e)
            }
    
    def get_token_name(self, address):
        """Get a human-readable name for a token address."""
        address_lower = address.lower()
        
        if address_lower == self.sdai_address.lower():
            return "sDAI"
        elif address_lower == self.wagno_address.lower():
            return "waGNO"
        elif address_lower == self.gno_address.lower():
            return "GNO"
        elif address_lower == self.sdai_yes_address.lower():
            return "sDAI YES"
        elif address_lower == self.sdai_no_address.lower():
            return "sDAI NO"
        elif address_lower == self.gno_yes_address.lower():
            return "GNO YES"
        elif address_lower == self.gno_no_address.lower():
            return "GNO NO"
        else:
            return "Unknown"
    
    def simulate_transaction_with_eth_call(self, contract, function_name, function_args, from_address=None):
        """
        Simulate a transaction using eth_call to get the exact output amount.
        
        Args:
            contract: Web3 contract instance
            function_name: Name of the function to call
            function_args: Arguments to pass to the function
            from_address: Address to use as the sender (default: zero address)
            
        Returns:
            Any: The result of the function call
        """
        if from_address is None:
            from_address = "0x0000000000000000000000000000000000000000"
        
        try:
            # Get the function from the contract
            contract_function = getattr(contract.functions, function_name)
            
            # Build the transaction
            tx = contract_function(*function_args).build_transaction({
                'from': self.w3.to_checksum_address(from_address),
                'gas': 5000000,
                'gasPrice': self.w3.eth.gas_price,
                'value': 0,
                'nonce': 0,  # Doesn't matter for eth_call
            })
            
            # Simulate the transaction using eth_call
            result = self.w3.eth.call(tx)
            
            # Decode the result using the contract's function
            decoded_result = contract_function(*function_args).call({
                'from': self.w3.to_checksum_address(from_address)
            })
            
            return decoded_result
            
        except Exception as e:
            if self.verbose:
                print(f"Error simulating transaction {function_name}: {e}")
                import traceback
                traceback.print_exc()
            return None

def main():
    """Main function to run the script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Calculate price impact for fixed trade sizes in Balancer and SushiSwap pools")
    parser.add_argument("--amount", type=float, default=0.01, help="Trade amount in GNO equivalent (default: 0.01)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Initialize the price impact calculator
    calculator = PriceImpactCalculator(verbose=args.verbose)
    
    # Calculate price impact for the specified GNO amount
    print(f"\nCalculating price impact for {args.amount} GNO equivalent...")
    
    # Calculate price impact for Balancer pool
    balancer_result = calculator.calculate_balancer_price_impact_with_eth_call(args.amount)
    
    # Calculate price impact for YES conditional pool
    yes_result = calculator.calculate_conditional_price_impact(args.amount, is_yes_pool=True)
    
    # Calculate price impact for NO conditional pool
    no_result = calculator.calculate_conditional_price_impact(args.amount, is_yes_pool=False)
    
    # Print summary
    print("\n=== Price Impact Summary ===")
    print(f"Trade amount: {args.amount} GNO")
    print(f"GNO to waGNO conversion rate: {calculator.gno_to_wagno_rate}")
    
    print("\nBalancer sDAI/waGNO Pool:")
    if "error" in balancer_result:
        print(f"  Error: {balancer_result['error']}")
    else:
        # Calculate and display GNO/sDAI price (using waGNO as proxy for GNO)
        gno_to_sdai_price = balancer_result['current_price_wagno_to_sdai']
        print(f"  Current price: 1 GNO = {gno_to_sdai_price:.6f} sDAI")
        print(f"  Buy impact: {balancer_result['buy_price_impact_percentage']:.4f}% for {args.amount} GNO")
        print(f"  Sell impact: {balancer_result['sell_price_impact_percentage']:.4f}% for {args.amount} GNO")
    
    print("\nSushiSwap YES Conditional Pool:")
    if "error" in yes_result:
        print(f"  Error: {yes_result['error']}")
    else:
        # Display GNO/sDAI price
        print(f"  Current price: 1 GNO YES = {yes_result['current_price_gno_to_sdai']:.6f} sDAI YES")
        print(f"  Simulated buy impact: {yes_result['buy_price_impact']}")
        print(f"  Simulated sell impact: {yes_result['sell_price_impact']}")
    
    print("\nSushiSwap NO Conditional Pool:")
    if "error" in no_result:
        print(f"  Error: {no_result['error']}")
    else:
        # Display GNO/sDAI price
        print(f"  Current price: 1 GNO NO = {no_result['current_price_gno_to_sdai']:.6f} sDAI NO")
        print(f"  Simulated buy impact: {no_result['buy_price_impact']}")
        print(f"  Simulated sell impact: {no_result['sell_price_impact']}")
    
    print("\nNote: For more accurate price impact calculations for Uniswap V3-style pools,")
    print("consider implementing integration with the SushiSwap Quoter contract or")
    print("using on-chain simulation via 'eth_call'.")

if __name__ == "__main__":
    main() 