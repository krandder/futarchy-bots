from core.futarchy_bot import FutarchyBot
from config.constants import CONTRACT_ADDRESSES, TOKEN_CONFIG
import os

# Create bot instance
bot = FutarchyBot()

# Connect to the sDAI-YES/sDAI pool
pool_address = bot.w3.to_checksum_address(CONTRACT_ADDRESSES['sdaiYesPool'])
pool_abi = [
    {'inputs': [], 'name': 'slot0', 'outputs': [{'internalType': 'uint160', 'name': 'sqrtPriceX96', 'type': 'uint160'}, {'internalType': 'int24', 'name': 'tick', 'type': 'int24'}, {'internalType': 'uint16', 'name': 'observationIndex', 'type': 'uint16'}, {'internalType': 'uint16', 'name': 'observationCardinality', 'type': 'uint16'}, {'internalType': 'uint16', 'name': 'observationCardinalityNext', 'type': 'uint16'}, {'internalType': 'uint8', 'name': 'feeProtocol', 'type': 'uint8'}, {'internalType': 'bool', 'name': 'unlocked', 'type': 'bool'}], 'stateMutability': 'view', 'type': 'function'},
    {'inputs': [], 'name': 'token0', 'outputs': [{'internalType': 'address', 'name': '', 'type': 'address'}], 'stateMutability': 'view', 'type': 'function'},
    {'inputs': [], 'name': 'token1', 'outputs': [{'internalType': 'address', 'name': '', 'type': 'address'}], 'stateMutability': 'view', 'type': 'function'}
]
pool_contract = bot.w3.eth.contract(address=pool_address, abi=pool_abi)

# Get pool data
token0 = pool_contract.functions.token0().call()
token1 = pool_contract.functions.token1().call()
slot0 = pool_contract.functions.slot0().call()
sqrt_price_x96 = slot0[0]
tick = slot0[1]

# Calculate price
price = (sqrt_price_x96 ** 2) / (2 ** 192)

# Print info
print(f'=== sDAI-YES/sDAI Pool Data ===')
print(f'Pool address: {pool_address}')
print(f'Token0: {token0}')
print(f'Token1: {token1}')
print(f'Current sqrtPriceX96: {sqrt_price_x96}')
print(f'Current tick: {tick}')
print(f'Derived price: {price}')

# Convert price based on token ordering
sdai_yes_address = TOKEN_CONFIG['currency']['yes_address'].lower()
sdai_address = TOKEN_CONFIG['currency']['address'].lower()

if token0.lower() == sdai_yes_address and token1.lower() == sdai_address:
    print(f'Price represents: token1/token0')
    print(f'This means 1 sDAI-YES = {1/price:.6f} sDAI')
elif token0.lower() == sdai_address and token1.lower() == sdai_yes_address:
    print(f'Price represents: token1/token0')
    print(f'This means 1 sDAI-YES = {price:.6f} sDAI') 