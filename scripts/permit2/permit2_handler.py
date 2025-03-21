import os
import json
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_typed_data
from hexbytes import HexBytes
from dotenv import load_dotenv

class Permit2Handler:
    """Handler for Permit2 approvals required by Balancer V3"""
    
    # Permit2 contract address is the same across all chains
    PERMIT2_ADDRESS = "0x000000000022D473030F116dDEE9F6B43aC78BA3"
    
    # Constants from the SDK
    MAX_ALLOWANCE_TRANSFER_AMOUNT = 2 ** 160 - 1
    MAX_ALLOWANCE_EXPIRATION = 2 ** 48 - 1
    MAX_SIG_DEADLINE = 2 ** 256 - 1
    
    def __init__(self, w3, account, token_address=None, spender_address=None):
        """
        Initialize the Permit2 handler.
        
        Args:
            w3: Web3 instance
            account: Account instance
            token_address: Address of the token to approve
            spender_address: Address of the spender to approve
        """
        self.w3 = w3
        self.account = account
        self.address = account.address
        self.token_address = token_address
        self.spender_address = spender_address
        
        # Load Permit2 ABI
        with open('config/permit2_abi.json', 'r') as f:
            self.permit2_abi = json.load(f)
        
        # Initialize Permit2 contract
        self.permit2_contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(self.PERMIT2_ADDRESS),
            abi=self.permit2_abi
        )
    
    def get_nonce(self):
        """Get the current nonce for an owner"""
        return self.permit2_contract.functions.nonces(self.address).call()
    
    def get_domain_separator(self):
        """Get the domain separator for signing"""
        return self.permit2_contract.functions.DOMAIN_SEPARATOR().call()
    
    def sign_permit(self, token_address, spender_address, amount, deadline):
        """
        Sign a Permit2 authorization.
        
        Args:
            token_address: Address of the token to permit
            spender_address: Address of the spender to permit
            amount: Amount to permit (in wei)
            deadline: Timestamp when the permit expires
            
        Returns:
            tuple: (permit_data, signature)
        """
        # Get current nonce
        current_nonce = self.get_nonce()
        
        # Set expiration to 24 hours from now
        expiration_time = self.w3.eth.get_block('latest')['timestamp'] + 24 * 60 * 60
        
        # Prepare the typed data structure according to EIP-712 for Permit2
        typed_data = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"}
                ],
                "PermitDetails": [
                    {"name": "token", "type": "address"},
                    {"name": "amount", "type": "uint160"},
                    {"name": "expiration", "type": "uint48"},
                    {"name": "nonce", "type": "uint48"}
                ],
                "PermitSingle": [
                    {"name": "details", "type": "PermitDetails"},
                    {"name": "spender", "type": "address"},
                    {"name": "sigDeadline", "type": "uint256"}
                ]
            },
            "domain": {
                "name": "Permit2",
                "chainId": self.w3.eth.chain_id,
                "verifyingContract": self.PERMIT2_ADDRESS
            },
            "primaryType": "PermitSingle",
            "message": {
                "details": {
                    "token": token_address,
                    "amount": amount,
                    "expiration": expiration_time,
                    "nonce": current_nonce
                },
                "spender": spender_address,
                "sigDeadline": deadline
            }
        }
        
        # Sign the message
        encoded_message = encode_typed_data(full_message=typed_data)
        signed_message = self.account.sign_message(encoded_message)
        signature = signed_message.signature.hex()
        
        # Create permit data
        permit_single = (
            (token_address, amount, expiration_time, current_nonce),  # details
            spender_address,  # spender
            deadline  # sigDeadline
        )
        
        return permit_single, HexBytes(signature)
    
    def approve_token_with_permit2(self, token_address, spender, amount, deadline=None):
        """
        Approve a token using Permit2.
        
        Args:
            token_address: Address of the token to approve
            spender: Address to approve for spending
            amount: Amount to approve (in wei)
            deadline: Optional deadline timestamp (default: 30 days from now)
            
        Returns:
            dict: Transaction receipt
        """
        if deadline is None:
            # Default to 30 days from now
            deadline = self.w3.eth.get_block('latest')['timestamp'] + (30 * 24 * 60 * 60)
        
        try:
            # First, check if the token is already approved for Permit2
            token_contract = self.w3.eth.contract(
                address=self.w3.to_checksum_address(token_address),
                abi=[{
                    "inputs": [
                        {"name": "owner", "type": "address"},
                        {"name": "spender", "type": "address"}
                    ],
                    "name": "allowance",
                    "outputs": [{"name": "", "type": "uint256"}],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [
                        {"name": "spender", "type": "address"},
                        {"name": "amount", "type": "uint256"}
                    ],
                    "name": "approve",
                    "outputs": [{"name": "", "type": "bool"}],
                    "stateMutability": "nonpayable",
                    "type": "function"
                }]
            )
            
            permit2_allowance = token_contract.functions.allowance(
                self.address,
                self.PERMIT2_ADDRESS
            ).call()
            
            if permit2_allowance < amount:
                print("Token needs to be approved for Permit2 first")
                approve_tx = token_contract.functions.approve(
                    self.PERMIT2_ADDRESS,
                    2**256 - 1  # max uint256
                ).build_transaction({
                    'from': self.address,
                    'nonce': self.w3.eth.get_transaction_count(self.address),
                    'gas': 100000,
                    'maxFeePerGas': self.w3.eth.gas_price,
                    'maxPriorityFeePerGas': self.w3.eth.gas_price,
                    'chainId': self.w3.eth.chain_id,
                })
                
                signed_tx = self.w3.eth.account.sign_transaction(approve_tx, self.account.key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                
                if receipt['status'] != 1:
                    raise Exception("Failed to approve token for Permit2")
                print("✅ Token approved for Permit2")
            
            # Get permit data and signature
            permit_single, signature = self.sign_permit(
                token_address,
                spender,
                amount,
                deadline
            )
            
            # Build the permit transaction
            permit_tx = self.permit2_contract.functions.permit(
                self.address,
                permit_single,
                signature
            ).build_transaction({
                'from': self.address,
                'nonce': self.w3.eth.get_transaction_count(self.address),
                'gas': 200000,
                'maxFeePerGas': self.w3.eth.gas_price,
                'maxPriorityFeePerGas': self.w3.eth.gas_price,
                'chainId': self.w3.eth.chain_id,
            })
            
            # Sign and send the permit transaction
            signed_tx = self.w3.eth.account.sign_transaction(permit_tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt['status'] != 1:
                raise Exception("Permit2 approval failed")
            
            print("✅ Permit2 approval successful")
            return receipt
            
        except Exception as e:
            print(f"❌ Error in Permit2 approval: {str(e)}")
            return None

def main():
    """Test the Permit2 handler"""
    # Load environment variables
    load_dotenv()
    
    # Connect to Gnosis Chain
    rpc_url = os.getenv('GNOSIS_RPC_URL')
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not w3.is_connected():
        print("❌ Failed to connect to Gnosis Chain")
        return
    
    print(f"✅ Connected to Gnosis Chain (Chain ID: {w3.eth.chain_id})")
    
    # Load account
    private_key = os.getenv('PRIVATE_KEY')
    if not private_key:
        print("❌ No private key found in .env file")
        return
    
    account = Account.from_key(private_key)
    print(f"🔑 Using account: {account.address}")
    
    # Initialize Permit2 handler
    permit2 = Permit2Handler(w3, account)
    
    # Test token addresses
    sdai_address = "0xaf204776c7245bF4147c2612BF6e5972Ee483701"
    batch_router_address = "0xe2fa4e1d17725e72dcdafe943ecf45df4b9e285b"
    
    # Test approval
    amount = w3.to_wei(0.01, 'ether')  # 0.01 tokens
    receipt = permit2.approve_token_with_permit2(
        sdai_address,
        batch_router_address,
        amount
    )
    
    if receipt:
        print(f"Transaction hash: {receipt['transactionHash'].hex()}")
    
if __name__ == "__main__":
    main() 