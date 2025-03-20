from core.futarchy_bot import FutarchyBot
from config.constants import TOKEN_CONFIG
from web3 import Web3

# Complete ERC20 ABI with transfer function
COMPLETE_ERC20_ABI = [
    {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "payable": False, "stateMutability": "nonpayable", "type": "function"},
    {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": False, "inputs": [{"name": "_from", "type": "address"}, {"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transferFrom", "outputs": [{"name": "", "type": "bool"}], "payable": False, "stateMutability": "nonpayable", "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": False, "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "payable": False, "stateMutability": "nonpayable", "type": "function"},
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"payable": True, "stateMutability": "payable", "type": "fallback"},
    {"anonymous": False, "inputs": [{"indexed": True, "name": "owner", "type": "address"}, {"indexed": True, "name": "spender", "type": "address"}, {"indexed": False, "name": "value", "type": "uint256"}], "name": "Approval", "type": "event"},
    {"anonymous": False, "inputs": [{"indexed": True, "name": "from", "type": "address"}, {"indexed": True, "name": "to", "type": "address"}, {"indexed": False, "name": "value", "type": "uint256"}], "name": "Transfer", "type": "event"}
]

def transfer_sdai_no_tokens(recipient_address):
    """
    Transfer all sDAI-NO tokens to the specified address
    
    Args:
        recipient_address: Address to send tokens to
    """
    # Initialize bot
    bot = FutarchyBot()
    
    # Get current balances
    balances = bot.get_balances()
    sdai_no_balance = balances['currency']['no']
    
    # Convert to wei (full amount with all decimals)
    sdai_no_balance_wei = bot.w3.to_wei(sdai_no_balance, 'ether')
    
    print(f"\n🔄 Transferring {sdai_no_balance} sDAI-NO tokens to {recipient_address}")
    
    # Check if we have any tokens to transfer
    if float(sdai_no_balance) <= 0:
        print("❌ No sDAI-NO tokens available to transfer")
        return False
    
    # Get the token contract for sDAI-NO using standard ERC20 ABI
    sdai_no_address = TOKEN_CONFIG["currency"]["no_address"]
    sdai_no_token = bot.w3.eth.contract(
        address=bot.w3.to_checksum_address(sdai_no_address),
        abi=COMPLETE_ERC20_ABI
    )
    
    # Ensure the recipient address is checksum
    recipient = Web3.to_checksum_address(recipient_address)
    
    try:
        # Build the transaction
        tx = sdai_no_token.functions.transfer(
            recipient,
            sdai_no_balance_wei
        ).build_transaction({
            'from': bot.address,
            'nonce': bot.w3.eth.get_transaction_count(bot.address),
            'gas': 100000,  # Gas limit
            'gasPrice': bot.w3.eth.gas_price,
            'chainId': bot.w3.eth.chain_id,
        })
        
        # Sign and send the transaction
        signed_tx = bot.w3.eth.account.sign_transaction(tx, bot.account.key)
        tx_hash = bot.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        print(f"⏳ Transfer transaction sent: {tx_hash.hex()}")
        print(f"🔗 Explorer: https://gnosisscan.io/tx/{tx_hash.hex()}")
        
        # Wait for confirmation
        receipt = bot.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt['status'] == 1:
            print(f"✅ Transfer successful! {sdai_no_balance} sDAI-NO tokens sent to {recipient_address}")
            
            # Check new balance
            new_balances = bot.get_balances()
            new_sdai_no_balance = new_balances['currency']['no']
            print(f"New sDAI-NO balance: {new_sdai_no_balance}")
            
            return True
        else:
            print("❌ Transfer failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error transferring tokens: {e}")
        return False

if __name__ == "__main__":
    # The address to send the tokens to
    recipient_address = "0xac48BA60B0F8A967E237A026d524a656e2c9631D"
    
    # Execute the transfer
    transfer_sdai_no_tokens(recipient_address) 