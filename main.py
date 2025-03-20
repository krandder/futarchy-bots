#!/usr/bin/env python3
"""
Futarchy Trading Bot - Main entry point
"""

import sys
import os
import argparse
from decimal import Decimal
import time
import json
from web3 import Web3
from dotenv import load_dotenv
from exchanges.sushiswap import SushiSwapExchange
from exchanges.passthrough_router import PassthroughRouter
from config.constants import (
    CONTRACT_ADDRESSES,
    TOKEN_CONFIG,
    POOL_CONFIG_YES,
    POOL_CONFIG_NO,
    BALANCER_CONFIG,
    DEFAULT_SWAP_CONFIG,
    DEFAULT_PERMIT_CONFIG
)
from eth_account import Account
from eth_account.signers.local import LocalAccount

# Add the current directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.futarchy_bot import FutarchyBot
from strategies.monitoring import simple_monitoring_strategy
from strategies.probability import probability_threshold_strategy
from strategies.arbitrage import arbitrage_strategy

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Futarchy Trading Bot')
    
    # General options
    parser.add_argument('--rpc', type=str, help='RPC URL for Gnosis Chain')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    
    # Command mode
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Interactive mode (default)
    interactive_parser = subparsers.add_parser('interactive', help='Run in interactive mode')
    
    # Monitor mode
    monitor_parser = subparsers.add_parser('monitor', help='Run monitoring strategy')
    monitor_parser.add_argument('--iterations', type=int, default=5, help='Number of monitoring iterations')
    monitor_parser.add_argument('--interval', type=int, default=60, help='Interval between updates (seconds)')
    
    # Probability strategy mode
    prob_parser = subparsers.add_parser('prices', help='Show current market prices and probabilities')
    prob_parser.add_argument('--buy', type=float, default=0.7, help='Buy threshold')
    prob_parser.add_argument('--sell', type=float, default=0.3, help='Sell threshold')
    prob_parser.add_argument('--amount', type=float, default=0.1, help='Trade amount')
    
    # Arbitrage strategy mode
    arb_parser = subparsers.add_parser('arbitrage', help='Run arbitrage strategy')
    arb_parser.add_argument('--diff', type=float, default=0.02, help='Minimum price difference')
    arb_parser.add_argument('--amount', type=float, default=0.1, help='Trade amount')
    
    # Balance commands
    balances_parser = subparsers.add_parser('balances', help='Show token balances')
    refresh_balances_parser = subparsers.add_parser('refresh_balances', help='Refresh and show token balances')
    
    # Buy GNO commands
    buy_wrapped_gno_parser = subparsers.add_parser('buy_wrapped_gno', help='Buy waGNO with sDAI')
    buy_wrapped_gno_parser.add_argument('amount', type=float, help='Amount of sDAI to spend')
    
    buy_gno_parser = subparsers.add_parser('buy_gno', help='Buy GNO with sDAI (buys waGNO and unwraps it)')
    buy_gno_parser.add_argument('amount', type=float, help='Amount of sDAI to spend')
    
    unwrap_wagno_parser = subparsers.add_parser('unwrap_wagno', help='Unwrap waGNO to GNO')
    unwrap_wagno_parser.add_argument('amount', type=float, help='Amount of waGNO to unwrap')
    
    split_gno_parser = subparsers.add_parser('split_gno', help='Split GNO into YES/NO tokens')
    split_gno_parser.add_argument('amount', type=float, help='Amount of GNO to split')
    
    swap_gno_yes_parser = subparsers.add_parser('swap_gno_yes', help='Swap GNO YES to sDAI YES')
    swap_gno_yes_parser.add_argument('amount', type=float, help='Amount of GNO YES to swap')
    
    swap_gno_no_parser = subparsers.add_parser('swap_gno_no', help='Swap GNO NO to sDAI NO')
    swap_gno_no_parser.add_argument('amount', type=float, help='Amount of GNO NO to swap')
    
    # Add the four new passthrough router swap commands
    swap_gno_yes_to_sdai_yes_parser = subparsers.add_parser('swap_gno_yes_to_sdai_yes', help='Swap GNO YES to sDAI YES using passthrough router')
    swap_gno_yes_to_sdai_yes_parser.add_argument('amount', type=float, help='Amount of GNO YES to swap')
    
    swap_sdai_yes_to_gno_yes_parser = subparsers.add_parser('swap_sdai_yes_to_gno_yes', help='Swap sDAI YES to GNO YES using passthrough router')
    swap_sdai_yes_to_gno_yes_parser.add_argument('amount', type=float, help='Amount of sDAI YES to swap')
    
    swap_gno_no_to_sdai_no_parser = subparsers.add_parser('swap_gno_no_to_sdai_no', help='Swap GNO NO to sDAI NO using passthrough router')
    swap_gno_no_to_sdai_no_parser.add_argument('amount', type=float, help='Amount of GNO NO to swap')
    
    swap_sdai_no_to_gno_no_parser = subparsers.add_parser('swap_sdai_no_to_gno_no', help='Swap sDAI NO to GNO NO using passthrough router')
    swap_sdai_no_to_gno_no_parser.add_argument('amount', type=float, help='Amount of sDAI NO to swap')
    
    # Add merge_sdai command
    merge_sdai_parser = subparsers.add_parser('merge_sdai', help='Merge sDAI-YES and sDAI-NO back into sDAI')
    merge_sdai_parser.add_argument('amount', type=float, help='Amount of sDAI-YES and sDAI-NO to merge')
    
    # Add sell_sdai_yes command
    sell_sdai_yes_parser = subparsers.add_parser('sell_sdai_yes', help='Sell sDAI-YES tokens for sDAI')
    sell_sdai_yes_parser.add_argument('amount', type=float, help='Amount of sDAI-YES to sell')
    
    # Add debug command
    debug_parser = subparsers.add_parser('debug', help='Run in debug mode with additional output')
    
    # Add test_swaps command
    test_swaps_parser = subparsers.add_parser('test_swaps', help='Test all swap functions with small amounts')
    test_swaps_parser.add_argument('--amount', type=float, default=0.001, help='Amount to use for testing (default: 0.001)')
    
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_args()
    
    # Initialize the bot with optional RPC URL
    bot = FutarchyBot(rpc_url=args.rpc, verbose=args.verbose)
    
    # Initialize passthrough router for conditional token swaps
    router = PassthroughRouter(
        bot.w3,
        os.environ.get("PRIVATE_KEY"),
        os.environ.get("V3_PASSTHROUGH_ROUTER_ADDRESS")
    )
    
    if args.command == 'debug':
        # Debug mode - check pool configuration and balances
        print("\n🔍 Debug Information:")
        
        # Get token balances
        sdai_balance = bot.get_token_balance(TOKEN_CONFIG["currency"]["address"])
        wagno_balance = bot.get_token_balance(TOKEN_CONFIG["wagno"]["address"])
        print("\n💰 Token Balances:")
        print(f"  sDAI: {bot.w3.from_wei(sdai_balance, 'ether')}")
        print(f"  waGNO: {bot.w3.from_wei(wagno_balance, 'ether')}")
        
        # Check pool configuration
        pool_id = BALANCER_CONFIG["pool_id"]
        print(f"\n🏊 Pool Configuration:")
        print(f"  Pool Address: {BALANCER_CONFIG['pool_address']}")
        print(f"  Pool ID: {pool_id}")
        
        # Get pool tokens and balances
        try:
            tokens, balances, _ = bot.balancer_handler.balancer_vault.functions.getPoolTokens(pool_id).call()
            print("\n📊 Pool Tokens:")
            for i, token in enumerate(tokens):
                print(f"  {i+1}: {token} - Balance: {bot.w3.from_wei(balances[i], 'ether')}")
        except Exception as e:
            print(f"❌ Error getting pool tokens: {e}")
        
        # Check token approvals
        vault_address = BALANCER_CONFIG["vault_address"]
        sdai_allowance = bot.get_token_allowance(TOKEN_CONFIG["currency"]["address"], vault_address)
        wagno_allowance = bot.get_token_allowance(TOKEN_CONFIG["wagno"]["address"], vault_address)
        print("\n✅ Token Approvals for Balancer Vault:")
        print(f"  sDAI: {bot.w3.from_wei(sdai_allowance, 'ether')}")
        print(f"  waGNO: {bot.w3.from_wei(wagno_allowance, 'ether')}")
        
        return
    
    elif args.command in ['balances', 'refresh_balances']:
        balances = bot.get_balances()
        bot.print_balances(balances)
        return
    
    # Check if command needs an amount and if it's provided
    if hasattr(args, 'amount') and not args.amount and args.command not in ['test_swaps']:
        print("❌ Amount is required for this command")
        return
    
    # Run the appropriate command
    if args.command == 'monitor':
        print(f"Running monitoring strategy for {args.iterations} iterations every {args.interval} seconds")
        bot.run_strategy(lambda b: simple_monitoring_strategy(b, args.iterations, args.interval))
    
    elif args.command == 'prices':
        # Show market prices using the bot's print_market_prices method
        prices = bot.get_market_prices()
        if prices:
            bot.print_market_prices(prices)
        return
    
    elif args.command == 'arbitrage':
        print(f"Running arbitrage strategy (min diff: {args.diff}, amount: {args.amount})")
        bot.run_strategy(lambda b: arbitrage_strategy(b, args.diff, args.amount))
    
    elif args.command == 'buy_wrapped_gno':
        # Buy waGNO with sDAI using Balancer BatchRouter
        from exchanges.balancer.swap import BalancerSwapHandler
        try:
            balancer = BalancerSwapHandler(bot)
            result = balancer.swap_sdai_to_wagno(args.amount)
            if result and result.get('success'):
                print("\nTransaction Summary:")
                print(f"Transaction Hash: {result['tx_hash']}")
                print("\nBalance Changes:")
                print(f"sDAI: {result['balance_changes']['token_in']:+.18f}")
                print(f"waGNO: {result['balance_changes']['token_out']:+.18f}")
        except Exception as e:
            print(f"❌ Error during swap: {e}")
            sys.exit(1)
    
    elif args.command == 'buy_gno':
        # Buy waGNO and automatically unwrap it to GNO
        from exchanges.balancer.swap import BalancerSwapHandler
        try:
            print(f"\n🔄 Buying and unwrapping GNO using {args.amount} sDAI...")
            
            # Step 1: Buy waGNO
            balancer = BalancerSwapHandler(bot)
            result = balancer.swap_sdai_to_wagno(args.amount)
            if not result or not result.get('success'):
                print("❌ Failed to buy waGNO")
                sys.exit(1)
                
            wagno_received = result['balance_changes']['token_out']
            print(f"\n✅ Successfully bought {wagno_received:.18f} waGNO")
            
            # Step 2: Unwrap waGNO to GNO
            print(f"\n🔄 Unwrapping {wagno_received:.18f} waGNO to GNO...")
            success = bot.aave_balancer.unwrap_wagno(wagno_received)
            
            if success:
                print("✅ Successfully unwrapped waGNO to GNO")
                balances = bot.get_balances()
                bot.print_balances(balances)
            else:
                print("❌ Failed to unwrap waGNO")
                sys.exit(1)
                
        except Exception as e:
            print(f"❌ Error during buy_gno operation: {e}")
            sys.exit(1)
    
    elif args.command == 'unwrap_wagno':
        # Use the waGNO token contract to unwrap to GNO
        success = bot.aave_balancer.unwrap_wagno(args.amount)
        if success:
            balances = bot.get_balances()
            bot.print_balances(balances)
    
    elif args.command == 'split_gno':
        # Split GNO into YES/NO tokens using add_collateral
        success = bot.add_collateral('company', args.amount)
        if success:
            balances = bot.get_balances()
            bot.print_balances(balances)
    
    elif args.command == 'swap_gno_yes':
        amount_wei = bot.w3.to_wei(args.amount, 'ether')
        token_in = bot.w3.to_checksum_address(TOKEN_CONFIG["company"]["yes_address"])
        token_out = bot.w3.to_checksum_address(TOKEN_CONFIG["currency"]["yes_address"])
        bot.execute_swap(token_in=token_in, token_out=token_out, amount=amount_wei)
    
    elif args.command == 'swap_gno_no':
        amount_wei = bot.w3.to_wei(args.amount, 'ether')
        token_in = bot.w3.to_checksum_address(TOKEN_CONFIG["company"]["no_address"])
        token_out = bot.w3.to_checksum_address(TOKEN_CONFIG["currency"]["no_address"])
        bot.execute_swap(token_in=token_in, token_out=token_out, amount=amount_wei)
    
    elif args.command == 'merge_sdai':
        # Merge sDAI-YES and sDAI-NO back into sDAI
        success = bot.remove_collateral('currency', args.amount)
        if success:
            balances = bot.get_balances()
            bot.print_balances(balances)
    
    elif args.command == 'sell_sdai_yes':
        sell_sdai_yes(bot, args.amount)
    
    elif args.command == 'swap_gno_yes_to_sdai_yes':
        # In YES pool: GNO is token0, so GNO->SDAI is zero_for_one=true
        # Get the current pool price directly from the pool
        pool_address = router.w3.to_checksum_address(POOL_CONFIG_YES["address"])
        pool_abi = [{"inputs": [], "name": "slot0", "outputs": [{"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"}, {"internalType": "int24", "name": "tick", "type": "int24"}, {"internalType": "uint16", "name": "observationIndex", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"}, {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"}, {"internalType": "bool", "name": "unlocked", "type": "bool"}], "stateMutability": "view", "type": "function"}]
        pool_contract = router.w3.eth.contract(address=pool_address, abi=pool_abi)
        slot0 = pool_contract.functions.slot0().call()
        current_sqrt_price = slot0[0]
        print(f"Current pool sqrtPriceX96: {current_sqrt_price}")
        
        # For zero_for_one=True (going down in price), use 80% of current price as the limit
        sqrt_price_limit_x96 = int(current_sqrt_price * 0.8)
        print(f"Using price limit of 80% of current price: {sqrt_price_limit_x96}")
        
        result = router.execute_swap(
            pool_address=pool_address,
            token_in=TOKEN_CONFIG["company"]["yes_address"],
            token_out=TOKEN_CONFIG["currency"]["yes_address"],
            amount=args.amount,
            zero_for_one=True,
            sqrt_price_limit_x96=sqrt_price_limit_x96
        )
        if not result:
            print("❌ GNO YES to sDAI YES swap failed")
            return
    
    elif args.command == 'swap_sdai_yes_to_gno_yes':
        # In YES pool: GNO is token0, so SDAI->GNO is zero_for_one=false
        # Get the current pool price directly from the pool
        pool_address = router.w3.to_checksum_address(POOL_CONFIG_YES["address"])
        pool_abi = [{"inputs": [], "name": "slot0", "outputs": [{"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"}, {"internalType": "int24", "name": "tick", "type": "int24"}, {"internalType": "uint16", "name": "observationIndex", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"}, {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"}, {"internalType": "bool", "name": "unlocked", "type": "bool"}], "stateMutability": "view", "type": "function"}]
        pool_contract = router.w3.eth.contract(address=pool_address, abi=pool_abi)
        slot0 = pool_contract.functions.slot0().call()
        current_sqrt_price = slot0[0]
        print(f"Current pool sqrtPriceX96: {current_sqrt_price}")
        
        # For zero_for_one=False (going up in price), use 120% of current price as the limit
        sqrt_price_limit_x96 = int(current_sqrt_price * 1.2)
        print(f"Using price limit of 120% of current price: {sqrt_price_limit_x96}")
        
        result = router.execute_swap(
            pool_address=pool_address,
            token_in=TOKEN_CONFIG["currency"]["yes_address"],
            token_out=TOKEN_CONFIG["company"]["yes_address"],
            amount=args.amount,
            zero_for_one=False,
            sqrt_price_limit_x96=sqrt_price_limit_x96
        )
        if not result:
            print("❌ sDAI YES to GNO YES swap failed")
            return
    
    elif args.command == 'swap_gno_no_to_sdai_no':
        # In NO pool: SDAI is token0, so GNO->SDAI is zero_for_one=false
        # Get the current pool price directly from the pool
        pool_address = router.w3.to_checksum_address(POOL_CONFIG_NO["address"])
        pool_abi = [{"inputs": [], "name": "slot0", "outputs": [{"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"}, {"internalType": "int24", "name": "tick", "type": "int24"}, {"internalType": "uint16", "name": "observationIndex", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"}, {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"}, {"internalType": "bool", "name": "unlocked", "type": "bool"}], "stateMutability": "view", "type": "function"}]
        pool_contract = router.w3.eth.contract(address=pool_address, abi=pool_abi)
        slot0 = pool_contract.functions.slot0().call()
        current_sqrt_price = slot0[0]
        print(f"Current pool sqrtPriceX96: {current_sqrt_price}")
        
        # For zero_for_one=False (going up in price), use 120% of current price as the limit
        sqrt_price_limit_x96 = int(current_sqrt_price * 1.2)
        print(f"Using price limit of 120% of current price: {sqrt_price_limit_x96}")
        
        result = router.execute_swap(
            pool_address=pool_address,
            token_in=TOKEN_CONFIG["company"]["no_address"],
            token_out=TOKEN_CONFIG["currency"]["no_address"],
            amount=args.amount,
            zero_for_one=False,
            sqrt_price_limit_x96=sqrt_price_limit_x96
        )
        if not result:
            print("❌ GNO NO to sDAI NO swap failed")
            return
    
    elif args.command == 'swap_sdai_no_to_gno_no':
        # In NO pool: SDAI is token0, so SDAI->GNO is zero_for_one=true
        # Get the current pool price directly from the pool
        pool_address = router.w3.to_checksum_address(POOL_CONFIG_NO["address"])
        pool_abi = [{"inputs": [], "name": "slot0", "outputs": [{"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"}, {"internalType": "int24", "name": "tick", "type": "int24"}, {"internalType": "uint16", "name": "observationIndex", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"}, {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"}, {"internalType": "bool", "name": "unlocked", "type": "bool"}], "stateMutability": "view", "type": "function"}]
        pool_contract = router.w3.eth.contract(address=pool_address, abi=pool_abi)
        slot0 = pool_contract.functions.slot0().call()
        current_sqrt_price = slot0[0]
        print(f"Current pool sqrtPriceX96: {current_sqrt_price}")
        
        # For zero_for_one=True (going down in price), use 80% of current price as the limit
        sqrt_price_limit_x96 = int(current_sqrt_price * 0.8)
        print(f"Using price limit of 80% of current price: {sqrt_price_limit_x96}")
        
        result = router.execute_swap(
            pool_address=pool_address,
            token_in=TOKEN_CONFIG["currency"]["no_address"],
            token_out=TOKEN_CONFIG["company"]["no_address"],
            amount=args.amount,
            zero_for_one=True,
            sqrt_price_limit_x96=sqrt_price_limit_x96
        )
        if not result:
            print("❌ sDAI NO to GNO NO swap failed")
            return
    
    elif args.command == 'test_swaps':
        print("\n🧪 Testing all swap functions with small amounts...")
        test_amount = args.amount if hasattr(args, 'amount') else 0.001
        
        # Set up pool ABIs for price queries
        pool_abi = [{"inputs": [], "name": "slot0", "outputs": [{"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"}, {"internalType": "int24", "name": "tick", "type": "int24"}, {"internalType": "uint16", "name": "observationIndex", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"}, {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"}, {"internalType": "bool", "name": "unlocked", "type": "bool"}], "stateMutability": "view", "type": "function"}]
        
        # Get YES pool price
        yes_pool_address = router.w3.to_checksum_address(POOL_CONFIG_YES["address"])
        yes_pool_contract = router.w3.eth.contract(address=yes_pool_address, abi=pool_abi)
        yes_slot0 = yes_pool_contract.functions.slot0().call()
        yes_sqrt_price = yes_slot0[0]
        print(f"YES pool current sqrtPriceX96: {yes_sqrt_price}")
        
        # Get NO pool price
        no_pool_address = router.w3.to_checksum_address(POOL_CONFIG_NO["address"])
        no_pool_contract = router.w3.eth.contract(address=no_pool_address, abi=pool_abi)
        no_slot0 = no_pool_contract.functions.slot0().call()
        no_sqrt_price = no_slot0[0]
        print(f"NO pool current sqrtPriceX96: {no_sqrt_price}")
        
        # 1. Test GNO YES to SDAI YES
        print("\n\n============================================")
        print(f"🔄 Testing GNO YES to SDAI YES swap with {test_amount} tokens...")
        print("============================================")
        
        # For GNO to SDAI (zero_for_one=True), use 80% of current price
        yes_sqrt_price_limit = int(yes_sqrt_price * 0.8)
        print(f"Using price limit of 80% of current price: {yes_sqrt_price_limit}")
        
        gno_yes_to_sdai_result = router.execute_swap(
            pool_address=yes_pool_address,
            token_in=TOKEN_CONFIG["company"]["yes_address"],
            token_out=TOKEN_CONFIG["currency"]["yes_address"],
            amount=test_amount,
            zero_for_one=True,
            sqrt_price_limit_x96=yes_sqrt_price_limit
        )
        
        # 2. Test SDAI YES to GNO YES
        print("\n\n============================================")
        print(f"🔄 Testing SDAI YES to GNO YES swap with {test_amount} tokens...")
        print("============================================")
        
        # For SDAI to GNO (zero_for_one=False), use 120% of current price
        yes_sqrt_price_limit = int(yes_sqrt_price * 1.2)
        print(f"Using price limit of 120% of current price: {yes_sqrt_price_limit}")
        
        sdai_yes_to_gno_result = router.execute_swap(
            pool_address=yes_pool_address,
            token_in=TOKEN_CONFIG["currency"]["yes_address"],
            token_out=TOKEN_CONFIG["company"]["yes_address"],
            amount=test_amount,
            zero_for_one=False,
            sqrt_price_limit_x96=yes_sqrt_price_limit
        )
        
        # 3. Test GNO NO to SDAI NO
        print("\n\n============================================")
        print(f"🔄 Testing GNO NO to SDAI NO swap with {test_amount} tokens...")
        print("============================================")
        
        # For GNO to SDAI (zero_for_one=False), use 120% of current price
        no_sqrt_price_limit = int(no_sqrt_price * 1.2)
        print(f"Using price limit of 120% of current price: {no_sqrt_price_limit}")
        
        gno_no_to_sdai_result = router.execute_swap(
            pool_address=no_pool_address,
            token_in=TOKEN_CONFIG["company"]["no_address"],
            token_out=TOKEN_CONFIG["currency"]["no_address"],
            amount=test_amount,
            zero_for_one=False,
            sqrt_price_limit_x96=no_sqrt_price_limit
        )
        
        # 4. Test SDAI NO to GNO NO
        print("\n\n============================================")
        print(f"🔄 Testing SDAI NO to GNO NO swap with {test_amount} tokens...")
        print("============================================")
        
        # For SDAI to GNO (zero_for_one=True), use 80% of current price
        no_sqrt_price_limit = int(no_sqrt_price * 0.8)
        print(f"Using price limit of 80% of current price: {no_sqrt_price_limit}")
        
        sdai_no_to_gno_result = router.execute_swap(
            pool_address=no_pool_address,
            token_in=TOKEN_CONFIG["currency"]["no_address"],
            token_out=TOKEN_CONFIG["company"]["no_address"],
            amount=test_amount,
            zero_for_one=True,
            sqrt_price_limit_x96=no_sqrt_price_limit
        )
        
        # Print summary
        print("\n\n============================================")
        print("🧪 Swap Tests Summary")
        print("============================================")
        print(f"GNO YES to SDAI YES: {'✅ Success' if gno_yes_to_sdai_result else '❌ Failed'}")
        print(f"SDAI YES to GNO YES: {'✅ Success' if sdai_yes_to_gno_result else '❌ Failed'}")
        print(f"GNO NO to SDAI NO: {'✅ Success' if gno_no_to_sdai_result else '❌ Failed'}")
        print(f"SDAI NO to GNO NO: {'✅ Success' if sdai_no_to_gno_result else '❌ Failed'}")
        
        # Show final balances
        balances = bot.get_balances()
        bot.print_balances(balances)
    
    else:
        # Default to showing help
        print("Please specify a command. Use --help for available commands.")
        sys.exit(1)

