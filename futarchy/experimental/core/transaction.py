"""
Transaction analysis module for checking and analyzing blockchain transactions.

This module is currently in EXPERIMENTAL status.
Requirements for promotion to DEVELOPMENT:
1. Complete test coverage
2. Documentation for all public functions
3. Error handling for all edge cases
"""

from web3 import Web3
from dotenv import load_dotenv
import os
import json
from typing import Dict, List, Union, Optional

# Load environment variables
load_dotenv()
RPC_URL = os.environ.get('RPC_URL')
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Configure token addresses 
GNO_NO_ADDRESS = '0xf1B3E5Ffc0219A4F8C0ac69EC98C97709EdfB6c9'
SDAI_NO_ADDRESS = '0xE1133Ef862f3441880adADC2096AB67c63f6E102'
NO_POOL_ADDRESS = '0x6E33153115Ab58dab0e0F1E3a2ccda6e67FA5cD7'

def analyze_transaction(tx_hash: str) -> Dict[str, Union[str, float, Dict]]:
    """
    Analyze a transaction and return detailed information about token transfers and swaps.
    
    Args:
        tx_hash: The transaction hash to analyze
        
    Returns:
        Dict containing transaction details, token transfers, and swap information
    """
    tx = w3.eth.get_transaction(tx_hash)
    tx_receipt = w3.eth.get_transaction_receipt(tx_hash)
    
    result = {
        'status': "Success" if tx_receipt.status == 1 else "Failed",
        'from': tx["from"],
        'to': tx["to"],
        'value': tx["value"],
        'gas_used': tx_receipt.gasUsed,
        'gas_price': tx["gasPrice"],
        'logs': []
    }
    
    # Process transaction logs
    for log in tx_receipt.logs:
        log_info = process_log(log)
        if log_info:
            result['logs'].append(log_info)
    
    # Calculate transaction summary
    summary = calculate_transaction_summary(result['logs'], tx['from'])
    result.update(summary)
    
    return result

def process_log(log: Dict) -> Optional[Dict]:
    """Process a single transaction log and return structured information."""
    log_info = {
        'address': log['address'],
        'topics': [topic.hex() for topic in log['topics']],
        'data': log['data'].hex() if isinstance(log['data'], bytes) else log['data']
    }
    
    # Process ERC20 Transfer events
    if (len(log_info['topics']) > 0 and 
        log_info['topics'][0] == '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'):
        return process_transfer_event(log_info)
    
    # Process Uniswap V3 Swap events
    elif (len(log_info['topics']) > 0 and 
          log_info['topics'][0] == '0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67'):
        return process_swap_event(log_info)
    
    return log_info

def process_transfer_event(log_info: Dict) -> Dict:
    """Process an ERC20 transfer event log."""
    token_address = log_info['address']
    token_name = ("GNO-NO" if token_address.lower() == GNO_NO_ADDRESS.lower() 
                 else "sDAI-NO" if token_address.lower() == SDAI_NO_ADDRESS.lower() 
                 else "Unknown Token")
    
    from_address = '0x' + log_info['topics'][1][26:]
    to_address = '0x' + log_info['topics'][2][26:]
    
    data_clean = log_info['data'][2:] if log_info['data'].startswith('0x') else log_info['data']
    value = int(data_clean, 16)
    value_decimal = value / (10**18)
    
    return {
        'type': 'transfer',
        'token': token_name,
        'token_address': token_address,
        'from': from_address,
        'to': to_address,
        'value': value,
        'value_decimal': value_decimal
    }

