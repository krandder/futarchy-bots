#!/usr/bin/env python3
import os
import sys
import argparse
from decimal import Decimal
from web3 import Web3

# Add the parent directory to the path so we can import the core module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.futarchy_bot import FutarchyBot
from config.constants import TOKEN_CONFIG, POOL_CONFIG_YES, UNISWAP_V3_POOL_ABI
from utils.web3_utils import get_raw_transaction

def main():
    parser = argparse.ArgumentParser(description="Test swapping sDAI YES tokens to GNO YES tokens with custom price limit")
    parser.add_argument("--amount", type=float, default=0.00001, help="Amount to swap (default: 0.00001)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--limit-factor", type=float, default=0.5, help="Price limit factor (0.5 = 50% worse than current price)")
    args = parser.parse_args()
    
    print(f"=== Testing sDAI YES to GNO YES Swap with Custom Price Limit (Amount: {args.amount} sDAI YES) ===")
    
    # Initialize the bot
    bot = FutarchyBot(verbose=args.verbose)
    
    # Check current balances
    print("\nChecking current balances...\n")
    balances = bot.get_balances()
    
    # Check if we have enough sDAI YES tokens
    sdai_yes_balance = Decimal(balances["currency"]["yes"])
    print(f"✅ sDAI YES balance is sufficient: {sdai_yes_balance}")
    
    if sdai_yes_balance < Decimal(args.amount):
        print(f"❌ Insufficient sDAI YES balance. Required: {args.amount}, Available: {sdai_yes_balance}")
        return
    
    # Get current price from the pool
    print("\nGetting current price from the pool...")
    
    # Create pool contract
    pool_contract = bot.w3.eth.contract(
        address=bot.w3.to_checksum_address(POOL_CONFIG_YES["address"]),
        abi=UNISWAP_V3_POOL_ABI
    )
    
    # Get token0 and token1
    token0 = pool_contract.functions.token0().call()
    token1 = pool_contract.functions.token1().call()
    
    # Get slot0 data
    slot0 = pool_contract.functions.slot0().call()
    current_sqrt_price_x96 = slot0[0]
    
    print(f"Current sqrtPriceX96: {current_sqrt_price_x96}")
    
    # Calculate a more lenient price limit
    # If we're swapping token1 for token0 (sDAI YES for GNO YES), we want a higher price limit
    # If we're swapping token0 for token1 (GNO YES for sDAI YES), we want a lower price limit
    
    # Determine if we're swapping token0 for token1 or vice versa
    sdai_yes_address = TOKEN_CONFIG["currency"]["yes_address"]
    gno_yes_address = TOKEN_CONFIG["company"]["yes_address"]
    
    zero_for_one = bot.w3.to_checksum_address(sdai_yes_address) == bot.w3.to_checksum_address(token0)
    
    # Calculate price limit based on direction
    if zero_for_one:
        # Swapping token0 for token1, want lower price limit
        sqrt_price_limit_x96 = int(current_sqrt_price_x96 * (1 - args.limit_factor))
    else:
        # Swapping token1 for token0, want higher price limit
        sqrt_price_limit_x96 = int(current_sqrt_price_x96 * (1 + args.limit_factor))
    
    print(f"Using custom sqrtPriceLimitX96: {sqrt_price_limit_x96}")
    
    # Execute the swap with custom price limit
    print(f"\nSwapping {args.amount} sDAI YES for GNO YES...")
    
    # Convert amount to wei
    amount_wei = bot.w3.to_wei(args.amount, 'ether')
    
    # Determine which tokens to use in the swap
    token_in = TOKEN_CONFIG["currency"]["yes_address"]  # YES sDAI
    token_out = TOKEN_CONFIG["company"]["yes_address"]  # YES GNO
    
    # Check balance of the token we're using as input
    token_in_contract = bot.get_token_contract(token_in)
    token_in_balance = token_in_contract.functions.balanceOf(bot.address).call()
    
    print(f"Checking balance for token: {token_in}")
    print(f"Required: {bot.w3.from_wei(amount_wei, 'ether')}")
    print(f"Available: {bot.w3.from_wei(token_in_balance, 'ether')}")
    
    if token_in_balance < amount_wei:
        print(f"❌ Insufficient token balance for swap")
        return
    
    # Approve token for SushiSwap
    if not bot.approve_token(token_in_contract, bot.w3.to_checksum_address(bot.sushiswap_router.address), amount_wei):
        return
    
    # Determine which pool to use
    pool_address = POOL_CONFIG_YES["address"]
    
    print(f"📝 Executing swap with custom price limit")
    print(f"Pool address: {pool_address}")
    print(f"Token In: {token_in}")
    print(f"Token Out: {token_out}")
    print(f"ZeroForOne: {zero_for_one}")
    print(f"Custom sqrtPriceLimitX96: {sqrt_price_limit_x96}")
    
    try:
        # Build transaction for swap
        swap_tx = bot.sushiswap_router.functions.swap(
            bot.w3.to_checksum_address(pool_address),  # pool address
            bot.address,  # recipient
            zero_for_one,  # zeroForOne
            int(amount_wei),  # amountSpecified
            int(sqrt_price_limit_x96),  # sqrtPriceLimitX96
            b''  # data - empty bytes
        ).build_transaction({
            'from': bot.address,
            'nonce': bot.w3.eth.get_transaction_count(bot.address),
            'gas': 1000000,  # INCREASED gas limit substantially
            'gasPrice': bot.w3.eth.gas_price,
            'chainId': bot.w3.eth.chain_id,
        })
        
        # Try to estimate gas to catch potential issues before sending
        try:
            estimated_gas = bot.w3.eth.estimate_gas(swap_tx)
            print(f"Estimated gas for this transaction: {estimated_gas}")
            
            # If estimated gas is more than 80% of our limit, increase limit further
            if estimated_gas > 800000:
                swap_tx['gas'] = int(estimated_gas * 1.25)  # Add 25% buffer
                print(f"Increased gas limit to: {swap_tx['gas']}")
        except Exception as gas_error:
            print(f"⚠️ Gas estimation failed: {gas_error}")
            print(f"⚠️ This may indicate the transaction will fail, but proceeding anyway...")
        
        signed_swap_tx = bot.w3.eth.account.sign_transaction(swap_tx, bot.account.key)
        swap_tx_hash = bot.w3.eth.send_raw_transaction(get_raw_transaction(signed_swap_tx))
        
        print(f"⏳ Swap transaction sent: {swap_tx_hash.hex()}")
        
        # Wait for confirmation
        swap_receipt = bot.w3.eth.wait_for_transaction_receipt(swap_tx_hash)
        
        if swap_receipt['status'] == 1:
            print(f"\n✅ sDAI YES to GNO YES swap test completed successfully")
        else:
            print(f"\n❌ Swap failed with receipt: {swap_receipt}")
    
    except Exception as e:
        print(f"❌ Error executing swap: {e}")
    
    # Check updated balances
    print("\nChecking updated balances...\n")
    bot.get_balances()

if __name__ == "__main__":
    main() 