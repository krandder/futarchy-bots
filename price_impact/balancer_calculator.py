"""
Module for calculating price impact in Balancer pools.
"""

import os
import json
from .utils.web3_utils import simulate_transaction_with_eth_call

class BalancerPriceImpactCalculator:
    """Class to calculate price impact for Balancer pools."""
    
    def __init__(self, w3, balancer_pool_address, balancer_vault_address, batch_router_address, 
                 sdai_address, wagno_address, gno_to_wagno_rate=1.0, verbose=False):
        """
        Initialize the Balancer price impact calculator.
        
        Args:
            w3: Web3 instance
            balancer_pool_address: Address of the Balancer pool
            balancer_vault_address: Address of the Balancer vault
            batch_router_address: Address of the Balancer batch router
            sdai_address: Address of the sDAI token
            wagno_address: Address of the waGNO token
            gno_to_wagno_rate: Conversion rate from GNO to waGNO
            verbose: Whether to print verbose output
        """
        self.w3 = w3
        self.balancer_pool_address = self.w3.to_checksum_address(balancer_pool_address)
        self.balancer_vault_address = self.w3.to_checksum_address(balancer_vault_address)
        self.batch_router_address = self.w3.to_checksum_address(batch_router_address)
        self.sdai_address = self.w3.to_checksum_address(sdai_address)
        self.wagno_address = self.w3.to_checksum_address(wagno_address)
        self.gno_to_wagno_rate = gno_to_wagno_rate
        self.verbose = verbose
        
        # Load the batch router ABI
        self.batch_router_abi = self.load_batch_router_abi()
        
    def load_batch_router_abi(self):
        """
        Load the Balancer batch router ABI.
        
        Returns:
            list: The batch router ABI
        """
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
                    batch_router_abi = json.load(f)
                    if self.verbose:
                        print(f"Loaded BatchRouter ABI from {path}")
                    return batch_router_abi
        
        # If we get here, we couldn't find the file
        raise FileNotFoundError(f"BatchRouter ABI file not found. Tried: {possible_paths}")
    
    def calculate_price_impact(self, gno_amount):
        """
        Calculate price impact for a fixed GNO amount in the Balancer pool.
        
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
            result = simulate_transaction_with_eth_call(
                self.w3,
                self.batch_router_address,
                self.batch_router_abi,
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
                buy_result = simulate_transaction_with_eth_call(
                    self.w3,
                    self.batch_router_address,
                    self.batch_router_abi,
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
                    buy_price_impact_percentage = None
                    effective_buy_price = None
                
                # Calculate price impact for selling waGNO for sDAI
                wagno_amount_wei = self.w3.to_wei(wagno_amount, 'ether')
                
                # Simulate the swap using eth_call
                sell_result = simulate_transaction_with_eth_call(
                    self.w3,
                    self.batch_router_address,
                    self.batch_router_abi,
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
                    
                    # Calculate effective price
                    effective_sell_price = sell_output / wagno_amount if wagno_amount != 0 else float('inf')
                    
                    # Calculate price impact
                    sell_price_impact_percentage = ((current_price_wagno_to_sdai / effective_sell_price) - 1) * 100
                    
                    print(f"\nSelling {wagno_amount} waGNO for sDAI:")
                    print(f"  Estimated sDAI received: {sell_output}")
                    print(f"  Effective price: 1 waGNO = {effective_sell_price} sDAI")
                    print(f"  Price impact: {sell_price_impact_percentage:.4f}%")
                else:
                    print(f"Error calculating sell price impact: simulation failed")
                    sell_price_impact_percentage = None
                    effective_sell_price = None
                
                return {
                    "pool": "Balancer sDAI/waGNO",
                    "gno_amount": gno_amount,
                    "wagno_amount": wagno_amount,
                    "current_price_sdai_to_wagno": current_price_sdai_to_wagno,
                    "current_price_wagno_to_sdai": current_price_wagno_to_sdai,
                    "buy_price_impact_percentage": buy_price_impact_percentage,
                    "effective_buy_price": effective_buy_price,
                    "sell_price_impact_percentage": sell_price_impact_percentage,
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