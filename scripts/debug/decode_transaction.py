import json
from web3 import Web3
from hexbytes import HexBytes

# Transaction input data from Tenderly
tx_input = "0x2d737113000000000000000000000000177304d505eca60e1ae0daf1bba4a4c4181db8ad000000000000000000000000493a0d1c776f8797297aa8b34594fbd0a7f8968a0000000000000000000000000000000000000000000000000000000000000064000000000000000000000000000000000000000000000000000000000000c2ed000000000000000000000000000000000000000000000000000000000000cdd9000000000000000000000000000000000000000000000000002386f26fc1000000000000000000000000000000000000000000000000000017979cfe362a000000000000000000000000000000000000000000000000000000235978e783e00000000000000000000000000000000000000000000000000017796a49bd92c000000000000000000000000000ac48ba60b0f8a967e237a026d524a656e2c9631d0000000000000000000000000000000000000000000000000000000067d3f031"

# Function signature (first 4 bytes of the keccak256 hash of the function signature)
function_signature = tx_input[:10]
print(f"Function Signature: {function_signature}")

# The rest of the data is the encoded parameters
encoded_params = tx_input[10:]

# Connect to a node (can be any node, we just need it for decoding)
w3 = Web3(Web3.HTTPProvider("https://rpc.gnosischain.com"))

# Define the ABI for the mint function
mint_abi = {
    "inputs": [
        {"internalType": "address", "name": "token0", "type": "address"},
        {"internalType": "address", "name": "token1", "type": "address"},
        {"internalType": "uint24", "name": "fee", "type": "uint24"},
        {"internalType": "int24", "name": "tickLower", "type": "int24"},
        {"internalType": "int24", "name": "tickUpper", "type": "int24"},
        {"internalType": "uint256", "name": "amount0Desired", "type": "uint256"},
        {"internalType": "uint256", "name": "amount1Desired", "type": "uint256"},
        {"internalType": "uint256", "name": "amount0Min", "type": "uint256"},
        {"internalType": "uint256", "name": "amount1Min", "type": "uint256"},
        {"internalType": "address", "name": "recipient", "type": "address"},
        {"internalType": "uint256", "name": "deadline", "type": "uint256"}
    ],
    "name": "mint",
    "outputs": [
        {"internalType": "uint256", "name": "tokenId", "type": "uint256"},
        {"internalType": "uint128", "name": "liquidity", "type": "uint128"},
        {"internalType": "uint256", "name": "amount0", "type": "uint256"},
        {"internalType": "uint256", "name": "amount1", "type": "uint256"}
    ],
    "stateMutability": "payable",
    "type": "function"
}

# Try to decode the parameters
try:
    # Create a contract object with just the mint function
    contract = w3.eth.contract(abi=[mint_abi])
    
    # Decode the function call
    func_obj, func_params = contract.decode_function_input(tx_input)
    
    print("\nDecoded Parameters:")
    for key, value in func_params.items():
        print(f"{key}: {value}")
    
    # Additional analysis
    print("\nAnalysis:")
    print(f"Token0: {func_params['token0']}")
    print(f"Token1: {func_params['token1']}")
    print(f"Fee: {func_params['fee']}")
    print(f"Tick Lower: {func_params['tickLower']}")
    print(f"Tick Upper: {func_params['tickUpper']}")
    print(f"Amount0 Desired: {func_params['amount0Desired']} ({Web3.from_wei(func_params['amount0Desired'], 'ether')} ether)")
    print(f"Amount1 Desired: {func_params['amount1Desired']} ({Web3.from_wei(func_params['amount1Desired'], 'ether')} ether)")
    
    # Check if tickLower < tickUpper
    if func_params['tickLower'] >= func_params['tickUpper']:
        print("\nERROR: tickLower must be less than tickUpper")
    
    # Check if the current tick is within the range
    print(f"\nCurrent tick from our debug script: 51299")
    if func_params['tickLower'] <= 51299 <= func_params['tickUpper']:
        print("Current tick is within the specified range")
    else:
        print("WARNING: Current tick is NOT within the specified range")
    
except Exception as e:
    print(f"Error decoding parameters: {e}")
    
    # Manual decoding as fallback
    print("\nManually parsing the input data:")
    
    # Extract parameters from the encoded data
    # Each parameter is 32 bytes (64 hex characters) except for the function signature
    
    # Addresses are 20 bytes but padded to 32 bytes
    token0 = "0x" + encoded_params[0:64][-40:]
    token1 = "0x" + encoded_params[64:128][-40:]
    
    # Fee is uint24 (3 bytes)
    fee_hex = encoded_params[128:192]
    fee = int(fee_hex, 16)
    
    # Ticks are int24
    tick_lower_hex = encoded_params[192:256]
    tick_upper_hex = encoded_params[256:320]
    tick_lower = int(tick_lower_hex, 16)
    if tick_lower >= 2**23:  # Handle negative numbers (two's complement)
        tick_lower -= 2**24
    tick_upper = int(tick_upper_hex, 16)
    if tick_upper >= 2**23:
        tick_upper -= 2**24
    
    # Amounts are uint256
    amount0_desired_hex = encoded_params[320:384]
    amount1_desired_hex = encoded_params[384:448]
    amount0_min_hex = encoded_params[448:512]
    amount1_min_hex = encoded_params[512:576]
    
    amount0_desired = int(amount0_desired_hex, 16)
    amount1_desired = int(amount1_desired_hex, 16)
    amount0_min = int(amount0_min_hex, 16)
    amount1_min = int(amount1_min_hex, 16)
    
    # Recipient address
    recipient = "0x" + encoded_params[576:640][-40:]
    
    # Deadline
    deadline_hex = encoded_params[640:704]
    deadline = int(deadline_hex, 16)
    
    print(f"token0: {token0}")
    print(f"token1: {token1}")
    print(f"fee: {fee}")
    print(f"tickLower: {tick_lower}")
    print(f"tickUpper: {tick_upper}")
    print(f"amount0Desired: {amount0_desired} ({Web3.from_wei(amount0_desired, 'ether')} ether)")
    print(f"amount1Desired: {amount1_desired} ({Web3.from_wei(amount1_desired, 'ether')} ether)")
    print(f"amount0Min: {amount0_min} ({Web3.from_wei(amount0_min, 'ether')} ether)")
    print(f"amount1Min: {amount1_min} ({Web3.from_wei(amount1_min, 'ether')} ether)")
    print(f"recipient: {recipient}")
    print(f"deadline: {deadline}")
    
    # Check if tickLower < tickUpper
    if tick_lower >= tick_upper:
        print("\nERROR: tickLower must be less than tickUpper")
    
    # Check if the current tick is within the range
    print(f"\nCurrent tick from our debug script: 51299")
    if tick_lower <= 51299 <= tick_upper:
        print("Current tick is within the specified range")
    else:
        print("WARNING: Current tick is NOT within the specified range")

print("\nPossible Issues:")
print("1. Ticks are not initialized - Uniswap V3 requires ticks to be initialized before they can be used")
print("2. Incorrect fee tier - The fee parameter must match the pool's fee")
print("3. Insufficient liquidity - The pool might not have enough liquidity to support the position")
print("4. Ratio of tokens doesn't match the current price - The ratio of token0 to token1 must be close to the current price")
print("5. Slippage too low - The minimum amounts might be too close to the desired amounts")

# Check if we can get more information from the pool
print("\nRecommendations:")
print("1. Try using initialized ticks from our debug script")
print("2. Try with a smaller amount of tokens")
print("3. Try with a wider price range")
print("4. Try with higher slippage tolerance")
print("5. Check if the pool exists and has liquidity") 