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
    DEFAULT_PERMIT_CONFIG,
    DEFAULT_RPC_URLS,
    UNISWAP_V3_POOL_ABI,
    UNISWAP_V3_PASSTHROUGH_ROUTER_ABI
)
from eth_account import Account
from eth_account.signers.local import LocalAccount
import math

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
    
    # Add the arbitrage synthetic GNO command
    arbitrage_synthetic_gno_parser = subparsers.add_parser('arbitrage_synthetic_gno', 
                                help='Execute full arbitrage: buy GNO spot → split → sell YES/NO → merge')
    arbitrage_synthetic_gno_parser.add_argument('amount', type=float, help='Amount of sDAI to use for arbitrage')
    
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
    
    # Add buy_sdai_yes command
    buy_sdai_yes_parser = subparsers.add_parser('buy_sdai_yes', help='Buy sDAI-YES tokens with sDAI using the dedicated sDAI/sDAI-YES pool')
    buy_sdai_yes_parser.add_argument('amount', type=float, help='Amount of sDAI to spend')
    
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
    elif args.command == 'buy_sdai_yes':
        buy_sdai_yes(bot, args.amount)
    
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
    
    elif args.command == 'arbitrage_synthetic_gno':
        # This function executes a full arbitrage operation
        execute_arbitrage_synthetic_gno(bot, args.amount)
    
    else:
        # Default to showing help
        print("Please specify a command. Use --help for available commands.")
        sys.exit(1)

def sell_sdai_yes(bot, amount):
    """
    Sell sDAI-YES tokens for sDAI.
    
    Args:
        bot: FutarchyBot instance
        amount: Amount of sDAI-YES to sell
    """
    # Function to floor a number to 6 decimal places
    def floor_to_6(val):
        # Convert to string with 6 decimal places, then back to float
        # This effectively truncates (floors) the value to 6 decimal places
        str_val = str(float(val))
        if '.' in str_val:
            integer_part, decimal_part = str_val.split('.')
            decimal_part = decimal_part[:6]  # Keep only first 6 decimal digits
            return float(f"{integer_part}.{decimal_part}")
        return float(val)
    
    # Round the input amount to 6 decimal places
    amount = float(round(float(amount), 6))
    print(f"\n🔄 Selling {amount:.6f} sDAI-YES for sDAI...")
    
    # Get current balances
    balances = bot.get_balances()
    sdai_yes_balance = balances['currency']['yes']
    sdai_balance = balances['currency']['wallet']
    
    # Display floor-rounded balances
    sdai_yes_display = floor_to_6(sdai_yes_balance)
    sdai_display = floor_to_6(sdai_balance)
    
    print("Balance before swap:")
    print(f"sDAI-YES: {sdai_yes_display:.6f}")
    print(f"sDAI: {sdai_display:.6f}")
    
    # Get current pool price
    pool_address = bot.w3.to_checksum_address(POOL_CONFIG_YES["address"])
    pool_abi = [{"inputs": [], "name": "slot0", "outputs": [{"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"}, {"internalType": "int24", "name": "tick", "type": "int24"}, {"internalType": "uint16", "name": "observationIndex", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"}, {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"}, {"internalType": "bool", "name": "unlocked", "type": "bool"}], "stateMutability": "view", "type": "function"}]
    pool_contract = bot.w3.eth.contract(address=pool_address, abi=pool_abi)
    slot0 = pool_contract.functions.slot0().call()
    current_sqrt_price = slot0[0]
    print(f"Current pool sqrtPriceX96: {current_sqrt_price}")
    
    # For zero_for_one=True (going down in price), use 80% of current price as the limit
    sqrt_price_limit_x96 = int(current_sqrt_price * 0.8)
    print(f"Using price limit of 80% of current price: {sqrt_price_limit_x96}")
    
    # Check balance (display floor-rounded values, compare exact values)
    print(f"💰 Current balance: {sdai_yes_display:.6f} tokens")
    print(f"💰 Required amount: {amount:.6f} tokens")
    
    if sdai_yes_balance < amount:
        print("❌ Insufficient balance")
        print("❌ Swap failed!")
        return
    
    # Execute the swap
    router = PassthroughRouter(
        bot.w3,
        os.environ.get("PRIVATE_KEY"),
        os.environ.get("V3_PASSTHROUGH_ROUTER_ADDRESS")
    )
    
    result = router.execute_swap(
        pool_address=pool_address,
        token_in=TOKEN_CONFIG["currency"]["yes_address"],
        token_out=TOKEN_CONFIG["currency"]["address"],
        amount=amount,
        zero_for_one=True,
        sqrt_price_limit_x96=sqrt_price_limit_x96
    )
    
    if result:
        print("✅ Swap successful!")
        
        # Get updated balances
        updated_balances = bot.get_balances()
        sdai_yes_change = updated_balances['currency']['yes'] - sdai_yes_balance
        sdai_change = updated_balances['currency']['wallet'] - sdai_balance
        
        print("\nBalance Changes:")
        print(f"sDAI-YES: {sdai_yes_change:+.6f}")
        print(f"sDAI: {sdai_change:+.6f}")
        
        # Calculate effective price and compare with the event probability
        if sdai_yes_change != 0:  # Avoid division by zero
            effective_price = abs(float(sdai_change) / float(sdai_yes_change))
            effective_percent = effective_price * 100
            event_probability = bot.get_sdai_yes_probability()
            event_percent = event_probability * 100
            
            print(f"\nEffective price: {effective_price:.6f} sDAI per sDAI-YES ({effective_percent:.2f}%)")
            print(f"Current pool price ratio: {event_probability:.6f} ({event_percent:.2f}%)")
            
            price_diff_pct = ((effective_price / event_probability) - 1) * 100
            print(f"Price difference from pool: {price_diff_pct:.2f}%")
        
        # Also show the full balances
        bot.print_balances(updated_balances)
    else:
        print("❌ Swap failed!")

