"""
Conditional Token Operations for the Futarchy Trading Bot.

This module is in DEVELOPMENT status.
Provides functionality for splitting tokens into conditional YES/NO pairs and merging them back.

Example usage:
    # Initialize the handler
    handler = ConditionalTokenHandler(w3, account)
    
    # Split sDAI into YES/NO tokens
    success = handler.split_token_to_conditional_pair('currency', 100.0)  # 100.0 sDAI
    
    # Split GNO into YES/NO tokens
    success = handler.split_token_to_conditional_pair('company', 1.0)  # 1.0 GNO
    
    # Merge sDAI YES/NO back to sDAI
    success = handler.merge_conditional_pair_to_token('currency', 50.0)  # 50.0 sDAI
    
    # Merge GNO YES/NO back to GNO
    success = handler.merge_conditional_pair_to_token('company', 0.5)  # 0.5 GNO
"""

from typing import Optional, Dict, Any, Tuple
from decimal import Decimal
from web3 import Web3
from eth_account.signers.local import LocalAccount

from futarchy.development.config.abis.erc20 import ERC20_ABI
from futarchy.development.config.tokens import TOKEN_CONFIG
from futarchy.development.config.contracts import CONTRACT_ADDRESSES

class ConditionalTokenHandler:
    """Handles operations for conditional tokens in the Futarchy system."""
    
    def __init__(self, w3: Web3, account: LocalAccount, verbose: bool = False):
        """
        Initialize the conditional token handler.
        
        Args:
            w3: Web3 instance
            account: Account to use for transactions
            verbose: Whether to print detailed information
        """
        self.w3 = w3
        self.account = account
        self.address = account.address
        self.verbose = verbose
        
        # Initialize contracts
        self.futarchy_router = self.w3.eth.contract(
            address=self.w3.to_checksum_address(CONTRACT_ADDRESSES["futarchyRouter"]),
            abi=ERC20_ABI  # This should be updated to use the correct router ABI
        )
        
        # Initialize token contracts
        self.token_contracts = {}
        for token_type in ['currency', 'company']:
            config = TOKEN_CONFIG[token_type]
            # Base token
            self.token_contracts[f"{token_type}_base"] = self._get_token_contract(config['address'])
            # YES token
            self.token_contracts[f"{token_type}_yes"] = self._get_token_contract(config['yes_address'])
            # NO token
            self.token_contracts[f"{token_type}_no"] = self._get_token_contract(config['no_address'])
    
    def _get_token_contract(self, address: str):
        """Create a contract instance for the given token address."""
        return self.w3.eth.contract(
            address=self.w3.to_checksum_address(address),
            abi=ERC20_ABI
        )
    
    def _check_token_balance(self, token_address: str, amount_wei: int) -> Tuple[bool, int]:
        """
        Check if there's sufficient token balance.
        
        Args:
            token_address: Token address to check
            amount_wei: Amount in wei to check for
            
        Returns:
            Tuple[bool, int]: (has_sufficient_balance, actual_balance)
        """
        token = self._get_token_contract(token_address)
        balance = token.functions.balanceOf(self.address).call()
        return balance >= amount_wei, balance
    
    def _approve_token(self, token_contract, spender: str, amount: int) -> bool:
        """
        Approve token spending.
        
        Args:
            token_contract: Token contract instance
            spender: Address to approve
            amount: Amount to approve in wei
            
        Returns:
            bool: Success or failure
        """
        try:
            # Build approval transaction
            tx = token_contract.functions.approve(spender, amount).build_transaction({
                'from': self.address,
                'nonce': self.w3.eth.get_transaction_count(self.address),
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.w3.eth.chain_id,
            })
            
            # Sign and send transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            return receipt['status'] == 1
            
        except Exception as e:
            print(f"❌ Error approving token: {e}")
            return False
    
    def split_token_to_conditional_pair(self, token_type: str, amount: float) -> bool:
        """
        Split a token into its conditional YES/NO pair.
        
        Args:
            token_type: Token type ('currency' for sDAI or 'company' for GNO)
            amount: Amount to split
            
        Returns:
            bool: Success or failure
            
        Example:
            # Split 100 sDAI into YES/NO tokens
            success = handler.split_token_to_conditional_pair('currency', 100.0)
            
            # Split 1 GNO into YES/NO tokens
            success = handler.split_token_to_conditional_pair('company', 1.0)
        """
        if token_type not in ['currency', 'company']:
            raise ValueError(f"Invalid token type: {token_type}")
        
        # Get token configuration
        config = TOKEN_CONFIG[token_type]
        token_name = config['name']
        base_token = self.token_contracts[f"{token_type}_base"]
        
        # Convert amount to wei
        amount_wei = self.w3.to_wei(amount, 'ether')
        
        # Check balance
        has_balance, actual_balance = self._check_token_balance(config['address'], amount_wei)
        if not has_balance:
            print(f"❌ Insufficient {token_name} balance")
            print(f"   Required: {amount} {token_name}")
            print(f"   Available: {self.w3.from_wei(actual_balance, 'ether')} {token_name}")
            return False
        
        # Approve router if needed
        allowance = base_token.functions.allowance(self.address, CONTRACT_ADDRESSES["futarchyRouter"]).call()
        if allowance < amount_wei:
            if not self._approve_token(base_token, CONTRACT_ADDRESSES["futarchyRouter"], amount_wei):
                return False
        
        try:
            # Build split transaction
            tx = self.futarchy_router.functions.splitPosition(
                self.w3.to_checksum_address(CONTRACT_ADDRESSES["market"]),
                self.w3.to_checksum_address(config['address']),
                amount_wei
            ).build_transaction({
                'from': self.address,
                'nonce': self.w3.eth.get_transaction_count(self.address),
                'gas': 500000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.w3.eth.chain_id,
            })
            
            # Sign and send transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt['status'] == 1:
                # Get new balances
                yes_balance = self.token_contracts[f"{token_type}_yes"].functions.balanceOf(self.address).call()
                no_balance = self.token_contracts[f"{token_type}_no"].functions.balanceOf(self.address).call()
                
                print(f"✅ Successfully split {amount} {token_name} into conditional tokens!")
                print(f"New balances:")
                print(f"{token_name} YES: {self.w3.from_wei(yes_balance, 'ether')}")
                print(f"{token_name} NO: {self.w3.from_wei(no_balance, 'ether')}")
                return True
            else:
                print(f"❌ Split transaction failed!")
                return False
                
        except Exception as e:
            print(f"❌ Error splitting {token_name}: {e}")
            return False
    
    def merge_conditional_pair_to_token(self, token_type: str, amount: float) -> bool:
        """
        Merge conditional YES/NO tokens back into the base token.
        
        Args:
            token_type: Token type ('currency' for sDAI or 'company' for GNO)
            amount: Amount to merge
            
        Returns:
            bool: Success or failure
            
        Example:
            # Merge 50 sDAI YES/NO back to sDAI
            success = handler.merge_conditional_pair_to_token('currency', 50.0)
            
            # Merge 0.5 GNO YES/NO back to GNO
            success = handler.merge_conditional_pair_to_token('company', 0.5)
        """
        if token_type not in ['currency', 'company']:
            raise ValueError(f"Invalid token type: {token_type}")
        
        # Get token configuration
        config = TOKEN_CONFIG[token_type]
        token_name = config['name']
        
        # Convert amount to wei
        amount_wei = self.w3.to_wei(amount, 'ether')
        
        # Check YES/NO token balances
        yes_balance = self.token_contracts[f"{token_type}_yes"].functions.balanceOf(self.address).call()
        no_balance = self.token_contracts[f"{token_type}_no"].functions.balanceOf(self.address).call()
        
        if yes_balance < amount_wei or no_balance < amount_wei:
            print(f"❌ Insufficient YES/NO token balance for merge")
            print(f"   Required: {amount} each")
            print(f"   Available: YES={self.w3.from_wei(yes_balance, 'ether')}, NO={self.w3.from_wei(no_balance, 'ether')}")
            return False
        
        # Approve YES and NO tokens if needed
        for token_suffix in ['yes', 'no']:
            token = self.token_contracts[f"{token_type}_{token_suffix}"]
            allowance = token.functions.allowance(self.address, CONTRACT_ADDRESSES["futarchyRouter"]).call()
            if allowance < amount_wei:
                if not self._approve_token(token, CONTRACT_ADDRESSES["futarchyRouter"], amount_wei):
                    return False
        
        try:
            # Build merge transaction
            tx = self.futarchy_router.functions.mergePosition(
                self.w3.to_checksum_address(CONTRACT_ADDRESSES["market"]),
                self.w3.to_checksum_address(config['address']),
                amount_wei
            ).build_transaction({
                'from': self.address,
                'nonce': self.w3.eth.get_transaction_count(self.address),
                'gas': 500000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.w3.eth.chain_id,
            })
            
            # Sign and send transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt['status'] == 1:
                # Get new balances
                base_balance = self.token_contracts[f"{token_type}_base"].functions.balanceOf(self.address).call()
                yes_balance = self.token_contracts[f"{token_type}_yes"].functions.balanceOf(self.address).call()
                no_balance = self.token_contracts[f"{token_type}_no"].functions.balanceOf(self.address).call()
                
                print(f"✅ Successfully merged {amount} {token_name} YES/NO tokens!")
                print(f"New balances:")
                print(f"{token_name}: {self.w3.from_wei(base_balance, 'ether')}")
                print(f"{token_name} YES: {self.w3.from_wei(yes_balance, 'ether')}")
                print(f"{token_name} NO: {self.w3.from_wei(no_balance, 'ether')}")
                return True
            else:
                print(f"❌ Merge transaction failed!")
                return False
                
        except Exception as e:
            print(f"❌ Error merging {token_name} YES/NO tokens: {e}")
            return False 