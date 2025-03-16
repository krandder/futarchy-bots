#!/usr/bin/env python3
"""
Futarchy Trading Bot - Main entry point
"""

import sys
import os
import argparse
from decimal import Decimal

# Add the current directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.futarchy_bot import FutarchyBot
from strategies.monitoring import simple_monitoring_strategy
from strategies.probability import probability_threshold_strategy
from strategies.arbitrage import arbitrage_strategy
from config.constants import TOKEN_CONFIG, BALANCER_CONFIG

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
    
    # Swap commands
    swap_sdai_parser = subparsers.add_parser('swap_sdai', help='Swap sDAI to waGNO')
    swap_sdai_parser.add_argument('amount', type=float, help='Amount of sDAI to swap')
    
    swap_wagno_parser = subparsers.add_parser('swap_wagno', help='Swap waGNO to sDAI')
    swap_wagno_parser.add_argument('amount', type=float, help='Amount of waGNO to swap')
    
    unwrap_wagno_parser = subparsers.add_parser('unwrap_wagno', help='Unwrap waGNO to GNO')
    unwrap_wagno_parser.add_argument('amount', type=float, help='Amount of waGNO to unwrap')
    
    split_gno_parser = subparsers.add_parser('split_gno', help='Split GNO into YES/NO tokens')
    split_gno_parser.add_argument('amount', type=float, help='Amount of GNO to split')
    
    swap_gno_yes_parser = subparsers.add_parser('swap_gno_yes', help='Swap GNO YES to sDAI YES')
    swap_gno_yes_parser.add_argument('amount', type=float, help='Amount of GNO YES to swap')
    
    swap_gno_no_parser = subparsers.add_parser('swap_gno_no', help='Swap GNO NO to sDAI NO')
    swap_gno_no_parser.add_argument('amount', type=float, help='Amount of GNO NO to swap')
    
    # Add merge_sdai command
    merge_sdai_parser = subparsers.add_parser('merge_sdai', help='Merge sDAI-YES and sDAI-NO back into sDAI')
    merge_sdai_parser.add_argument('amount', type=float, help='Amount of sDAI-YES and sDAI-NO to merge')
    
    # Add debug command
    debug_parser = subparsers.add_parser('debug', help='Run in debug mode with additional output')
    
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_args()
    
    # Initialize the bot with optional RPC URL
    bot = FutarchyBot(rpc_url=args.rpc, verbose=args.verbose)
    
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
    
    if not args.amount:
        print("❌ Amount is required for this command")
        return
    
    # Run the appropriate command
    if args.command == 'monitor':
        print(f"Running monitoring strategy for {args.iterations} iterations every {args.interval} seconds")
        bot.run_strategy(lambda b: simple_monitoring_strategy(b, args.iterations, args.interval))
    
    elif args.command == 'prices':
        # Just show market prices without executing any strategy
        prices = bot.get_market_prices()
        if prices:
            print("\n=== Market Prices & Probability ===")
            print(f"YES GNO Price: {prices['yes_company_price']:.6f}")
            print(f"NO GNO Price: {prices['no_company_price']:.6f}")
            print(f"GNO Spot Price (SDAI): {prices['gno_spot_price']:.6f}")
            print(f"Event Probability: {prices['event_probability']:.2%}")
        return
    
    elif args.command == 'arbitrage':
        print(f"Running arbitrage strategy (min diff: {args.diff}, amount: {args.amount})")
        bot.run_strategy(lambda b: arbitrage_strategy(b, args.diff, args.amount))
    
    elif args.command == 'swap_sdai':
        # Swap sDAI to waGNO using Balancer BatchRouter
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
    
    elif args.command == 'swap_wagno':
        # Swap waGNO to sDAI using Balancer BatchRouter
        from exchanges.balancer.swap import BalancerSwapHandler
        try:
            balancer = BalancerSwapHandler(bot)
            result = balancer.swap_wagno_to_sdai(args.amount)
            if result and result.get('success'):
                print("\nTransaction Summary:")
                print(f"Transaction Hash: {result['tx_hash']}")
                print("\nBalance Changes:")
                print(f"waGNO: {result['balance_changes']['token_in']:+.18f}")
                print(f"sDAI: {result['balance_changes']['token_out']:+.18f}")
        except Exception as e:
            print(f"❌ Error during swap: {e}")
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
    
    else:
        # Default to showing help
        print("Please specify a command. Use --help for available commands.")
        sys.exit(1)

if __name__ == "__main__":
    main()
