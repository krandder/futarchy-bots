"""
Module for calculating price impact in SushiSwap pools.
"""

from .config.constants import UNISWAP_V3_POOL_ABI, UNISWAP_V3_QUOTER_ABI, SUSHISWAP_QUOTER_ADDRESS

class SushiSwapPriceImpactCalculator:
    """Class to calculate price impact for SushiSwap pools."""
    
    def __init__(self, w3, yes_pool_address, no_pool_address, 
                 sdai_yes_address, sdai_no_address, 
                 gno_yes_address, gno_no_address, verbose=False):
        """
        Initialize the SushiSwap price impact calculator.
        
        Args:
            w3: Web3 instance
            yes_pool_address: Address of the YES pool
            no_pool_address: Address of the NO pool
            sdai_yes_address: Address of the sDAI YES token
            sdai_no_address: Address of the sDAI NO token
            gno_yes_address: Address of the GNO YES token
            gno_no_address: Address of the GNO NO token
            verbose: Whether to print verbose output
        """
        self.w3 = w3
        self.yes_pool_address = self.w3.to_checksum_address(yes_pool_address)
        self.no_pool_address = self.w3.to_checksum_address(no_pool_address)
        self.sdai_yes_address = self.w3.to_checksum_address(sdai_yes_address)
        self.sdai_no_address = self.w3.to_checksum_address(sdai_no_address)
        self.gno_yes_address = self.w3.to_checksum_address(gno_yes_address)
        self.gno_no_address = self.w3.to_checksum_address(gno_no_address)
        self.verbose = verbose
        
        # Initialize contracts
        self.init_contracts()
        
    def init_contracts(self):
        """Initialize contract instances."""
        # Initialize Uniswap V3 pool contracts for conditional tokens
        self.yes_pool = self.w3.eth.contract(
            address=self.yes_pool_address,
            abi=UNISWAP_V3_POOL_ABI
        )
        
        self.no_pool = self.w3.eth.contract(
            address=self.no_pool_address,
            abi=UNISWAP_V3_POOL_ABI
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
    
    def get_token_name(self, address):
        """
        Get a human-readable name for a token address.
        
        Args:
            address: Token address
            
        Returns:
            str: Human-readable token name
        """
        address_lower = address.lower()
        
        if address_lower == self.sdai_yes_address.lower():
            return "sDAI YES"
        elif address_lower == self.sdai_no_address.lower():
            return "sDAI NO"
        elif address_lower == self.gno_yes_address.lower():
            return "GNO YES"
        elif address_lower == self.gno_no_address.lower():
            return "GNO NO"
        else:
            return "Unknown"
    
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
    
    def calculate_price_impact(self, gno_amount, is_yes_pool):
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