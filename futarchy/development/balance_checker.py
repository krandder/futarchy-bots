"""
Token Balance Checker for the Futarchy Trading Bot.

This module is in DEVELOPMENT status.
Provides functionality to check token balances for various tokens in the Futarchy system.

Example usage:
    # Simple usage with defaults
    from futarchy.development.balance_checker import get_balances
    balances = get_balances('0x123...')
    
    # Or use the class directly for more control
    from futarchy.development.balance_checker import TokenBalanceChecker
    checker = TokenBalanceChecker(w3, token_config, erc20_abi)
    balances = checker.get_balances('0x123...')
"""

import os
from typing import Optional, Dict, Any
from decimal import Decimal, ROUND_DOWN
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

from .config.abis.erc20 import ERC20_ABI
from .config.tokens import TOKEN_CONFIG

class TokenBalanceChecker:
    """Handles balance checking for various tokens in the Futarchy system."""
    
    def __init__(self, w3: Web3, token_config: dict = None, erc20_abi: list = None):
        """
        Initialize the balance checker.
        
        Args:
            w3: Web3 instance
            token_config: Dictionary containing token configurations (optional)
            erc20_abi: ABI for ERC20 token interface (optional)
        """
        self.w3 = w3
        self.token_config = token_config or TOKEN_CONFIG
        self.erc20_abi = erc20_abi or ERC20_ABI
        
        # Initialize token contracts
        self.token_contracts = {}
        for category in ['currency', 'company', 'wagno']:
            if category in self.token_config:
                # Main token
                address = self.token_config[category]['address']
                self.token_contracts[category] = self.w3.eth.contract(
                    address=self.w3.to_checksum_address(address),
                    abi=self.erc20_abi
                )
                
                # YES/NO tokens if they exist
                if 'yes_address' in self.token_config[category]:
                    yes_address = self.token_config[category]['yes_address']
                    self.token_contracts[f"{category}_yes"] = self.w3.eth.contract(
                        address=self.w3.to_checksum_address(yes_address),
                        abi=self.erc20_abi
                    )
                    
                if 'no_address' in self.token_config[category]:
                    no_address = self.token_config[category]['no_address']
                    self.token_contracts[f"{category}_no"] = self.w3.eth.contract(
                        address=self.w3.to_checksum_address(no_address),
                        abi=self.erc20_abi
                    )
    
    def get_balances(self, address: str = None) -> Dict[str, Dict[str, Any]]:
        """
        Get token balances for the specified address.
        
        Args:
            address: Address to check balances for (optional, uses account from .env if not provided)
            
        Returns:
            dict: Dictionary containing token balances
        """
        if not address:
            address = get_address_from_env()
            if not address:
                raise ValueError("No address provided and couldn't get one from environment")
        
        balances = {}
        for category in ['currency', 'company', 'wagno']:
            if category in self.token_config:
                config = self.token_config[category]
                contract = self.token_contracts[category]
                
                # Get main token balance
                balance = contract.functions.balanceOf(address).call()
                balances[category] = {
                    'balance': balance,
                    'formatted': format_token_amount(balance, config['address']),
                    'address': config['address']
                }
                
                # Get YES token balance if it exists
                if f"{category}_yes" in self.token_contracts:
                    yes_contract = self.token_contracts[f"{category}_yes"]
                    yes_balance = yes_contract.functions.balanceOf(address).call()
                    balances[category]['yes_balance'] = yes_balance
                    balances[category]['yes_formatted'] = format_token_amount(
                        yes_balance, config['yes_address']
                    )
                    balances[category]['yes_address'] = config['yes_address']
                
                # Get NO token balance if it exists
                if f"{category}_no" in self.token_contracts:
                    no_contract = self.token_contracts[f"{category}_no"]
                    no_balance = no_contract.functions.balanceOf(address).call()
                    balances[category]['no_balance'] = no_balance
                    balances[category]['no_formatted'] = format_token_amount(
                        no_balance, config['no_address']
                    )
                    balances[category]['no_address'] = config['no_address']
        
        return balances
    
    def print_balances(self, balances: dict = None, address: str = None):
        """
        Print token balances in a readable format.
        
        Args:
            balances: Dictionary of balances (optional, will fetch if not provided)
            address: Address to check balances for (optional)
        """
        if not balances:
            balances = self.get_balances(address)
        
        print("\n=== Token Balances ===")
        print("-" * 50)
        
        for category in ['currency', 'company', 'wagno']:
            if category in balances:
                token_data = balances[category]
                config = self.token_config[category]
                
                print(f"\n{config['name']}:")
                print(f"  Main Token: {token_data['formatted']}")
                
                if 'yes_balance' in token_data:
                    print(f"  YES Token: {token_data['yes_formatted']}")
                if 'no_balance' in token_data:
                    print(f"  NO Token: {token_data['no_formatted']}")

def format_token_amount(amount: int, token_address: str) -> str:
    """Format token amount with appropriate decimals."""
    decimals = TOKEN_CONFIG.get_decimals(token_address)
    if decimals is None:
        decimals = 18  # Default to 18 decimals
        
    amount_decimal = Decimal(amount) / Decimal(10 ** decimals)
    return f"{amount_decimal:.6f}"

def get_web3(rpc_url: str = None) -> Web3:
    """Get Web3 instance connected to Gnosis Chain."""
    if not rpc_url:
        rpc_url = os.getenv('GNOSIS_RPC_URL', 'https://rpc.gnosischain.com')
        
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    # Add PoA middleware for Gnosis Chain
    from web3.middleware import geth_poa_middleware
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    
    if not w3.is_connected():
        raise ConnectionError(f"Failed to connect to {rpc_url}")
        
    return w3

def get_address_from_env() -> Optional[str]:
    """Get address from private key in .env file."""
    load_dotenv()
    private_key = os.getenv('PRIVATE_KEY')
    if not private_key:
        return None
    
    account = Account.from_key(private_key)
    return account.address

def get_balances(address: str = None, rpc_url: str = None) -> Dict[str, Dict[str, Any]]:
    """
    Quick way to get token balances.
    
    Args:
        address: Address to check balances for (optional, uses account from .env if not provided)
        rpc_url: RPC URL to use (optional, uses environment or default)
        
    Returns:
        dict: Dictionary containing token balances
    """
    w3 = get_web3(rpc_url)
    checker = TokenBalanceChecker(w3)
    return checker.get_balances(address) 