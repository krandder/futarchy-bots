import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web3 import Web3
from web3.exceptions import ContractLogicError
from utils.web3_utils import setup_web3_connection, get_account_from_private_key, get_raw_transaction
from config.constants import CONTRACT_ADDRESSES, ERC20_ABI

class BaseBot:
    """Base bot with common functionality for blockchain interactions"""
    
    def __init__(self, rpc_url=None):
        """
        Initialize the base bot.
        
        Args:
            rpc_url: Optional RPC URL to connect to
        """
        # Set up Web3 connection
        self.w3 = setup_web3_connection(rpc_url)
        
        # Check connection
        self.check_connection()
        
        # Set up account
        self.account, self.address = get_account_from_private_key()
    
    def check_connection(self):
        """
        Check connection to the Gnosis Chain.
        
        Raises:
            ConnectionError: If connection fails
        """
        if self.w3.is_connected():
            chain_id = self.w3.eth.chain_id
            latest_block = self.w3.eth.block_number
            print(f"✅ Connected to Gnosis Chain (Chain ID: {chain_id})")
            print(f"📊 Latest block: {latest_block}")
        else:
            print("❌ Failed to connect to Gnosis Chain")
            raise ConnectionError("Failed to connect to Gnosis Chain")
    
    def approve_token(self, token_contract, spender_address, amount_wei=None):
        """
        Approve token spending.
        
        Args:
            token_contract: Token contract instance
            spender_address: Address to approve for spending
            amount_wei: Amount to approve in wei (or max uint256 if None)
            
        Returns:
            bool: Success or failure
        """
        if self.account is None:
            raise ValueError("No account configured for transactions")
        
        try:
            # Convert address to checksum format
            spender_address = self.w3.to_checksum_address(spender_address)
            
            # Get current allowance
            current_allowance = token_contract.functions.allowance(
                self.address, 
                spender_address
            ).call()
            
            # If already approved, return true
            if amount_wei and current_allowance >= amount_wei:
                print(f"✅ Token already approved for {spender_address}")
                return True
            
            # Use max approval if no specific amount
            if amount_wei is None:
                amount_wei = 2**256 - 1  # max uint256
                
            print(f"📝 Approving token for {spender_address}...")
            
            # Build transaction
            tx = token_contract.functions.approve(
                spender_address,
                amount_wei
            ).build_transaction({
                'from': self.address,
                'nonce': self.w3.eth.get_transaction_count(self.address),
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.w3.eth.chain_id,
            })
            
            # Sign transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(get_raw_transaction(signed_tx))
            
            print(f"⏳ Approval transaction sent: {tx_hash.hex()}")
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt['status'] == 1:
                print(f"✅ Token approved successfully!")
                return True
            else:
                print(f"❌ Token approval failed!")
                return False
                
        except Exception as e:
            print(f"❌ Error in token approval: {str(e)}")
            return False
    
    def get_token_contract(self, token_address):
        """
        Get an ERC20 token contract instance.
        
        Args:
            token_address: Token address
            
        Returns:
            Contract instance
        """
        return self.w3.eth.contract(
            address=self.w3.to_checksum_address(token_address),
            abi=ERC20_ABI
        )
    
    def check_token_balance(self, token_address, required_amount_wei, address=None):
        """
        Check if an address has enough token balance.
        
        Args:
            token_address: Token address
            required_amount_wei: Required amount in wei
            address: Address to check (defaults to self.address)
            
        Returns:
            tuple: (bool, balance_wei) indicating success and actual balance
        """
        if address is None:
            if self.address is None:
                raise ValueError("No address provided")
            address = self.address
            
        address = self.w3.to_checksum_address(address)
        token_address = self.w3.to_checksum_address(token_address)
        
        # Get token contract
        token_contract = self.get_token_contract(token_address)
        
        # Get balance
        balance_wei = token_contract.functions.balanceOf(address).call()
        
        # Check if balance is sufficient
        if balance_wei < required_amount_wei:
            return False, balance_wei
        
        return True, balance_wei
