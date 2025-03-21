#!/bin/bash

# Comprehensive test script for the Futarchy system
# Runs all available test scripts in sequence

echo "==================================="
echo "Running all Futarchy system tests"
echo "==================================="

# Current directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Test 1: Balance checking
echo -e "\n\n=== Testing Balance Checking ==="
# Create a simplified balance checking script that shows full precision
cat > /tmp/check_balances.py << 'EOL'
import sys
sys.path.append('/Users/kas/futarchy-bots')
import os
from dotenv import load_dotenv
from web3 import Web3
from eth_account import Account
from decimal import Decimal, getcontext

# Set high precision for decimal calculations
getcontext().prec = 78  # Maximum precision for Decimal

from futarchy.development.config.constants import GNO_ADDRESS, WAGNO_ADDRESS, ERC20_ABI
from futarchy.development.config.tokens import TOKEN_CONFIG

# Load environment variables
load_dotenv()
address = os.getenv('ADDRESS') or os.getenv('WALLET_ADDRESS')

# If no address in environment, try to get it from private key
if not address:
    private_key = os.getenv('PRIVATE_KEY')
    if private_key:
        account = Account.from_key(private_key)
        address = account.address

if not address:
    print("❌ No address found in environment variables")
    sys.exit(1)

# Setup web3
web3 = Web3(Web3.HTTPProvider(os.getenv('RPC_URL', 'https://rpc.gnosischain.com')))
from web3.middleware import geth_poa_middleware
web3.middleware_onion.inject(geth_poa_middleware, layer=0)

print(f"Checking balances for {address}")

try:
    # Create token contracts
    tokens = {}
    
    # Add GNO and waGNO
    gno_contract = web3.eth.contract(address=GNO_ADDRESS, abi=ERC20_ABI)
    wagno_contract = web3.eth.contract(address=WAGNO_ADDRESS, abi=ERC20_ABI)
    
    # Get GNO and waGNO balances
    gno_balance = gno_contract.functions.balanceOf(address).call()
    wagno_balance = wagno_contract.functions.balanceOf(address).call()
    
    # Function to format amount with full precision
    def format_amount_full_precision(amount_wei, decimals=18):
        if amount_wei == 0:
            return "0"
        amount_decimal = Decimal(amount_wei) / Decimal(10 ** decimals)
        # Convert to string to avoid scientific notation
        return str(amount_decimal)
    
    # Check currency and company tokens from TOKEN_CONFIG
    print("\n✅ Balances retrieved successfully (full precision):")
    
    print("\nGNO:")
    print(f"  Main Token: {format_amount_full_precision(gno_balance)}")
    
    print("\nwaGNO:")
    print(f"  Main Token: {format_amount_full_precision(wagno_balance)}")
    
    # Check conditional tokens
    for token_type, config in TOKEN_CONFIG.items():
        if token_type in ["currency", "company"]:
            token_name = "sDAI" if token_type == "currency" else "GNO"
            decimals = config.get("decimals", 18)
            
            # Create contracts
            token_contract = web3.eth.contract(address=config["address"], abi=ERC20_ABI)
            
            # Get balances
            token_balance = token_contract.functions.balanceOf(address).call()
            yes_balance = 0
            no_balance = 0
            
            if "yes_address" in config:
                yes_contract = web3.eth.contract(address=config["yes_address"], abi=ERC20_ABI)
                yes_balance = yes_contract.functions.balanceOf(address).call()
            
            if "no_address" in config:
                no_contract = web3.eth.contract(address=config["no_address"], abi=ERC20_ABI)
                no_balance = no_contract.functions.balanceOf(address).call()
            
            print(f"\n{token_name}:")
            print(f"  Main Token: {format_amount_full_precision(token_balance, decimals)}")
            print(f"  YES Token: {format_amount_full_precision(yes_balance, decimals)}")
            print(f"  NO Token: {format_amount_full_precision(no_balance, decimals)}")

except Exception as e:
    print(f"❌ Error retrieving balances: {str(e)}")
    import traceback
    traceback.print_exc()
EOL

# Run the balance checking script
python /tmp/check_balances.py

# Test 2: GNO wrapping
echo -e "\n\n=== Testing GNO Wrapping ==="
python wrap_gno_test.py

# Test 3: GNO unwrapping
echo -e "\n\n=== Testing GNO Unwrapping ==="
python unwrap_wagno_test.py

# Test 4: Split GNO into YES/NO tokens
echo -e "\n\n=== Testing GNO Splitting ==="
python ../../scripts/split_merge_test.py split gno --amount 0.0025

# Test 5: Merge GNO YES/NO tokens back to GNO
echo -e "\n\n=== Testing GNO Merging ==="
python ../../scripts/split_merge_test.py merge gno --amount 0.0025

# Test 6: Split sDAI into YES/NO tokens
echo -e "\n\n=== Testing sDAI Splitting ==="
python ../../scripts/split_merge_test.py split sdai --amount 0.01

# Test 7: Merge sDAI YES/NO tokens back to sDAI
echo -e "\n\n=== Testing sDAI Merging ==="
python ../../scripts/split_merge_test.py merge sdai --amount 0.01

echo -e "\n==================================="
echo "All tests completed"
echo "=====================================" 