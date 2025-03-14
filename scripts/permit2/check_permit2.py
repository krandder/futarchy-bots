from web3 import Web3
import json
import os

# Setup
RPC_URL = os.environ.get('GNOSIS_RPC_URL', 'https://gnosis-mainnet.public.blastapi.io')
w3 = Web3(Web3.HTTPProvider(RPC_URL))
private_key = os.environ.get('PRIVATE_KEY')

if not private_key:
    raise Exception("PRIVATE_KEY environment variable not set. Please set it before running this script.")

account = w3.eth.account.from_key(private_key)
user_address = account.address

# Token and contract addresses - configurable via environment variables
TOKEN_ADDRESS = os.environ.get('TOKEN_ADDRESS', '0xaf204776c7245bf4147c2612bf6e5972ee483701')  # Default to sDAI
PERMIT2_ADDRESS = os.environ.get('PERMIT2_ADDRESS', '0x000000000022D473030F116dDEE9F6B43aC78BA3')
SPENDER_ADDRESS = os.environ.get('SPENDER_ADDRESS', '0xe2fa4e1d17725e72dcdAfe943Ecf45dF4B9E285b')  # Default to BatchRouter

# Convert addresses to checksum format
token_address = Web3.to_checksum_address(TOKEN_ADDRESS)
permit2_address = Web3.to_checksum_address(PERMIT2_ADDRESS)
spender_address = Web3.to_checksum_address(SPENDER_ADDRESS)

# Token name for display
TOKEN_NAME = os.environ.get('TOKEN_NAME', 'sDAI')
SPENDER_NAME = os.environ.get('SPENDER_NAME', 'BatchRouter')

print(f"User address: {user_address}")
print(f"Checking {TOKEN_NAME} permissions for {SPENDER_NAME} via Permit2...")

# Check Step 1: Verify token allowance to Permit2
erc20_abi = [
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

token = w3.eth.contract(address=token_address, abi=erc20_abi)
permit2_allowance = token.functions.allowance(user_address, permit2_address).call()
print(f'✅ Step 1: {TOKEN_NAME} allowance for Permit2: {permit2_allowance}')
if permit2_allowance > 0:
    print(f"   Status: APPROVED - Permit2 can spend your {TOKEN_NAME}")
else:
    print(f"   Status: FAILED - Permit2 cannot spend your {TOKEN_NAME}")

# Check Step 2: Verify token balance
balance = token.functions.balanceOf(user_address).call()
print(f'✅ Step 2: {TOKEN_NAME} balance: {balance}')
if balance > 0:
    print(f"   Status: PASSED - You have {TOKEN_NAME} tokens")
else:
    print(f"   Status: FAILED - You don't have any {TOKEN_NAME} tokens")

# Check Step 3: Check Permit2 allowance for Spender using the correct function
permit2_abi = [
    {
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "token", "type": "address"},
            {"name": "spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [
            {"name": "amount", "type": "uint160"},
            {"name": "expiration", "type": "uint48"},
            {"name": "nonce", "type": "uint48"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

try:
    permit2 = w3.eth.contract(address=permit2_address, abi=permit2_abi)
    result = permit2.functions.allowance(user_address, token_address, spender_address).call()
    amount, expiration, nonce = result
    
    print(f'✅ Step 3: Permit2 allowance for {SPENDER_NAME}:')
    print(f'   Amount: {amount}')
    print(f'   Expiration: {expiration} (timestamp)')
    current_time = w3.eth.get_block('latest')['timestamp']
    if expiration > current_time:
        days_remaining = (expiration - current_time) // 86400
        print(f'   Status: VALID - Expires in {days_remaining} days')
    else:
        days_expired = (current_time - expiration) // 86400
        print(f'   Status: EXPIRED - Expired {days_expired} days ago')
    print(f'   Nonce: {nonce}')
    
    if amount > 0 and expiration > current_time:
        print(f"   Overall Status: APPROVED - {SPENDER_NAME} can spend your tokens through Permit2")
    else:
        print(f"   Overall Status: NOT APPROVED - {SPENDER_NAME} cannot spend your tokens through Permit2")
        
except Exception as e:
    print(f'❌ Step 3: Error checking Permit2 allowance: {e}')
    print("   Status: FAILED - Could not verify spender's permission through Permit2")

print("\nDIAGNOSIS:")
print("------------")
if permit2_allowance > 0 and balance > 0:
    print(f"Your {TOKEN_NAME} tokens are approved for Permit2 and you have a balance.")
    try:
        if amount > 0 and expiration > current_time:
            print(f"The {SPENDER_NAME} has permission to spend your tokens via Permit2.")
            print("The permit signature is working correctly!")
            print(f"\nRECOMMENDATION: If you're still having issues with {SPENDER_NAME},")
            print("the problem might be in the contract itself or in the swap parameters.")
        else:
            print(f"The {SPENDER_NAME} does NOT have permission to spend your tokens via Permit2.")
            print("\nRECOMMENDATION: Create a new permit signature by running:")
            print("python permit2_creator.py")
    except NameError:
        print(f"Could not verify {SPENDER_NAME}'s permission. Try creating a new permit.")
else:
    if permit2_allowance == 0:
        print(f"Your {TOKEN_NAME} tokens are NOT approved for Permit2.")
        print(f"\nRECOMMENDATION: Approve Permit2 to spend your {TOKEN_NAME} tokens first.")
        print("This requires a separate transaction to increase the ERC20 allowance.")
    if balance == 0:
        print(f"You don't have any {TOKEN_NAME} tokens.")
        print(f"\nRECOMMENDATION: Get some {TOKEN_NAME} tokens before attempting a swap.") 