def sell_sdai_yes(bot, amount):
    """
    Sell sDAI-YES tokens for sDAI using SushiSwap V3.
    
    Args:
        bot: FutarchyBot instance
        amount: Amount of sDAI-YES to sell
    """
    print(f"\n🔄 Selling {amount} sDAI-YES for sDAI...")
    
    # Convert amount to wei
    amount_wei = bot.w3.to_wei(amount, 'ether')
    
    # Get token addresses
    sdai_yes_address = TOKEN_CONFIG["currency"]["yes_address"]
    sdai_address = TOKEN_CONFIG["currency"]["address"]
    pool_address = CONTRACT_ADDRESSES["sdaiYesPool"]
    
    # Initialize SushiSwap exchange
    sushiswap = SushiSwapExchange(bot)
    
    # Get pool info to determine token order
    pool_info = sushiswap.get_pool_info(pool_address)
    token0 = pool_info['token0'].lower()
    
    # Determine if we're swapping token0 for token1 or vice versa
    zero_for_one = sdai_yes_address.lower() == token0
    
    # Execute the swap
    success = sushiswap.swap(
        pool_address=pool_address,
        token_in=sdai_yes_address,
        token_out=sdai_address,
        amount=amount_wei,
        zero_for_one=zero_for_one
    )
    
    if success:
        print("✅ Swap completed successfully!")
        # Refresh balances to show the result
        show_balances(bot)
    else:
        print("❌ Swap failed!")

if __name__ == "__main__":
    main()