def buy_sdai_yes(bot, amount_in_sdai):
    """
    Buy sDAI-YES tokens using sDAI directly from the sDAI/sDAI-YES pool.
    
    Args:
        bot: FutarchyBot instance
        amount_in_sdai (float): Amount of sDAI to use for buying sDAI-YES
    """
    def floor_to_6(num):
        # Convert decimal to float if needed
        if hasattr(num, 'is_finite') and num.is_finite():  # Check if it's a Decimal
            num = float(num)
        return math.floor(num * 1e6) / 1e6
    
    # Convert to float to ensure proper calculation
    amount_in_sdai = float(amount_in_sdai)
    
    print(f"\n🔄 Buying sDAI-YES with {amount_in_sdai:.6f} sDAI...")
    
    # Get token balances before swap
    balances = bot.get_balances()
    sdai_balance = balances['currency']['wallet']
    sdai_yes_balance = balances['currency']['yes']
    print("Balance before swap:")
    print(f"sDAI-YES: {sdai_yes_balance}")
    print(f"sDAI: {sdai_balance}")
    
    # Check if user has enough sDAI
    if sdai_balance < amount_in_sdai:
        print(f"❌ Insufficient sDAI balance. You have {sdai_balance} sDAI, but need {amount_in_sdai} sDAI.")
        return
    
    # Get pool address from constants
    pool_address = CONTRACT_ADDRESSES["sdaiYesPool"]
    print(f"Using sDAI/sDAI-YES pool: {pool_address}")
    
    # Get account address
    account = bot.account.address
    
    # Initialize the router with Web3
    router_address = CONTRACT_ADDRESSES["uniswapV3PassthroughRouter"]
    router = bot.w3.eth.contract(
        address=bot.w3.to_checksum_address(router_address),
        abi=UNISWAP_V3_PASSTHROUGH_ROUTER_ABI
    )
    print(f"Using router: {router_address}")
    
    # Get the pool contract
    pool_contract = bot.w3.eth.contract(
        address=bot.w3.to_checksum_address(pool_address),
        abi=UNISWAP_V3_POOL_ABI
    )
    
    # Get token0 and token1 addresses
    token0_address = bot.w3.to_checksum_address(pool_contract.functions.token0().call())
    token1_address = bot.w3.to_checksum_address(pool_contract.functions.token1().call())
    print(f"Pool token0: {token0_address}")
    print(f"Pool token1: {token1_address}")
    
    # Get sDAI and sDAI-YES addresses
    sdai_address = bot.w3.to_checksum_address(TOKEN_CONFIG["currency"]["address"]) 
    sdai_yes_address = bot.w3.to_checksum_address(TOKEN_CONFIG["currency"]["yes_address"])
    print(f"sDAI address: {sdai_address}")
    print(f"sDAI-YES address: {sdai_yes_address}")
    
    # Determine if sDAI-YES is token0 or token1
    if token0_address.lower() == sdai_yes_address.lower() and token1_address.lower() == sdai_address.lower():
        # sDAI-YES is token0, sDAI is token1
        zero_for_one = False  # We're swapping token1 for token0
        print("sDAI-YES is token0, sDAI is token1 => using zero_for_one=FALSE to buy sDAI-YES with sDAI")
    elif token0_address.lower() == sdai_address.lower() and token1_address.lower() == sdai_yes_address.lower():
        # sDAI is token0, sDAI-YES is token1
        zero_for_one = True  # We're swapping token0 for token1
        print("sDAI is token0, sDAI-YES is token1 => using zero_for_one=TRUE to buy sDAI-YES with sDAI")
    else:
        print(f"❌ Pool does not contain the expected tokens.")
        print(f"Expected tokens: sDAI ({sdai_address}) and sDAI-YES ({sdai_yes_address})")
        print(f"Pool tokens: token0 ({token0_address}) and token1 ({token1_address})")
        return
    
    try:
        # Get current sqrtPriceX96
        slot0 = pool_contract.functions.slot0().call()
        current_sqrt_price_x96 = slot0[0]
        print(f"Current pool sqrtPriceX96: {current_sqrt_price_x96}")
        
        # Set price limit based on direction
        if zero_for_one:
            # If swapping token0 for token1, we set a lower price limit (minimum we accept)
            # We accept a price 20% lower than current
            price_limit = int(current_sqrt_price_x96 * 0.8)
        else:
            # If swapping token1 for token0, we set a higher price limit (maximum we will pay)
            # We accept a price 20% higher than current
            price_limit = int(current_sqrt_price_x96 * 1.2)
        
        print(f"Using price limit of {'80%' if zero_for_one else '120%'} of current price: {price_limit}")
        
        # First we need to authorize the pool for the router (if not already authorized)
        print(f"\n🔑 Authorizing pool for router...")
        
        try:
            tx = router.functions.authorizePool(pool_address).build_transaction({
                'from': account,
                'gas': 500000,
                'gasPrice': bot.w3.eth.gas_price,
                'nonce': bot.w3.eth.get_transaction_count(account),
                'chainId': bot.w3.eth.chain_id,
            })
            
            signed_tx = bot.account.sign_transaction(tx)
            tx_hash = bot.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            receipt = bot.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                print(f"✅ Pool authorization successful!")
            else:
                print(f"⚠️ Pool authorization failed. But this may be because it's already authorized.")
        except Exception as e:
            print(f"⚠️ Pool authorization error: {e}. But we'll continue as it might already be authorized.")
        
        # First test with a small amount
        test_amount = min(amount_in_sdai * 0.1, 1e-5)
        print(f"\n🧪 Testing with small amount ({test_amount} sDAI) first...")
        
        # Convert to wei
        test_amount_wei = bot.w3.to_wei(test_amount, 'ether')
        
        # For the swap function, we need to approve the token we're spending
        # We need to approve the router to spend our token, not the pool
        try:
            if zero_for_one:
                # If zero_for_one is True, we're selling token0 (sDAI) to buy token1 (sDAI-YES)
                bot.approve_token(sdai_address, router_address, test_amount_wei)
            else:
                # If zero_for_one is False, we're selling token1 (sDAI) to buy token0 (sDAI-YES)
                bot.approve_token(sdai_address, router_address, test_amount_wei)
        except Exception as e:
            print(f"⚠️ Error in token approval: {e}")
            print("Continuing anyway as it might be approved already...")
        
        # The amountSpecified parameter is positive for exact input, negative for exact output
        # We're doing exact input, so it's positive
        amount_specified = test_amount_wei
        
        # Empty bytes for the data parameter
        empty_bytes = b''
        
        # Execute the test swap
        tx = router.functions.swap(
            pool_address,             # pool
            account,                  # recipient
            zero_for_one,             # zeroForOne
            amount_specified,         # amountSpecified
            price_limit,              # sqrtPriceLimitX96
            empty_bytes               # data
        ).build_transaction({
            'from': account,
            'gas': 500000,
            'gasPrice': bot.w3.eth.gas_price,
            'nonce': bot.w3.eth.get_transaction_count(account),
            'chainId': bot.w3.eth.chain_id,
        })
        
        # Sign and send transaction using bot's account
        signed_tx = bot.account.sign_transaction(tx)
        tx_hash = bot.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = bot.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            print(f"✅ Test swap successful!")
        else:
            print(f"❌ Test swap failed. See transaction for details.")
            return
        
        # Now do the actual swap with the full amount
        print(f"\n💱 Executing swap with {amount_in_sdai} sDAI...")
        
        # Convert to wei
        amount_wei = bot.w3.to_wei(amount_in_sdai, 'ether')
        
        # Approve the tokens again for the full amount
        try:
            if zero_for_one:
                bot.approve_token(sdai_address, router_address, amount_wei)
            else:
                bot.approve_token(sdai_address, router_address, amount_wei)
        except Exception as e:
            print(f"⚠️ Error in token approval: {e}")
            print("Continuing anyway as it might be approved already...")
        
        # Execute the swap
        tx = router.functions.swap(
            pool_address,             # pool
            account,                  # recipient
            zero_for_one,             # zeroForOne
            amount_wei,               # amountSpecified
            price_limit,              # sqrtPriceLimitX96
            empty_bytes               # data
        ).build_transaction({
            'from': account,
            'gas': 500000,
            'gasPrice': bot.w3.eth.gas_price,
            'nonce': bot.w3.eth.get_transaction_count(account),
            'chainId': bot.w3.eth.chain_id,
        })
        
        # Sign and send transaction using bot's account
        signed_tx = bot.account.sign_transaction(tx)
        tx_hash = bot.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = bot.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            print(f"✅ Swap successful!")
            print(f"Transaction hash: {tx_hash.hex()}")

            try:
                # Get tokens after swap
                updated_balances = bot.get_balances()
                new_sdai_balance = updated_balances['currency']['wallet']
                new_sdai_yes_balance = updated_balances['currency']['yes']
                
                # Convert to float if they are Decimal objects
                sdai_balance_float = float(sdai_balance)
                new_sdai_balance_float = float(new_sdai_balance)
                sdai_yes_balance_float = float(sdai_yes_balance)
                new_sdai_yes_balance_float = float(new_sdai_yes_balance)
                
                sdai_spent = floor_to_6(sdai_balance_float - new_sdai_balance_float)
                sdai_yes_gained = floor_to_6(new_sdai_yes_balance_float - sdai_yes_balance_float)
                
                print("\n📊 Swap Summary:")
                print(f"sDAI spent: {sdai_spent}")
                print(f"sDAI-YES gained: {sdai_yes_gained}")
                
                if sdai_spent > 0 and sdai_yes_gained > 0:
                    effective_price = sdai_spent / sdai_yes_gained
                    print(f"Effective price: {effective_price:.6f} sDAI per sDAI-YES")
                else:
                    print("Effective price: Unable to calculate (no sDAI spent or no sDAI-YES gained)")
                    
                # Get the probability from the pool
                probability = bot.get_sdai_yes_probability()
                print(f"Current pool price ratio: {probability:.6f}")
                
                # Show updated balances
                bot.print_balances(updated_balances)
                return True
            except Exception as e:
                print(f"⚠️ Error calculating swap summary: {e}")
                print("But the swap was successful!")
                return True
        else:
            print(f"❌ Swap failed. See transaction for details.")
            return False
            
    except Exception as e:
        print(f"❌ Error during swap: {e}")
        print(f"❌ Test swap failed. The pool may have low liquidity or the parameters are incorrect.")
        print(f"Consider using the split_sdai command to split sDAI into YES/NO tokens at 1:1 ratio.")
        return False

