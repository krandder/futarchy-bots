from web3 import Web3
from dotenv import load_dotenv
import os
import json

load_dotenv()
RPC_URL = os.environ.get('RPC_URL')
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Configure token addresses 
GNO_NO_ADDRESS = '0xf1B3E5Ffc0219A4F8C0ac69EC98C97709EdfB6c9'
SDAI_NO_ADDRESS = '0xE1133Ef862f3441880adADC2096AB67c63f6E102'
NO_POOL_ADDRESS = '0x6E33153115Ab58dab0e0F1E3a2ccda6e67FA5cD7'

# Recent GNO-NO to sDAI-NO swap transaction
tx_hash = '0x4902b54b67be76bb2d974043bf98b45cfeb8b03d0201dcb696ebfc13f9c10291'
print(f'Transaction hash: {tx_hash}')

tx = w3.eth.get_transaction(tx_hash)
tx_receipt = w3.eth.get_transaction_receipt(tx_hash)

print(f'Status: {"Success" if tx_receipt.status == 1 else "Failed"}')
print(f'From: {tx["from"]}')
print(f'To: {tx["to"]}')
print(f'Value: {tx["value"]} wei')
print(f'Gas used: {tx_receipt.gasUsed}')
print(f'Gas price: {tx["gasPrice"]} wei')

# Create a simplified JSON representation of the logs
logs_simplified = []
for log in tx_receipt.logs:
    log_simplified = {
        'address': log['address'],
        'topics': [topic.hex() for topic in log['topics']],
        'data': log['data'].hex() if isinstance(log['data'], bytes) else log['data']
    }
    logs_simplified.append(log_simplified)

print("\nTransaction logs:")
for i, log in enumerate(logs_simplified):
    print(f"\nLog {i+1}:")
    print(f"  Address: {log['address']}")
    print(f"  Topics: {log['topics']}")
    data = log['data']
    data_length = len(data) - 2 if data.startswith('0x') else len(data)
    data_length = data_length // 2  # Convert from hex characters to bytes
    print(f"  Data length: {data_length} bytes")
    print(f"  Data: {data[:100]}..." if len(data) > 100 else f"  Data: {data}")
    
    # ERC20 Transfer event
    if (len(log['topics']) > 0 and 
        log['topics'][0] == '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'):
        token_address = log['address']
        print(f"  This is an ERC20 Transfer event from token: {token_address}")
        
        # token_address to readable name
        token_name = "GNO-NO" if token_address.lower() == GNO_NO_ADDRESS.lower() else "sDAI-NO" if token_address.lower() == SDAI_NO_ADDRESS.lower() else "Unknown Token"
        
        # Parse from and to addresses
        from_address = '0x' + log['topics'][1][26:]  # Extract the last 20 bytes
        to_address = '0x' + log['topics'][2][26:]  # Extract the last 20 bytes
        
        # Parse value
        data_clean = data[2:] if data.startswith('0x') else data
        value = int(data_clean, 16)
        value_decimal = value / (10**18)  # Assuming 18 decimals for the token
        
        print(f"  From: {from_address}")
        print(f"  To: {to_address}")
        print(f"  Value: {value} wei ({value_decimal:.18f} {token_name})")
    
    # Uniswap V3 Swap event
    elif len(log['topics']) > 0 and log['topics'][0] == '0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67':
        pool_address = log['address']
        print(f"  This is a Uniswap V3 Swap event from pool: {pool_address}")
        
        # Pool address to readable name
        pool_name = "NO Pool" if pool_address.lower() == NO_POOL_ADDRESS.lower() else "Unknown Pool"
        print(f"  Pool: {pool_name}")
        
        # The Swap event has the following format:
        # event Swap(
        #    address indexed sender,
        #    address indexed recipient,
        #    int256 amount0,
        #    int256 amount1,
        #    uint160 sqrtPriceX96,
        #    uint128 liquidity,
        #    int24 tick
        # )
        
        try:
            # Parse sender and recipient addresses
            sender_address = '0x' + log['topics'][1][26:]  # Extract the last 20 bytes
            recipient_address = '0x' + log['topics'][2][26:]  # Extract the last 20 bytes
            print(f"  Sender: {sender_address}")
            print(f"  Recipient: {recipient_address}")
            
            # Data includes amount0, amount1, sqrtPriceX96, liquidity, tick
            data_clean = data[2:] if data.startswith('0x') else data  # Remove 0x prefix
            amount0 = int(data_clean[:64], 16)  # First 32 bytes (64 hex chars)
            amount1 = int(data_clean[64:128], 16)  # Second 32 bytes
            sqrtPriceX96 = int(data_clean[128:192], 16)  # Third 32 bytes
            liquidity = int(data_clean[192:256], 16)  # Fourth 32 bytes
            tick = int(data_clean[256:320], 16)  # Fifth 32 bytes
            
            # Convert to signed integers if needed
            if amount0 >= 2**255:
                amount0 = amount0 - 2**256
            if amount1 >= 2**255:
                amount1 = amount1 - 2**256
                
            # Convert to token amounts with 18 decimals (common for ERC20)
            amount0_decimal = amount0 / (10**18)
            amount1_decimal = amount1 / (10**18)
            
            print(f"  Decoded Swap event:")
            print(f"    amount0 (sDAI-NO): {amount0} ({amount0_decimal:.18f} tokens)")
            print(f"    amount1 (GNO-NO): {amount1} ({amount1_decimal:.18f} tokens)")
            print(f"    sqrtPriceX96: {sqrtPriceX96}")
            print(f"    liquidity: {liquidity}")
            print(f"    tick: {tick}")
            
            # If one amount is positive and the other is negative, this is a swap
            if (amount0 > 0 and amount1 < 0) or (amount0 < 0 and amount1 > 0):
                if amount0 > 0 and amount1 < 0:
                    # token0 (sDAI-NO) is being received, token1 (GNO-NO) is being spent
                    price = amount0_decimal / abs(amount1_decimal)
                    print(f"    Price: {price:.6f} sDAI-NO per GNO-NO")
                    print(f"    or {1/price:.6f} GNO-NO per sDAI-NO")
                else:
                    # token1 (GNO-NO) is being received, token0 (sDAI-NO) is being spent
                    price = amount1_decimal / abs(amount0_decimal)
                    print(f"    Price: {price:.6f} GNO-NO per sDAI-NO")
                    print(f"    or {1/price:.6f} sDAI-NO per GNO-NO")
            else:
                print(f"    No actual token swap detected (both amounts are zero or same sign)")
                
            # Calculate price from sqrtPriceX96
            price_from_sqrt = (sqrtPriceX96 ** 2) / (2 ** 192)
            print(f"    Price from sqrtPriceX96: {price_from_sqrt:.18f}")
            print(f"    This is the price of token1 (GNO-NO) in terms of token0 (sDAI-NO)")
            print(f"    Or: {1/price_from_sqrt:.6f} sDAI-NO per GNO-NO")
            
        except Exception as e:
            print(f"  Error decoding Swap event: {e}")