def process_swap_event(log_info: Dict) -> Dict:
    """Process a Uniswap V3 swap event log."""
    pool_address = log_info['address']
    pool_name = "NO Pool" if pool_address.lower() == NO_POOL_ADDRESS.lower() else "Unknown Pool"
    
    sender_address = '0x' + log_info['topics'][1][26:]
    recipient_address = '0x' + log_info['topics'][2][26:]
    
    data_clean = log_info['data'][2:] if log_info['data'].startswith('0x') else log_info['data']
    
    try:
        amount0 = int(data_clean[:64], 16)
        amount1 = int(data_clean[64:128], 16)
        sqrtPriceX96 = int(data_clean[128:192], 16)
        liquidity = int(data_clean[192:256], 16)
        tick = int(data_clean[256:320], 16)
        
        # Convert to signed integers if needed
        if amount0 >= 2**255:
            amount0 = amount0 - 2**256
        if amount1 >= 2**255:
            amount1 = amount1 - 2**256
        
        amount0_decimal = amount0 / (10**18)
        amount1_decimal = amount1 / (10**18)
        
        # Calculate prices
        price_from_sqrt = (sqrtPriceX96 ** 2) / (2 ** 192)
        
        return {
            'type': 'swap',
            'pool': pool_name,
            'pool_address': pool_address,
            'sender': sender_address,
            'recipient': recipient_address,
            'amount0': amount0,
            'amount0_decimal': amount0_decimal,
            'amount1': amount1,
            'amount1_decimal': amount1_decimal,
            'sqrtPriceX96': sqrtPriceX96,
            'liquidity': liquidity,
            'tick': tick,
            'price_from_sqrt': price_from_sqrt,
            'price_token1_in_token0': price_from_sqrt,
            'price_token0_in_token1': 1/price_from_sqrt if price_from_sqrt != 0 else None
        }
    except Exception as e:
        return {
            'type': 'swap',
            'error': str(e),
            'raw_data': log_info
        }

def calculate_transaction_summary(logs: List[Dict], user_address: str) -> Dict:
    """Calculate summary of token transfers and swaps for a transaction."""
    gno_no_transferred = 0
    sdai_no_transferred = 0
    swap_rate = None
    effective_rate = None
    
    # Process transfers
    for log in logs:
        if log.get('type') == 'transfer':
            value = log['value_decimal']
            if log['from'].lower() == user_address.lower():
                if log['token'] == 'GNO-NO':
                    gno_no_transferred = value
                elif log['token'] == 'sDAI-NO':
                    sdai_no_transferred = value
            elif log['to'].lower() == user_address.lower():
                if log['token'] == 'GNO-NO':
                    gno_no_transferred = -value
                elif log['token'] == 'sDAI-NO':
                    sdai_no_transferred = -value
    
    # Process swaps
    for log in logs:
        if log.get('type') == 'swap' and 'error' not in log:
            swap_rate = 1/log['price_from_sqrt']
            
            if abs(gno_no_transferred) > 0 and abs(sdai_no_transferred) > 0:
                if gno_no_transferred > 0:  # Sent GNO-NO, received sDAI-NO
                    effective_rate = abs(sdai_no_transferred) / gno_no_transferred
                else:  # Sent sDAI-NO, received GNO-NO
                    effective_rate = sdai_no_transferred / abs(gno_no_transferred)
    
    return {
        'summary': {
            'gno_no_amount': gno_no_transferred,
            'sdai_no_amount': sdai_no_transferred,
            'pool_rate': swap_rate,
            'effective_rate': effective_rate
        }
    }

if __name__ == '__main__':
    # Example usage
    tx_hash = '0x4902b54b67be76bb2d974043bf98b45cfeb8b03d0201dcb696ebfc13f9c10291'
    result = analyze_transaction(tx_hash)
    
    # Print results in a readable format
    print(f"Transaction Analysis for {tx_hash}")
    print(f"Status: {result['status']}")
    print(f"From: {result['from']}")
    print(f"To: {result['to']}")
    print(f"Value: {result['value']} wei")
    print(f"Gas used: {result['gas_used']}")
    print(f"Gas price: {result['gas_price']} wei")
    
    print("\nToken Transfers:")
    for log in result['logs']:
        if log.get('type') == 'transfer':
            print(f"{log['token']}: {log['value_decimal']} from {log['from']} to {log['to']}")
    
    print("\nSwap Information:")
    for log in result['logs']:
        if log.get('type') == 'swap' and 'error' not in log:
            print(f"Pool: {log['pool']}")
            print(f"Amount0 (sDAI-NO): {log['amount0_decimal']}")
            print(f"Amount1 (GNO-NO): {log['amount1_decimal']}")
            print(f"Price (sDAI-NO per GNO-NO): {log['price_token0_in_token1']:.6f}")
    
    print("\nSummary:")
    summary = result['summary']
    print(f"GNO-NO transferred: {summary['gno_no_amount']:.18f}")
    print(f"sDAI-NO transferred: {summary['sdai_no_amount']:.18f}")
    if summary['pool_rate']:
        print(f"Pool rate: {summary['pool_rate']:.6f} sDAI-NO per GNO-NO")
    if summary['effective_rate']:
        print(f"Effective rate: {summary['effective_rate']:.6f} sDAI-NO per GNO-NO") 