def execute_arbitrage_synthetic_gno(bot, sdai_amount):
    """
    Execute a full arbitrage operation:
    1. Buy waGNO with sDAI
    2. Unwrap waGNO to GNO
    3. Split GNO into YES/NO tokens
    4. Sell GNO-YES for sDAI-YES
    5. Sell GNO-NO for sDAI-NO
    6. Merge sDAI-YES and sDAI-NO back into sDAI
    7. Compare final sDAI amount with initial amount
    
    Args:
        bot: The FutarchyBot instance
        sdai_amount: Amount of sDAI to use for arbitrage
    """
    print(f"\n🔄 Starting synthetic GNO arbitrage with {sdai_amount} sDAI")
    
    # Get initial balances and prices
    initial_balances = bot.get_balances()
    initial_sdai = float(initial_balances['currency']['wallet'])
    
    if initial_sdai < sdai_amount:
        print(f"❌ Insufficient sDAI balance. Required: {sdai_amount}, Available: {initial_sdai}")
        return
    
    # Get initial market prices for reporting only
    print("\n📊 Initial market prices:")
    market_prices = bot.get_market_prices()
    synthetic_price, spot_price = bot.calculate_synthetic_price()
    
    print(f"GNO Spot Price: {spot_price:.6f} sDAI")
    print(f"GNO Synthetic Price: {synthetic_price:.6f} sDAI")
    print(f"Price Difference: {((synthetic_price / spot_price) - 1) * 100:.2f}%")
    
    # Step 1: Buy waGNO with sDAI
    print(f"\n🔹 Step 1: Buying waGNO with {sdai_amount} sDAI")
    from exchanges.balancer.swap import BalancerSwapHandler
    
    try:
        balancer = BalancerSwapHandler(bot)
        result = balancer.swap_sdai_to_wagno(sdai_amount)
        if not result or not result.get('success'):
            print("❌ Failed to buy waGNO. Aborting arbitrage.")
            return
            
        wagno_received = result['balance_changes']['token_out']
        print(f"✅ Successfully bought {wagno_received:.6f} waGNO")
    except Exception as e:
        print(f"❌ Error during waGNO purchase: {e}")
        return
    
    # Step 2: Unwrap waGNO to GNO
    print(f"\n🔹 Step 2: Unwrapping {wagno_received:.6f} waGNO to GNO")
    success = bot.aave_balancer.unwrap_wagno(wagno_received)
    
    if not success:
        print("❌ Failed to unwrap waGNO. Aborting arbitrage.")
        return
    
    # Check GNO balance
    intermediate_balances = bot.get_balances()
    gno_amount = float(intermediate_balances['company']['wallet'])
    
    if gno_amount <= 0:
        print("❌ No GNO received after unwrapping. Aborting arbitrage.")
        return
    
    print(f"✅ Received {gno_amount:.6f} GNO after unwrapping")
    
    # Step 3: Split GNO into YES/NO tokens
    print(f"\n🔹 Step 3: Splitting {gno_amount:.6f} GNO into YES/NO tokens")
    # Using the existing split_gno functionality (add_collateral)
    if not bot.add_collateral('company', gno_amount):
        print("❌ Failed to split GNO. Aborting arbitrage.")
        return
    
    # Check GNO-YES and GNO-NO balances
    intermediate_balances = bot.get_balances()
    gno_yes_amount = float(intermediate_balances['company']['yes'])
    gno_no_amount = float(intermediate_balances['company']['no'])
    
    if gno_yes_amount <= 0 or gno_no_amount <= 0:
        print("❌ Failed to receive both GNO-YES and GNO-NO tokens. Aborting arbitrage.")
        return
    
    print(f"✅ Received {gno_yes_amount:.6f} GNO-YES and {gno_no_amount:.6f} GNO-NO tokens")
    
    # Step 4: Sell GNO-YES for sDAI-YES
    print(f"\n🔹 Step 4: Selling {gno_yes_amount:.6f} GNO-YES for sDAI-YES")
    
    # Get the router
    router = PassthroughRouter(
        bot.w3,
        os.environ.get("PRIVATE_KEY"),
        os.environ.get("V3_PASSTHROUGH_ROUTER_ADDRESS")
    )
    
    # Get the current pool price directly from the pool
    pool_address = router.w3.to_checksum_address(POOL_CONFIG_YES["address"])
    pool_abi = [{"inputs": [], "name": "slot0", "outputs": [{"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"}, {"internalType": "int24", "name": "tick", "type": "int24"}, {"internalType": "uint16", "name": "observationIndex", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"}, {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"}, {"internalType": "bool", "name": "unlocked", "type": "bool"}], "stateMutability": "view", "type": "function"}]
    pool_contract = router.w3.eth.contract(address=pool_address, abi=pool_abi)
    slot0 = pool_contract.functions.slot0().call()
    current_sqrt_price = slot0[0]
    
    # For zero_for_one=True (going down in price), use 80% of current price as the limit
    sqrt_price_limit_x96 = int(current_sqrt_price * 0.8)
    
    result = router.execute_swap(
        pool_address=pool_address,
        token_in=TOKEN_CONFIG["company"]["yes_address"],
        token_out=TOKEN_CONFIG["currency"]["yes_address"],
        amount=gno_yes_amount,
        zero_for_one=True,
        sqrt_price_limit_x96=sqrt_price_limit_x96
    )
    
    if result:
        print("✅ Successfully sold GNO-YES tokens for sDAI-YES")
    else:
        print("⚠️ Failed to sell GNO-YES tokens. Continuing with remaining steps.")
    
    # Step 5: Sell GNO-NO for sDAI-NO
    print(f"\n🔹 Step 5: Selling {gno_no_amount:.6f} GNO-NO for sDAI-NO")
    
    # Get the current pool price directly from the pool
    pool_address = router.w3.to_checksum_address(POOL_CONFIG_NO["address"])
    pool_contract = router.w3.eth.contract(address=pool_address, abi=pool_abi)
    slot0 = pool_contract.functions.slot0().call()
    current_sqrt_price = slot0[0]
    
    # For zero_for_one=False (going up in price), use 120% of current price as the limit
    sqrt_price_limit_x96 = int(current_sqrt_price * 1.2)
    
    result = router.execute_swap(
        pool_address=pool_address,
        token_in=TOKEN_CONFIG["company"]["no_address"],
        token_out=TOKEN_CONFIG["currency"]["no_address"],
        amount=gno_no_amount,
        zero_for_one=False,
        sqrt_price_limit_x96=sqrt_price_limit_x96
    )
    
    if result:
        print("✅ Successfully sold GNO-NO tokens for sDAI-NO")
    else:
        print("⚠️ Failed to sell GNO-NO tokens. Continuing with remaining steps.")
    
    # Check sDAI-YES and sDAI-NO balances for merging
    intermediate_balances = bot.get_balances()
    sdai_yes_amount = float(intermediate_balances['currency']['yes'])
    sdai_no_amount = float(intermediate_balances['currency']['no'])
    
    # Step 6: Merge sDAI-YES and sDAI-NO into sDAI
    # We can only merge the minimum of the two amounts
    merge_amount = min(sdai_yes_amount, sdai_no_amount)
    
    if merge_amount > 0:
        print(f"\n🔹 Step 6: Merging {merge_amount:.6f} sDAI-YES and sDAI-NO tokens into sDAI")
        # Using the existing merge_sdai functionality
        if not bot.remove_collateral('currency', merge_amount):
            print("⚠️ Failed to merge sDAI tokens. Continuing to final evaluation.")
        else:
            print(f"✅ Successfully merged {merge_amount:.6f} pairs of YES/NO tokens into sDAI")
    else:
        print("\n🔹 Step 6: No tokens to merge (requires equal YES and NO amounts)")
    
    # Get final balances and calculate profit/loss
    final_balances = bot.get_balances()
    final_sdai = float(final_balances['currency']['wallet'])
    sdai_yes_final = float(final_balances['currency']['yes'])
    sdai_no_final = float(final_balances['currency']['no'])
    
    # Calculate remaining value locked in YES/NO tokens
    # This is a rough estimate using the current market probability
    market_prices_final = bot.get_market_prices()
    probability = market_prices_final.get('probability', 0.5)
    
    estimated_value_of_yes = sdai_yes_final * probability
    estimated_value_of_no = sdai_no_final * (1 - probability)
    
    # Total value = direct sDAI + estimated value of YES/NO tokens
    total_estimated_value = final_sdai + estimated_value_of_yes + estimated_value_of_no
    
    # Calculate profit/loss
    profit_loss = final_sdai - initial_sdai
    profit_loss_percent = (profit_loss / initial_sdai) * 100 if initial_sdai > 0 else 0
    
    total_profit_loss = total_estimated_value - initial_sdai
    total_profit_loss_percent = (total_profit_loss / initial_sdai) * 100 if initial_sdai > 0 else 0
    
    # Get updated market prices for reporting only
    synthetic_price_final, spot_price_final = bot.calculate_synthetic_price()
    
    # Print summary
    print("\n📈 Arbitrage Operation Summary")
    print("=" * 40)
    print(f"Initial sDAI: {initial_sdai:.6f}")
    print(f"Final sDAI: {final_sdai:.6f}")
    print(f"Direct Profit/Loss: {profit_loss:.6f} sDAI ({profit_loss_percent:.2f}%)")
    
    print(f"\nRemaining sDAI-YES: {sdai_yes_final:.6f}")
    print(f"Remaining sDAI-NO: {sdai_no_final:.6f}")
    print(f"Estimated value of remaining tokens: {(estimated_value_of_yes + estimated_value_of_no):.6f} sDAI")
    print(f"Total estimated value: {total_estimated_value:.6f} sDAI")
    print(f"Total estimated profit/loss: {total_profit_loss:.6f} sDAI ({total_profit_loss_percent:.2f}%)")
    
    print("\nMarket Prices:")
    print(f"Initial GNO Spot: {spot_price:.6f} → Final: {spot_price_final:.6f}")
    print(f"Initial GNO Synthetic: {synthetic_price:.6f} → Final: {synthetic_price_final:.6f}")
    print(f"Initial Price Gap: {((synthetic_price / spot_price) - 1) * 100:.2f}% → Final: {((synthetic_price_final / spot_price_final) - 1) * 100:.2f}%")
    
    if profit_loss > 0:
        print("\n✅ Arbitrage was profitable!")
    else:
        print("\n⚠️ Arbitrage was not profitable. Consider market conditions and gas costs.")

if __name__ == "__main__":
    main()