print("\n===== Transaction Summary =====")
# Look for token transfers to summarize
gno_no_transferred = 0
sdai_no_transferred = 0

for log in logs_simplified:
    if (len(log['topics']) > 0 and 
        log['topics'][0] == '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'):
        token_address = log['address']
        data_clean = log['data'][2:] if log['data'].startswith('0x') else log['data']
        value = int(data_clean, 16)
        value_decimal = value / (10**18)
        
        # From user to router: this is input
        from_address = '0x' + log['topics'][1][26:]
        if from_address.lower() == tx['from'].lower():
            if token_address.lower() == GNO_NO_ADDRESS.lower():
                gno_no_transferred = value_decimal
                print(f"GNO-NO sent: {gno_no_transferred:.18f}")
            elif token_address.lower() == SDAI_NO_ADDRESS.lower():
                sdai_no_transferred = value_decimal
                print(f"sDAI-NO sent: {sdai_no_transferred:.18f}")
                
        # From router to user: this is output
        to_address = '0x' + log['topics'][2][26:]
        if to_address.lower() == tx['from'].lower():
            if token_address.lower() == GNO_NO_ADDRESS.lower():
                gno_no_transferred = -value_decimal  # Negative to indicate received
                print(f"GNO-NO received: {abs(gno_no_transferred):.18f}")
            elif token_address.lower() == SDAI_NO_ADDRESS.lower():
                sdai_no_transferred = -value_decimal  # Negative to indicate received
                print(f"sDAI-NO received: {abs(sdai_no_transferred):.18f}")

# Check for a Swap event to get the exchange rate
for log in logs_simplified:
    if len(log['topics']) > 0 and log['topics'][0] == '0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67':
        data_clean = log['data'][2:] if log['data'].startswith('0x') else log['data']
        amount0 = int(data_clean[:64], 16)
        amount1 = int(data_clean[64:128], 16)
        sqrtPriceX96 = int(data_clean[128:192], 16)
        
        # Convert to signed integers if needed
        if amount0 >= 2**255:
            amount0 = amount0 - 2**256
        if amount1 >= 2**255:
            amount1 = amount1 - 2**256
        
        # Compute price from sqrtPriceX96
        price_from_sqrt = (sqrtPriceX96 ** 2) / (2 ** 192)
        sDAI_per_GNO = 1/price_from_sqrt
        
        print(f"\nPool rate: {sDAI_per_GNO:.6f} sDAI-NO per GNO-NO")
        
        # If we have both input and output amounts, calculate the effective rate
        if abs(gno_no_transferred) > 0 and abs(sdai_no_transferred) > 0:
            if gno_no_transferred > 0:  # We sent GNO-NO, received sDAI-NO
                effective_rate = abs(sdai_no_transferred) / gno_no_transferred
                print(f"Effective rate: {effective_rate:.6f} sDAI-NO per GNO-NO")
            else:  # We sent sDAI-NO, received GNO-NO
                effective_rate = sdai_no_transferred / abs(gno_no_transferred)
                print(f"Effective rate: {effective_rate:.6f} sDAI-NO per GNO-NO") 