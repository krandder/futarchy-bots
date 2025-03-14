import os
import json
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
CONTRACT_ADDRESSES = {
    "baseCurrencyToken": "0xaf204776c7245bF4147c2612BF6e5972Ee483701",  # SDAI
    "baseCompanyToken": "0x9C58BAcC331c9aa871AFD802DB6379a98e80CEdb",  # GNO
    "currencyYesToken": "0x493A0D1c776f8797297Aa8B34594fBd0A7F8968a",
    "currencyNoToken": "0xE1133Ef862f3441880adADC2096AB67c63f6E102",
    "companyYesToken": "0x177304d505eCA60E1aE0dAF1bba4A4c4181dB8Ad",
    "companyNoToken": "0xf1B3E5Ffc0219A4F8C0ac69EC98C97709EdfB6c9",
    "wagno": "0x7c16f0185a26db0ae7a9377f23bc18ea7ce5d644",
}

# Simple ERC20 ABI for balanceOf
ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "payable": False, "stateMutability": "view", "type": "function"}
]

def main():
    # Connect to Gnosis Chain
    rpc_url = os.getenv("RPC_URL", "https://rpc.gnosischain.com")
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    # Check connection
    if not w3.is_connected():
        print("❌ Failed to connect to the blockchain")
        return
    
    print(f"✅ Connected to {rpc_url}")
    
    # Get account from private key if available
    private_key = os.getenv("PRIVATE_KEY")
    address = None
    
    if private_key:
        account = w3.eth.account.from_key(private_key)
        address = account.address
        print(f"📝 Using account: {address}")
    else:
        print("⚠️ No private key found in .env file")
        address = input("Enter your address to check balances: ")
    
    # Check native token balance
    native_balance = w3.eth.get_balance(address)
    print(f"\n💰 Native Token (xDAI): {w3.from_wei(native_balance, 'ether')}")
    
    # Check token balances
    print("\n=== Token Balances ===")
    
    for token_name, token_address in CONTRACT_ADDRESSES.items():
        try:
            token_contract = w3.eth.contract(address=w3.to_checksum_address(token_address), abi=ERC20_ABI)
            
            # Get token info
            try:
                symbol = token_contract.functions.symbol().call()
            except:
                symbol = token_name
                
            try:
                decimals = token_contract.functions.decimals().call()
            except:
                decimals = 18
                
            # Get balance
            balance = token_contract.functions.balanceOf(address).call()
            balance_formatted = balance / (10 ** decimals)
            
            print(f"{symbol}: {balance_formatted}")
        except Exception as e:
            print(f"Error getting balance for {token_name}: {e}")
    
    print("\n=== Pool Prices ===")
    # We could add price checks here if needed

if __name__ == "__main__":
    main() 