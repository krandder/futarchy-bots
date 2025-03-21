"""
Handler for GNO/waGNO operations in development.
Simplified version for wrapping and unwrapping GNO tokens.
"""

from web3 import Web3
from eth_account import Account

from futarchy.development.config.constants import GNO_ADDRESS, WAGNO_ADDRESS, ERC20_ABI, WAGNO_ABI
from futarchy.development.utils.web3_utils import get_raw_transaction

class GnoHandler:
    def __init__(self, w3: Web3, account: Account):
        """Initialize the GNO handler."""
        self.w3 = w3
        self.account = account
        self.address = account.address
        
        # Initialize token contracts
        self.gno_token = w3.eth.contract(address=GNO_ADDRESS, abi=ERC20_ABI)
        self.wagno_token = w3.eth.contract(address=WAGNO_ADDRESS, abi=WAGNO_ABI)
    
    def print_balances(self):
        """Print current GNO and waGNO balances."""
        gno_balance = self.gno_token.functions.balanceOf(self.address).call()
        wagno_balance = self.wagno_token.functions.balanceOf(self.address).call()
        
        print("\n=== Token Balances ===")
        print(f"GNO:   {self.w3.from_wei(gno_balance, 'ether')}")
        print(f"waGNO: {self.w3.from_wei(wagno_balance, 'ether')}")
    
    def wrap_gno_to_wagno(self, amount):
        """
        Wrap GNO to waGNO.
        
        Args:
            amount: Amount of GNO to wrap (in ether units)
            
        Returns:
            str: Transaction hash if successful, None otherwise
        """
        try:
            amount_wei = self.w3.to_wei(amount, 'ether')
            
            # Check GNO balance
            gno_balance = self.gno_token.functions.balanceOf(self.address).call()
            if gno_balance < amount_wei:
                print(f"❌ Insufficient GNO balance")
                print(f"   Required: {amount} GNO")
                print(f"   Available: {self.w3.from_wei(gno_balance, 'ether')} GNO")
                return None
            
            print(f"Wrapping {amount} GNO to waGNO...")
            
            # First approve waGNO contract to spend GNO
            print(f"📝 Approving waGNO contract to spend GNO...")
            approve_tx = self.gno_token.functions.approve(
                WAGNO_ADDRESS, amount_wei
            ).build_transaction({
                'from': self.address,
                'nonce': self.w3.eth.get_transaction_count(self.address),
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.w3.eth.chain_id,
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(approve_tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(get_raw_transaction(signed_tx))
            print(f"⏳ Approval transaction sent: {tx_hash.hex()}")
            
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt['status'] != 1:
                print("❌ Approval transaction failed!")
                return None
            print("✅ GNO approved successfully!")
            
            # Now deposit GNO to get waGNO
            deposit_tx = self.wagno_token.functions.deposit(
                amount_wei, self.address
            ).build_transaction({
                'from': self.address,
                'nonce': self.w3.eth.get_transaction_count(self.address),
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.w3.eth.chain_id,
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(deposit_tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(get_raw_transaction(signed_tx))
            
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt['status'] == 1:
                print(f"✅ Successfully wrapped {amount} GNO to waGNO!")
                return tx_hash.hex()
            else:
                print("❌ Wrapping transaction failed!")
                return None
                
        except Exception as e:
            print(f"❌ Error wrapping GNO to waGNO: {str(e)}")
            return None
    
    def unwrap_wagno_to_gno(self, amount):
        """
        Unwrap waGNO back to GNO.
        
        Args:
            amount: Amount of waGNO to unwrap (in ether units)
            
        Returns:
            str: Transaction hash if successful, None otherwise
        """
        try:
            amount_wei = self.w3.to_wei(amount, 'ether')
            
            # Check waGNO balance
            wagno_balance = self.wagno_token.functions.balanceOf(self.address).call()
            if wagno_balance < amount_wei:
                print(f"❌ Insufficient waGNO balance")
                print(f"   Required: {amount} waGNO")
                print(f"   Available: {self.w3.from_wei(wagno_balance, 'ether')} waGNO")
                return None
            
            print(f"Unwrapping {amount} waGNO to GNO...")
            
            # Redeem waGNO to get GNO back
            redeem_tx = self.wagno_token.functions.redeem(
                amount_wei,
                self.address,  # receiver
                self.address   # owner
            ).build_transaction({
                'from': self.address,
                'nonce': self.w3.eth.get_transaction_count(self.address),
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.w3.eth.chain_id,
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(redeem_tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(get_raw_transaction(signed_tx))
            
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt['status'] == 1:
                print(f"✅ Successfully unwrapped {amount} waGNO to GNO!")
                return tx_hash.hex()
            else:
                print("❌ Unwrapping transaction failed!")
                return None
                
        except Exception as e:
            print(f"❌ Error unwrapping waGNO to GNO: {str(e)}")
            return None 