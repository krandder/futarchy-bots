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

def handle_approval_tx(web3, tx, private_key, token_type="token"):
    """Handle approval transaction signing and confirmation."""
    try:
        # Sign and send approval transaction
        signed_tx = web3.eth.account.sign_transaction(tx, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"Approval transaction sent for {token_type}: {tx_hash.hex()}")
        
        # Wait for transaction confirmation
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt["status"] == 1:
            print(f"✅ {token_type.capitalize()} approval confirmed")
            return True
        else:
            print(f"❌ {token_type.capitalize()} approval failed")
            return False
    except Exception as e:
        print(f"❌ Error during {token_type} approval: {str(e)}")
        return False

def execute_operation_with_approvals(web3, handler, action, token_symbol, amount, address, private_key):
    """Execute token operation with automatic approval handling."""
    # First attempt
    if action == 'split':
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
    
    # Handle approvals if needed
    if not success:
        print(f"Info: {msg}")
        if not tx:
            print(f"❌ Error: No transaction data available for {msg}")
            return False
        
        # Handle the approval
        token_type = "token"
        if "YES token" in msg:
            token_type = "YES token"
        elif "NO token" in msg:
            token_type = "NO token"
        
        if not handle_approval_tx(web3, tx, private_key, token_type):
            return False
        
        # Try again after approval
        if action == 'split':
            success, msg, tx = handler.split_tokens(
                token_symbol=token_symbol,
                amount=amount,
                condition_id="",
                partition=[],
                from_address=address
            )
        else:  # merge
            success, msg, tx = handler.merge_tokens(
                token_symbol=token_symbol,
                amount=amount,
                condition_id="",
                partition=[],
                from_address=address
            )
        
        # If we still need another approval (for merge we need both YES and NO)
        if not success and "NO token" in msg and tx:
            if not handle_approval_tx(web3, tx, private_key, "NO token"):
                return False
            
            # Try one more time after NO token approval
            if action == 'merge':
                success, msg, tx = handler.merge_tokens(
                    token_symbol=token_symbol,
                    amount=amount,
                    condition_id="",
                    partition=[],
                    from_address=address
                )
    
    # If we have a valid transaction now, execute it
    if success:
        try:
            # Sign and send the main transaction
            signed_tx = web3.eth.account.sign_transaction(tx, private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            print(f"Transaction sent: {tx_hash.hex()}")
            
            # Wait for transaction and print final balances
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
            status = "Success" if receipt["status"] == 1 else "Failed"
            print(f"\nTransaction confirmed. Status: {status}")
            
            if receipt["status"] == 1:
                return True
            else:
                print(f"❌ Transaction failed. Please check the transaction details.")
                return False
                
        except Exception as e:
            print(f"❌ Error executing {action} operation: {str(e)}")
            return False
    else:
        print(f"❌ Could not prepare {action} transaction: {msg}")
        return False

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
    
    # Execute operation with automatic approval handling
    success = execute_operation_with_approvals(
        web3=web3,
        handler=handler,
        action=args.action,
        token_symbol=token_symbol,
        amount=amount,
        address=address,
        private_key=private_key
    )
    
    # Print final result and balances
    if success:
        print(f"\n✅ {args.action.capitalize()} operation for {args.token.upper()} completed successfully!")
    else:
        print(f"\n❌ {args.action.capitalize()} operation for {args.token.upper()} failed.")
    
    print("\nFinal balances:")
    print_balances(web3, address, TOKEN_CONFIG)

if __name__ == "__main__":
    main() 