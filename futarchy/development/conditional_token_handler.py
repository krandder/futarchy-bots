"""
Conditional token handler for splitting and merging tokens.

This module is in DEVELOPMENT status.
Provides functionality for interacting with conditional tokens.
"""

from typing import List, Optional, Tuple
from web3 import Web3
from eth_typing import ChecksumAddress

from .config.abis.erc20 import ERC20_ABI
from .config.abis.conditional_token import CONDITIONAL_TOKEN_ABI
from .config.abis.futarchy_router import FUTARCHY_ROUTER_ABI
from .config.contracts import CONTRACTS
from .config.tokens import TOKEN_CONFIG

class ConditionalTokenHandler:
    """Handles operations related to conditional tokens like splitting and merging."""
    
    def __init__(self, web3: Web3):
        """Initialize the handler with Web3 instance and contract interfaces.
        
        Args:
            web3: Web3 instance connected to the appropriate network
        """
        self.web3 = web3
        self.conditional_token_contract = web3.eth.contract(
            address=CONTRACTS["CONDITIONAL_TOKEN"],
            abi=CONDITIONAL_TOKEN_ABI
        )
        self.futarchy_router = web3.eth.contract(
            address=CONTRACTS["FUTARCHY_ROUTER"],
            abi=FUTARCHY_ROUTER_ABI
        )
        
    def _get_token_contract(self, token_address: ChecksumAddress):
        """Get ERC20 contract interface for a token.
        
        Args:
            token_address: Address of the token contract
            
        Returns:
            Contract interface for the token
        """
        return self.web3.eth.contract(address=token_address, abi=ERC20_ABI)
        
    def _calculate_position_id(self, collateral_token: str, condition_id: str, outcome_index: int) -> str:
        """Calculate the position ID for a specific outcome.
        
        Args:
            collateral_token: The collateral token address
            condition_id: The condition ID
            outcome_index: The index of the outcome (0 for YES, 1 for NO)
            
        Returns:
            str: The position ID
        """
        try:
            # Convert inputs to bytes
            if isinstance(collateral_token, str) and collateral_token.startswith('0x'):
                collateral_token = bytes.fromhex(collateral_token[2:])
            if isinstance(condition_id, str) and condition_id.startswith('0x'):
                condition_id = bytes.fromhex(condition_id[2:])
            
            # Calculate the collection ID using keccak256(condition_id . indexSet)
            index_set = 1 << outcome_index  # 2^outcome_index
            collection_id = self.web3.keccak(
                condition_id + index_set.to_bytes(32, 'big')
            )
            
            # Calculate the position ID using keccak256(collateralToken . collectionId)
            position_id = self.web3.keccak(
                collateral_token + collection_id
            ).hex()
            
            return position_id
            
        except Exception as e:
            raise Exception(f"Error calculating position ID: {str(e)}")
        
    def split_tokens(
        self,
        token_symbol: str,
        amount: int,
        condition_id: str,
        partition: List[int],
        from_address: ChecksumAddress
    ) -> bool:
        """Split tokens into conditional tokens.
        
        Args:
            token_symbol: Symbol of the token to split (e.g. 'SDAI', 'GNO')
            amount: Amount of tokens to split in wei
            condition_id: ID of the condition to split on (not used with router)
            partition: List of partition numbers (not used with router)
            from_address: Address initiating the split
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get token config and contract
            token_config = TOKEN_CONFIG[token_symbol]
            token_contract = self._get_token_contract(token_config["address"])
            
            # Check allowance and approve if needed
            allowance = token_contract.functions.allowance(
                from_address,
                CONTRACTS["FUTARCHY_ROUTER"]
            ).call()
            
            if allowance < amount:
                approve_tx = token_contract.functions.approve(
                    CONTRACTS["FUTARCHY_ROUTER"],
                    amount
                ).build_transaction({
                    'from': from_address,
                    'gas': 200000,
                    'nonce': self.web3.eth.get_transaction_count(from_address)
                })
                # Return False since user needs to approve first
                return False, "Approval needed", approve_tx
                
            # Build split transaction using the router
            split_tx = self.futarchy_router.functions.splitPosition(
                CONTRACTS["MARKET"],  # market address
                token_config["address"],  # token address
                amount  # amount to split
            ).build_transaction({
                'from': from_address,
                'gas': 500000,
                'nonce': self.web3.eth.get_transaction_count(from_address)
            })
            
            return True, "Ready to split", split_tx
            
        except Exception as e:
            return False, f"Error in split_tokens: {str(e)}", None
            
    def merge_tokens(
        self,
        token_symbol: str,
        amount: int,
        condition_id: str,
        partition: List[int],
        from_address: ChecksumAddress
    ) -> bool:
        """Merge conditional tokens back into the original token.
        
        Args:
            token_symbol: Symbol of the token to merge (e.g. 'SDAI', 'GNO')
            amount: Amount of tokens to merge in wei
            condition_id: ID of the condition to merge on (not used with router)
            partition: List of partition numbers (not used with router)
            from_address: Address initiating the merge
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get token config
            token_config = TOKEN_CONFIG[token_symbol]
            
            # Get YES and NO token contracts
            yes_token = self._get_token_contract(token_config["yes_address"])
            no_token = self._get_token_contract(token_config["no_address"])
            
            # Check YES token allowance
            yes_allowance = yes_token.functions.allowance(
                from_address,
                CONTRACTS["FUTARCHY_ROUTER"]
            ).call()
            
            if yes_allowance < amount:
                approve_tx = yes_token.functions.approve(
                    CONTRACTS["FUTARCHY_ROUTER"],
                    amount
                ).build_transaction({
                    'from': from_address,
                    'gas': 200000,
                    'nonce': self.web3.eth.get_transaction_count(from_address)
                })
                return False, "YES token approval needed", approve_tx
            
            # Check NO token allowance
            no_allowance = no_token.functions.allowance(
                from_address,
                CONTRACTS["FUTARCHY_ROUTER"]
            ).call()
            
            if no_allowance < amount:
                approve_tx = no_token.functions.approve(
                    CONTRACTS["FUTARCHY_ROUTER"],
                    amount
                ).build_transaction({
                    'from': from_address,
                    'gas': 200000,
                    'nonce': self.web3.eth.get_transaction_count(from_address)
                })
                return False, "NO token approval needed", approve_tx
            
            # Build merge transaction using the router
            merge_tx = self.futarchy_router.functions.mergePositions(
                CONTRACTS["MARKET"],  # market address
                token_config["address"],  # token address
                amount  # amount to merge
            ).build_transaction({
                'from': from_address,
                'gas': 500000,
                'nonce': self.web3.eth.get_transaction_count(from_address)
            })
            
            return True, "Ready to merge", merge_tx
            
        except Exception as e:
            return False, f"Error in merge_tokens: {str(e)}", None
            
    def get_outcome_slot_count(self, condition_id: str) -> int:
        """Get the number of outcome slots for a condition.
        
        Args:
            condition_id: ID of the condition
            
        Returns:
            int: Number of outcome slots
        """
        try:
            return self.conditional_token_contract.functions.getOutcomeSlotCount(
                condition_id
            ).call()
        except Exception as e:
            raise Exception(f"Error getting outcome slot count: {str(e)}")
            
    def calculate_condition_id(
        self,
        oracle_address: ChecksumAddress,
        question_id: str,
        outcome_slot_count: int
    ) -> str:
        """Calculate the condition ID from its parameters.
        
        Args:
            oracle_address: Address of the oracle
            question_id: ID of the question (in hex format)
            outcome_slot_count: Number of possible outcomes
            
        Returns:
            str: The calculated condition ID
        """
        try:
            # Convert question_id to bytes if it's in hex format
            if isinstance(question_id, str) and question_id.startswith('0x'):
                question_id = bytes.fromhex(question_id[2:])
            
            # Pack parameters and calculate condition ID
            # The condition ID is the keccak256 hash of the packed oracle address, question ID, and outcome slot count
            packed_data = bytes.fromhex(oracle_address[2:].zfill(40)) + question_id + outcome_slot_count.to_bytes(32, 'big')
            condition_id = self.web3.keccak(packed_data).hex()
            
            return condition_id
            
        except Exception as e:
            raise Exception(f"Error calculating condition ID: {str(e)}") 