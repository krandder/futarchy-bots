from config.constants import (
    CONTRACT_ADDRESSES,
    SUSHISWAP_V3_ROUTER_ABI,
    SUSHISWAP_V3_NFPM_ABI,
    UNISWAP_V3_POOL_ABI,
    ERC20_ABI
)
from utils.web3_utils import get_raw_transaction
import time
import math

class SushiSwapExchange:
    """Class for interacting with SushiSwap V3"""
    
    # Constants for price limits
    MIN_SQRT_RATIO = 4295128739  # Minimum value for sqrtPriceX96
    MAX_SQRT_RATIO = 1461446703485210103287273052203988822378723970342  # Maximum value for sqrtPriceX96
    
    def __init__(self, bot):
        """
        Initialize SushiSwap exchange handler.
        
        Args:
            bot: FutarchyBot instance with web3 connection and account
        """
        self.bot = bot
        self.w3 = bot.w3
        self.account = bot.account
        self.address = bot.address
        
        # Initialize SushiSwap router contract
        self.router = self.w3.eth.contract(
            address=self.w3.to_checksum_address(CONTRACT_ADDRESSES["sushiswap"]),
            abi=SUSHISWAP_V3_ROUTER_ABI
        )
        
        # Initialize SushiSwap NonFungiblePositionManager contract
        self.nfpm = self.w3.eth.contract(
            address=self.w3.to_checksum_address(CONTRACT_ADDRESSES["sushiswapNFPM"]),
            abi=SUSHISWAP_V3_NFPM_ABI
        )
    
    def swap(self, pool_address, token_in, token_out, amount, zero_for_one):
        """
        Execute a swap on SushiSwap V3.
        
        Args:
            pool_address: Address of the pool
            token_in: Address of token to sell
            token_out: Address of token to buy
            amount: Amount to swap in wei
            zero_for_one: Direction of swap (True if swapping token0 for token1)
            
        Returns:
            bool: Success or failure
        """
        if self.account is None:
            raise ValueError("No account configured for transactions")
        
        # Convert addresses to checksum format
        pool_address = self.w3.to_checksum_address(pool_address)
        token_in = self.w3.to_checksum_address(token_in)
        token_out = self.w3.to_checksum_address(token_out)
        sushiswap_address = self.w3.to_checksum_address(CONTRACT_ADDRESSES["sushiswap"])
        
        # Check current allowance and balance
        token_in_contract = self.bot.get_token_contract(token_in)
        current_allowance = token_in_contract.functions.allowance(
            self.address,
            sushiswap_address
        ).call()
        current_balance = token_in_contract.functions.balanceOf(self.address).call()
        
        print(f"Current allowance: {self.w3.from_wei(current_allowance, 'ether')}")
        print(f"Current balance: {self.w3.from_wei(current_balance, 'ether')}")
        print(f"Required amount: {self.w3.from_wei(amount, 'ether')}")
        
        # Reset allowance if it's too low
        if current_allowance < amount:
            print(f"Insufficient allowance. Approving {self.w3.from_wei(amount, 'ether')} tokens...")
            if not self.bot.approve_token(token_in_contract, sushiswap_address, amount):
                return False
        
        # Get current pool price
        pool_contract = self.w3.eth.contract(
            address=pool_address,
            abi=UNISWAP_V3_POOL_ABI
        )
        slot0 = pool_contract.functions.slot0().call()
        current_sqrt_price_x96 = slot0[0]
        
        # Calculate a more reasonable price limit (allow 50% price impact)
        if zero_for_one:
            # If selling token0 for token1, we want a lower limit
            sqrt_price_limit_x96 = int(current_sqrt_price_x96 * 0.5)  # Allow up to 50% worse price
            # Ensure we don't go below the minimum
            sqrt_price_limit_x96 = max(sqrt_price_limit_x96, self.MIN_SQRT_RATIO)
        else:
            # If selling token1 for token0, we want a higher limit
            sqrt_price_limit_x96 = int(current_sqrt_price_x96 * 2.0)  # Allow up to 50% worse price
            # Ensure we don't exceed the maximum
            sqrt_price_limit_x96 = min(sqrt_price_limit_x96, self.MAX_SQRT_RATIO)
        
        print(f"📝 Executing SushiSwap swap for {self.w3.from_wei(amount, 'ether')} tokens")
        print(f"Pool address: {pool_address}")
        print(f"Token In: {token_in}")
        print(f"Token Out: {token_out}")
        print(f"ZeroForOne: {zero_for_one}")
        print(f"Current sqrt price: {current_sqrt_price_x96}")
        print(f"Price limit: {sqrt_price_limit_x96}")
        
        try:
            # Build transaction for swap
            swap_tx = self.router.functions.swap(
                pool_address,  # pool address
                self.address,  # recipient
                zero_for_one,  # zeroForOne
                int(amount),  # amountSpecified
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
                print(f"✅ Swap executed successfully!")
                return True
            else:
                print(f"❌ Swap failed with receipt: {swap_receipt}")
                return False
        
        except Exception as e:
            print(f"❌ Error executing swap: {e}")
            return False
    
    def get_pool_info(self, pool_address):
        """
        Get information about a SushiSwap V3 pool.
        
        Args:
            pool_address: Address of the pool
            
        Returns:
            dict: Pool information including token0, token1, and current price
        """
        pool_contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(pool_address),
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
    
    def calculate_tick_range(self, current_tick, price_range_percentage):
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
    
    def add_liquidity(self, pool_address, token0_amount, token1_amount, price_range_percentage=10, slippage_percentage=0.5):
        """
        Add liquidity to a SushiSwap V3 pool with a concentrated position.
        
        Args:
            pool_address: Address of the pool
            token0_amount: Amount of token0 to add (in wei)
            token1_amount: Amount of token1 to add (in wei)
            price_range_percentage: Percentage range around current price (e.g., 10 for ±10%)
            slippage_percentage: Slippage tolerance percentage
            
        Returns:
            dict: Information about the created position or None if failed
        """
        if self.account is None:
            raise ValueError("No account configured for transactions")
        
        try:
            # Get pool information
            pool_info = self.get_pool_info(pool_address)
            token0 = pool_info['token0']
            token1 = pool_info['token1']
            current_tick = pool_info['tick']
            
            # Calculate tick range based on price range percentage
            tick_lower, tick_upper = self.calculate_tick_range(current_tick, price_range_percentage)
            
            print(f"📝 Adding liquidity to SushiSwap V3 pool")
            print(f"Pool address: {pool_address}")
            print(f"Token0: {token0}")
            print(f"Token1: {token1}")
            print(f"Amount0: {self.w3.from_wei(token0_amount, 'ether')}")
            print(f"Amount1: {self.w3.from_wei(token1_amount, 'ether')}")
            print(f"Current tick: {current_tick}")
            print(f"Tick range: {tick_lower} to {tick_upper}")
            
            # Calculate minimum amounts based on slippage
            slippage_factor = 1 - (slippage_percentage / 100)
            amount0_min = int(token0_amount * slippage_factor)
            amount1_min = int(token1_amount * slippage_factor)
            
            # Approve tokens for the NonFungiblePositionManager
            token0_contract = self.bot.get_token_contract(token0)
            token1_contract = self.bot.get_token_contract(token1)
            
            if not self.bot.approve_token(token0_contract, CONTRACT_ADDRESSES["sushiswapNFPM"], token0_amount):
                return None
            
            if not self.bot.approve_token(token1_contract, CONTRACT_ADDRESSES["sushiswapNFPM"], token1_amount):
                return None
            
            # Set deadline (30 minutes from now)
            deadline = int(time.time() + 1800)
            
            # Determine fee tier (0.3% is common, represented as 3000)
            fee = 3000
            
            # Build transaction for minting a new position
            mint_tx = self.nfpm.functions.mint(
                token0,  # token0
                token1,  # token1
                fee,  # fee
                tick_lower,  # tickLower
                tick_upper,  # tickUpper
                token0_amount,  # amount0Desired
                token1_amount,  # amount1Desired
                amount0_min,  # amount0Min
                amount1_min,  # amount1Min
                self.address,  # recipient
                deadline  # deadline
            ).build_transaction({
                'from': self.address,
                'nonce': self.w3.eth.get_transaction_count(self.address),
                'gas': 1000000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.w3.eth.chain_id,
                'value': 0  # No ETH sent with transaction
            })
            
            # Try to estimate gas to catch potential issues before sending
            try:
                estimated_gas = self.w3.eth.estimate_gas(mint_tx)
                print(f"Estimated gas for this transaction: {estimated_gas}")
                
                # If estimated gas is more than 80% of our limit, increase limit further
                if estimated_gas > 800000:
                    mint_tx['gas'] = int(estimated_gas * 1.25)  # Add 25% buffer
                    print(f"Increased gas limit to: {mint_tx['gas']}")
            except Exception as gas_error:
                print(f"⚠️ Gas estimation failed: {gas_error}")
                print(f"⚠️ This may indicate the transaction will fail, but proceeding anyway...")
            
            signed_mint_tx = self.w3.eth.account.sign_transaction(mint_tx, self.account.key)
            mint_tx_hash = self.w3.eth.send_raw_transaction(get_raw_transaction(signed_mint_tx))
            
            print(f"⏳ Mint transaction sent: {mint_tx_hash.hex()}")
            
            # Wait for confirmation
            mint_receipt = self.w3.eth.wait_for_transaction_receipt(mint_tx_hash)
            
            if mint_receipt['status'] == 1:
                print(f"✅ Liquidity added successfully!")
                
                # Parse the logs to get the token ID and other information
                logs = self.nfpm.events.Transfer().process_receipt(mint_receipt)
                if logs:
                    token_id = logs[0]['args']['tokenId']
                    print(f"Position NFT ID: {token_id}")
                    
                    # Get position details
                    position = self.nfpm.functions.positions(token_id).call()
                    
                    return {
                        'tokenId': token_id,
                        'token0': position[2],
                        'token1': position[3],
                        'fee': position[4],
                        'tickLower': position[5],
                        'tickUpper': position[6],
                        'liquidity': position[7]
                    }
                else:
                    print("⚠️ Could not find token ID in transaction logs")
                    return None
            else:
                print(f"❌ Adding liquidity failed with receipt: {mint_receipt}")
                return None
        
        except Exception as e:
            print(f"❌ Error adding liquidity: {e}")
            return None
    
    def increase_liquidity(self, token_id, token0_amount, token1_amount, slippage_percentage=0.5):
        """
        Increase liquidity in an existing position.
        
        Args:
            token_id: ID of the position NFT
            token0_amount: Amount of token0 to add (in wei)
            token1_amount: Amount of token1 to add (in wei)
            slippage_percentage: Slippage tolerance percentage
            
        Returns:
            bool: Success or failure
        """
        if self.account is None:
            raise ValueError("No account configured for transactions")
        
        try:
            # Get position information
            position = self.nfpm.functions.positions(token_id).call()
            token0 = position[2]
            token1 = position[3]
            
            print(f"📝 Increasing liquidity for position {token_id}")
            print(f"Token0: {token0}")
            print(f"Token1: {token1}")
            print(f"Amount0: {self.w3.from_wei(token0_amount, 'ether')}")
            print(f"Amount1: {self.w3.from_wei(token1_amount, 'ether')}")
            
            # Calculate minimum amounts based on slippage
            slippage_factor = 1 - (slippage_percentage / 100)
            amount0_min = int(token0_amount * slippage_factor)
            amount1_min = int(token1_amount * slippage_factor)
            
            # Approve tokens for the NonFungiblePositionManager
            token0_contract = self.bot.get_token_contract(token0)
            token1_contract = self.bot.get_token_contract(token1)
            
            if not self.bot.approve_token(token0_contract, CONTRACT_ADDRESSES["sushiswapNFPM"], token0_amount):
                return False
            
            if not self.bot.approve_token(token1_contract, CONTRACT_ADDRESSES["sushiswapNFPM"], token1_amount):
                return False
            
            # Set deadline (30 minutes from now)
            deadline = int(time.time() + 1800)
            
            # Build transaction for increasing liquidity
            increase_tx = self.nfpm.functions.increaseLiquidity(
                token_id,  # tokenId
                token0_amount,  # amount0Desired
                token1_amount,  # amount1Desired
                amount0_min,  # amount0Min
                amount1_min,  # amount1Min
                deadline  # deadline
            ).build_transaction({
                'from': self.address,
                'nonce': self.w3.eth.get_transaction_count(self.address),
                'gas': 500000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.w3.eth.chain_id,
                'value': 0  # No ETH sent with transaction
            })
            
            # Try to estimate gas to catch potential issues before sending
            try:
                estimated_gas = self.w3.eth.estimate_gas(increase_tx)
                print(f"Estimated gas for this transaction: {estimated_gas}")
                
                # If estimated gas is more than 80% of our limit, increase limit further
                if estimated_gas > 400000:
                    increase_tx['gas'] = int(estimated_gas * 1.25)  # Add 25% buffer
                    print(f"Increased gas limit to: {increase_tx['gas']}")
            except Exception as gas_error:
                print(f"⚠️ Gas estimation failed: {gas_error}")
                print(f"⚠️ This may indicate the transaction will fail, but proceeding anyway...")
            
            signed_increase_tx = self.w3.eth.account.sign_transaction(increase_tx, self.account.key)
            increase_tx_hash = self.w3.eth.send_raw_transaction(get_raw_transaction(signed_increase_tx))
            
            print(f"⏳ Increase liquidity transaction sent: {increase_tx_hash.hex()}")
            
            # Wait for confirmation
            increase_receipt = self.w3.eth.wait_for_transaction_receipt(increase_tx_hash)
            
            if increase_receipt['status'] == 1:
                print(f"✅ Liquidity increased successfully!")
                return True
            else:
                print(f"❌ Increasing liquidity failed with receipt: {increase_receipt}")
                return False
        
        except Exception as e:
            print(f"❌ Error increasing liquidity: {e}")
            return False
    
    def decrease_liquidity(self, token_id, liquidity_percentage, slippage_percentage=0.5):
        """
        Decrease liquidity in an existing position.
        
        Args:
            token_id: ID of the position NFT
            liquidity_percentage: Percentage of liquidity to remove (0-100)
            slippage_percentage: Slippage tolerance percentage
            
        Returns:
            dict: Amounts of token0 and token1 received, or None if failed
        """
        if self.account is None:
            raise ValueError("No account configured for transactions")
        
        try:
            # Get position information
            position = self.nfpm.functions.positions(token_id).call()
            token0 = position[2]
            token1 = position[3]
            current_liquidity = position[7]
            
            # Calculate liquidity to remove
            liquidity_to_remove = int(current_liquidity * (liquidity_percentage / 100))
            
            print(f"📝 Decreasing liquidity for position {token_id}")
            print(f"Token0: {token0}")
            print(f"Token1: {token1}")
            print(f"Current liquidity: {current_liquidity}")
            print(f"Liquidity to remove: {liquidity_to_remove} ({liquidity_percentage}%)")
            
            # Set minimum amounts to 0 initially (will be updated after simulation)
            amount0_min = 0
            amount1_min = 0
            
            # Try to simulate the transaction to get expected output amounts
            try:
                # Set deadline (30 minutes from now)
                deadline = int(time.time() + 1800)
                
                # Simulate decreaseLiquidity to get expected amounts
                simulated_amounts = self.nfpm.functions.decreaseLiquidity(
                    token_id,
                    liquidity_to_remove,
                    0,  # amount0Min
                    0,  # amount1Min
                    deadline
                ).call({'from': self.address})
                
                expected_amount0 = simulated_amounts[0]
                expected_amount1 = simulated_amounts[1]
                
                print(f"Expected amount0: {self.w3.from_wei(expected_amount0, 'ether')}")
                print(f"Expected amount1: {self.w3.from_wei(expected_amount1, 'ether')}")
                
                # Calculate minimum amounts based on slippage
                slippage_factor = 1 - (slippage_percentage / 100)
                amount0_min = int(expected_amount0 * slippage_factor)
                amount1_min = int(expected_amount1 * slippage_factor)
            except Exception as sim_error:
                print(f"⚠️ Simulation failed: {sim_error}")
                print(f"⚠️ Using default minimum amounts of 0")
            
            # Set deadline (30 minutes from now)
            deadline = int(time.time() + 1800)
            
            # Build transaction for decreasing liquidity
            decrease_tx = self.nfpm.functions.decreaseLiquidity(
                token_id,  # tokenId
                liquidity_to_remove,  # liquidity
                amount0_min,  # amount0Min
                amount1_min,  # amount1Min
                deadline  # deadline
            ).build_transaction({
                'from': self.address,
                'nonce': self.w3.eth.get_transaction_count(self.address),
                'gas': 500000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.w3.eth.chain_id,
                'value': 0  # No ETH sent with transaction
            })
            
            # Try to estimate gas to catch potential issues before sending
            try:
                estimated_gas = self.w3.eth.estimate_gas(decrease_tx)
                print(f"Estimated gas for this transaction: {estimated_gas}")
                
                # If estimated gas is more than 80% of our limit, increase limit further
                if estimated_gas > 400000:
                    decrease_tx['gas'] = int(estimated_gas * 1.25)  # Add 25% buffer
                    print(f"Increased gas limit to: {decrease_tx['gas']}")
            except Exception as gas_error:
                print(f"⚠️ Gas estimation failed: {gas_error}")
                print(f"⚠️ This may indicate the transaction will fail, but proceeding anyway...")
            
            signed_decrease_tx = self.w3.eth.account.sign_transaction(decrease_tx, self.account.key)
            decrease_tx_hash = self.w3.eth.send_raw_transaction(get_raw_transaction(signed_decrease_tx))
            
            print(f"⏳ Decrease liquidity transaction sent: {decrease_tx_hash.hex()}")
            
            # Wait for confirmation
            decrease_receipt = self.w3.eth.wait_for_transaction_receipt(decrease_tx_hash)
            
            if decrease_receipt['status'] == 1:
                print(f"✅ Liquidity decreased successfully!")
                
                # Note: Tokens are not automatically collected after decreasing liquidity
                # They need to be collected with a separate collect() call
                
                # Get updated position information
                updated_position = self.nfpm.functions.positions(token_id).call()
                tokens_owed0 = updated_position[10]
                tokens_owed1 = updated_position[11]
                
                return {
                    'tokenId': token_id,
                    'liquidityRemoved': liquidity_to_remove,
                    'tokensOwed0': tokens_owed0,
                    'tokensOwed1': tokens_owed1
                }
            else:
                print(f"❌ Decreasing liquidity failed with receipt: {decrease_receipt}")
                return None
        
        except Exception as e:
            print(f"❌ Error decreasing liquidity: {e}")
            return None
    
    def collect_fees(self, token_id):
        """
        Collect accumulated fees from a position.
        
        Args:
            token_id: ID of the position NFT
            
        Returns:
            dict: Amounts of token0 and token1 collected, or None if failed
        """
        if self.account is None:
            raise ValueError("No account configured for transactions")
        
        try:
            # Get position information
            position = self.nfpm.functions.positions(token_id).call()
            token0 = position[2]
            token1 = position[3]
            tokens_owed0 = position[10]
            tokens_owed1 = position[11]
            
            print(f"📝 Collecting fees for position {token_id}")
            print(f"Token0: {token0}")
            print(f"Token1: {token1}")
            print(f"Tokens owed0: {self.w3.from_wei(tokens_owed0, 'ether')}")
            print(f"Tokens owed1: {self.w3.from_wei(tokens_owed1, 'ether')}")
            
            # Build transaction for collecting fees
            # Use max uint128 to collect all available fees
            max_uint128 = 2**128 - 1
            
            collect_tx = self.nfpm.functions.collect(
                token_id,  # tokenId
                self.address,  # recipient
                max_uint128,  # amount0Max
                max_uint128  # amount1Max
            ).build_transaction({
                'from': self.address,
                'nonce': self.w3.eth.get_transaction_count(self.address),
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.w3.eth.chain_id,
                'value': 0  # No ETH sent with transaction
            })
            
            # Try to estimate gas to catch potential issues before sending
            try:
                estimated_gas = self.w3.eth.estimate_gas(collect_tx)
                print(f"Estimated gas for this transaction: {estimated_gas}")
                
                # If estimated gas is more than 80% of our limit, increase limit further
                if estimated_gas > 250000:
                    collect_tx['gas'] = int(estimated_gas * 1.25)  # Add 25% buffer
                    print(f"Increased gas limit to: {collect_tx['gas']}")
            except Exception as gas_error:
                print(f"⚠️ Gas estimation failed: {gas_error}")
                print(f"⚠️ This may indicate the transaction will fail, but proceeding anyway...")
            
            signed_collect_tx = self.w3.eth.account.sign_transaction(collect_tx, self.account.key)
            collect_tx_hash = self.w3.eth.send_raw_transaction(get_raw_transaction(signed_collect_tx))
            
            print(f"⏳ Collect fees transaction sent: {collect_tx_hash.hex()}")
            
            # Wait for confirmation
            collect_receipt = self.w3.eth.wait_for_transaction_receipt(collect_tx_hash)
            
            if collect_receipt['status'] == 1:
                print(f"✅ Fees collected successfully!")
                
                # Try to parse the logs to get the collected amounts
                try:
                    # Get the Collect event logs
                    logs = self.nfpm.events.Collect().process_receipt(collect_receipt)
                    if logs:
                        collected_amount0 = logs[0]['args']['amount0']
                        collected_amount1 = logs[0]['args']['amount1']
                        
                        print(f"Collected amount0: {self.w3.from_wei(collected_amount0, 'ether')}")
                        print(f"Collected amount1: {self.w3.from_wei(collected_amount1, 'ether')}")
                        
                        return {
                            'tokenId': token_id,
                            'amount0': collected_amount0,
                            'amount1': collected_amount1
                        }
                except Exception as log_error:
                    print(f"⚠️ Error parsing logs: {log_error}")
                
                # If we couldn't parse the logs, return a success with unknown amounts
                return {
                    'tokenId': token_id,
                    'amount0': tokens_owed0,  # This is an estimate
                    'amount1': tokens_owed1   # This is an estimate
                }
            else:
                print(f"❌ Collecting fees failed with receipt: {collect_receipt}")
                return None
        
        except Exception as e:
            print(f"❌ Error collecting fees: {e}")
            return None
    
    def get_position_info(self, token_id):
        """
        Get detailed information about a position.
        
        Args:
            token_id: ID of the position NFT
            
        Returns:
            dict: Position information
        """
        try:
            # Get position information
            position = self.nfpm.functions.positions(token_id).call()
            
            token0 = position[2]
            token1 = position[3]
            fee = position[4]
            tick_lower = position[5]
            tick_upper = position[6]
            liquidity = position[7]
            fee_growth_inside0_last_x128 = position[8]
            fee_growth_inside1_last_x128 = position[9]
            tokens_owed0 = position[10]
            tokens_owed1 = position[11]
            
            # Get token contracts to get symbols and decimals
            token0_contract = self.bot.get_token_contract(token0)
            token1_contract = self.bot.get_token_contract(token1)
            
            token0_symbol = token0_contract.functions.symbol().call()
            token1_symbol = token1_contract.functions.symbol().call()
            
            token0_decimals = token0_contract.functions.decimals().call()
            token1_decimals = token1_contract.functions.decimals().call()
            
            # Calculate price range
            price_lower = 1.0001 ** tick_lower
            price_upper = 1.0001 ** tick_upper
            
            return {
                'tokenId': token_id,
                'token0': {
                    'address': token0,
                    'symbol': token0_symbol,
                    'decimals': token0_decimals
                },
                'token1': {
                    'address': token1,
                    'symbol': token1_symbol,
                    'decimals': token1_decimals
                },
                'fee': fee,
                'tickLower': tick_lower,
                'tickUpper': tick_upper,
                'priceLower': price_lower,
                'priceUpper': price_upper,
                'liquidity': liquidity,
                'tokensOwed0': tokens_owed0,
                'tokensOwed1': tokens_owed1
            }
        
        except Exception as e:
            print(f"❌ Error getting position info: {e}")
            return None
