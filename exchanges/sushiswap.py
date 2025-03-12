from ..config.constants import SUSHISWAP_V3_ROUTER_ABI, CONTRACT_ADDRESSES, MIN_SQRT_RATIO, MAX_SQRT_RATIO
from ..utils.web3_utils import get_raw_transaction

class SushiSwapExchange:
    """Class for interacting with SushiSwap V3"""
    
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
        
        # Approve token for SushiSwap
        token_in_contract = self.bot.get_token_contract(token_in)
        if not self.bot.approve_token(token_in_contract, CONTRACT_ADDRESSES["sushiswap"], amount):
            return False
        
        # Set price limit based on swap direction
        sqrt_price_limit_x96 = MIN_SQRT_RATIO if zero_for_one else MAX_SQRT_RATIO
        
        print(f"📝 Executing SushiSwap swap for {self.w3.from_wei(amount, 'ether')} tokens")
        print(f"Pool address: {pool_address}")
        print(f"Token In: {token_in}")
        print(f"Token Out: {token_out}")
        print(f"ZeroForOne: {zero_for_one}")
        
        try:
            # Build transaction for swap
            swap_tx = self.router.functions.swap(
                self.w3.to_checksum_address(pool_address),  # pool address
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
