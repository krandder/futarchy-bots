"""
Pool price checking module for Uniswap V3 pools.

This module is currently in EXPERIMENTAL status.
Requirements for promotion to DEVELOPMENT:
1. Complete test coverage
2. Documentation for all public functions
3. Error handling for all edge cases
"""

from typing import Tuple, Dict, Any
from web3.contract import Contract
from web3 import Web3

from futarchy.experimental.core.futarchy_bot import FutarchyBot
from futarchy.experimental.config.constants import CONTRACT_ADDRESSES, TOKEN_CONFIG

class PoolPriceChecker:
    """Class for checking and analyzing Uniswap V3 pool prices."""
    
    def __init__(self, bot: FutarchyBot):
        self.bot = bot
        self.pool_abi = [
            {'inputs': [], 'name': 'slot0', 'outputs': [
                {'internalType': 'uint160', 'name': 'sqrtPriceX96', 'type': 'uint160'},
                {'internalType': 'int24', 'name': 'tick', 'type': 'int24'},
                {'internalType': 'uint16', 'name': 'observationIndex', 'type': 'uint16'},
                {'internalType': 'uint16', 'name': 'observationCardinality', 'type': 'uint16'},
                {'internalType': 'uint16', 'name': 'observationCardinalityNext', 'type': 'uint16'},
                {'internalType': 'uint8', 'name': 'feeProtocol', 'type': 'uint8'},
                {'internalType': 'bool', 'name': 'unlocked', 'type': 'bool'}
            ], 'stateMutability': 'view', 'type': 'function'},
            {'inputs': [], 'name': 'token0', 'outputs': [{'internalType': 'address', 'name': '', 'type': 'address'}], 'stateMutability': 'view', 'type': 'function'},
            {'inputs': [], 'name': 'token1', 'outputs': [{'internalType': 'address', 'name': '', 'type': 'address'}], 'stateMutability': 'view', 'type': 'function'}
        ]
    
    def get_pool_contract(self, pool_address: str) -> Contract:
        """Get the pool contract instance."""
        return self.bot.w3.eth.contract(
            address=self.bot.w3.to_checksum_address(pool_address), 
            abi=self.pool_abi
        )
    
    def get_pool_data(self, pool_address: str) -> Dict[str, Any]:
        """
        Get detailed pool data including tokens and current price.
        
        Args:
            pool_address: Address of the Uniswap V3 pool
            
        Returns:
            Dict containing pool data including tokens, price, and tick
        """
        pool_contract = self.get_pool_contract(pool_address)
        
        # Get pool data
        token0 = pool_contract.functions.token0().call()
        token1 = pool_contract.functions.token1().call()
        slot0 = pool_contract.functions.slot0().call()
        sqrt_price_x96 = slot0[0]
        tick = slot0[1]
        
        # Calculate price
        price = (sqrt_price_x96 ** 2) / (2 ** 192)
        
        return {
            'pool_address': pool_address,
            'token0': token0,
            'token1': token1,
            'sqrt_price_x96': sqrt_price_x96,
            'tick': tick,
            'derived_price': price
        }
    
    def get_sdai_yes_pool_price(self) -> Dict[str, Any]:
        """
        Get the current price of the sDAI-YES/sDAI pool.
        
        Returns:
            Dict containing pool price information and token relationships
        """
        pool_address = CONTRACT_ADDRESSES['sdaiYesPool']
        pool_data = self.get_pool_data(pool_address)
        
        sdai_yes_address = TOKEN_CONFIG['currency']['yes_address'].lower()
        sdai_address = TOKEN_CONFIG['currency']['address'].lower()
        
        # Determine price relationship based on token ordering
        if pool_data['token0'].lower() == sdai_yes_address and pool_data['token1'].lower() == sdai_address:
            sdai_yes_price = 1/pool_data['derived_price']
        elif pool_data['token0'].lower() == sdai_address and pool_data['token1'].lower() == sdai_yes_address:
            sdai_yes_price = pool_data['derived_price']
        else:
            raise ValueError("Unexpected token ordering in pool")
            
        pool_data['sdai_yes_price'] = sdai_yes_price
        return pool_data

def main():
    """Main function for checking pool prices."""
    # Create bot instance
    bot = FutarchyBot()
    
    # Create price checker
    checker = PoolPriceChecker(bot)
    
    # Get and print pool data
    pool_data = checker.get_sdai_yes_pool_price()
    
    print(f'=== sDAI-YES/sDAI Pool Data ===')
    print(f'Pool address: {pool_data["pool_address"]}')
    print(f'Token0: {pool_data["token0"]}')
    print(f'Token1: {pool_data["token1"]}')
    print(f'Current sqrtPriceX96: {pool_data["sqrt_price_x96"]}')
    print(f'Current tick: {pool_data["tick"]}')
    print(f'Derived price: {pool_data["derived_price"]}')
    print(f'1 sDAI-YES = {pool_data["sdai_yes_price"]:.6f} sDAI')

if __name__ == '__main__':
    main() 