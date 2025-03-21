"""
Test script for splitting and merging conditional tokens.
"""

import os
import sys
import argparse
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
from decimal import Decimal

from futarchy.development.conditional_token_handler import ConditionalTokenHandler
from futarchy.development.config.tokens import TOKEN_CONFIG, format_token_amount
from futarchy.development.config.contracts import CONTRACTS
from futarchy.development.config.abis.erc20 import ERC20_ABI

def print_balances(web3, address, token_configs):
    """Print balances for all tokens."""
    print("\nCurrent Balances:")
    print("-" * 50)
    
    for token_type, config in token_configs.items():
        if token_type in ["currency", "company"]:  # Only check main tokens and their conditionals
            # Create contract
            contract = web3.eth.contract(
                address=config["address"],
                abi=ERC20_ABI
            )
            
            # Get balances
            balance = contract.functions.balanceOf(address).call()
            yes_balance = 0
            no_balance = 0
            
            if "yes_address" in config:
                yes_contract = web3.eth.contract(address=config["yes_address"], abi=ERC20_ABI)
                yes_balance = yes_contract.functions.balanceOf(address).call()
            
            if "no_address" in config:
                no_contract = web3.eth.contract(address=config["no_address"], abi=ERC20_ABI)
                no_balance = no_contract.functions.balanceOf(address).call()
            
            print(f"\n{config['name']}:")
            print(f"  Main Token: {format_token_amount(balance, config['address'])}")
            print(f"  YES Token: {format_token_amount(yes_balance, config['yes_address'])}")
            print(f"  NO Token: {format_token_amount(no_balance, config['no_address'])}")

def main():
    parser = argparse.ArgumentParser(description='Split or merge conditional tokens.')
    parser.add_argument('action', choices=['split', 'merge'], help='Action to perform')
    parser.add_argument('token', choices=['sdai', 'gno'], help='Token to split/merge')
    parser.add_argument('--amount', type=float, default=0.01, help='Amount to split/merge (default: 0.01)')
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    private_key = os.getenv("PRIVATE_KEY")
    if not private_key:
        print("Error: Please set PRIVATE_KEY in .env file")
        sys.exit(1)
    
    # Setup web3 and account
    web3 = Web3(Web3.HTTPProvider("https://rpc.gnosischain.com"))
    account = Account.from_key(private_key)
    address = account.address
    
    print(f"Using address: {address}")
    
    # Create handler
    handler = ConditionalTokenHandler(web3)
    
    # Print initial balances
    print_balances(web3, address, TOKEN_CONFIG)
    
    # Convert amount to wei
    amount = web3.to_wei(args.amount, 'ether')
    
    # Map token argument to token symbol
    token_map = {'sdai': 'currency', 'gno': 'company'}
    token_symbol = token_map[args.token]
    
    # Execute split/merge
    if args.action == 'split':
        success, msg, tx = handler.split_tokens(
            token_symbol=token_symbol,
            amount=amount,
            condition_id="",  # Not used with router
            partition=[],     # Not used with router
            from_address=address
        )
    else:  # merge
        success, msg, tx = handler.merge_tokens(
            token_symbol=token_symbol,
            amount=amount,
            condition_id="",  # Not used with router
            partition=[],     # Not used with router
            from_address=address
        )
    
    if not success:
        print(f"Error: {msg}")
        if tx:  # If we have an approval transaction
            # Sign and send approval transaction
            signed_tx = web3.eth.account.sign_transaction(tx, private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            print(f"Approval transaction sent: {tx_hash.hex()}")
            web3.eth.wait_for_transaction_receipt(tx_hash)
            print("Approval confirmed. Please run the command again to execute the split/merge.")
        sys.exit(1)
    
    # Sign and send the transaction
    signed_tx = web3.eth.account.sign_transaction(tx, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"Transaction sent: {tx_hash.hex()}")
    
    # Wait for transaction and print final balances
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    print("\nTransaction confirmed. Status:", "Success" if receipt["status"] == 1 else "Failed")
    print("\nFinal balances:")
    print_balances(web3, address, TOKEN_CONFIG)

if __name__ == "__main__":
    main() 