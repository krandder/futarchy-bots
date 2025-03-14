#!/usr/bin/env python3
"""
Futarchy Trading Bot - Main entry point
"""

import sys
import os
import argparse

# Add the current directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from cli.menu import FutarchyMenu
from core.futarchy_bot import FutarchyBot
from strategies.monitoring import simple_monitoring_strategy
from strategies.probability import probability_threshold_strategy
from strategies.arbitrage import arbitrage_strategy

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Futarchy Trading Bot')
    
    # General options
    parser.add_argument('--rpc', type=str, help='RPC URL for Gnosis Chain')
    
    # Command mode
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Interactive mode (default)
    interactive_parser = subparsers.add_parser('interactive', help='Run in interactive mode')
    
    # Monitor mode
    monitor_parser = subparsers.add_parser('monitor', help='Run monitoring strategy')
    monitor_parser.add_argument('--iterations', type=int, default=5, help='Number of monitoring iterations')
    monitor_parser.add_argument('--interval', type=int, default=60, help='Interval between updates (seconds)')
    
    # Probability strategy mode
    prob_parser = subparsers.add_parser('probability', help='Run probability threshold strategy')
    prob_parser.add_argument('--buy', type=float, default=0.7, help='Buy threshold')
    prob_parser.add_argument('--sell', type=float, default=0.3, help='Sell threshold')
    prob_parser.add_argument('--amount', type=float, default=0.1, help='Trade amount')
    
    # Arbitrage strategy mode
    arb_parser = subparsers.add_parser('arbitrage', help='Run arbitrage strategy')
    arb_parser.add_argument('--diff', type=float, default=0.02, help='Minimum price difference')
    arb_parser.add_argument('--amount', type=float, default=0.1, help='Trade amount')
    
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_args()
    
    # Initialize the bot with optional RPC URL
    if args.command != 'interactive':
        bot = FutarchyBot(rpc_url=args.rpc)
        
        # Get and print balances
        balances = bot.get_balances()
        bot.print_balances(balances)
        
        # Get and print market prices
        prices = bot.get_market_prices()
        if prices:
            bot.print_market_prices(prices)
    
    # Run the appropriate command
    if args.command == 'monitor' or args.command is None:
        if args.command == 'monitor':
            print(f"Running monitoring strategy for {args.iterations} iterations every {args.interval} seconds")
            bot.run_strategy(lambda b: simple_monitoring_strategy(b, args.iterations, args.interval))
        else:
            # Default to interactive mode
            menu = FutarchyMenu()
            menu.run()
    
    elif args.command == 'interactive':
        menu = FutarchyMenu()
        menu.run()
    
    elif args.command == 'probability':
        print(f"Running probability threshold strategy (buy: {args.buy}, sell: {args.sell}, amount: {args.amount})")
        bot.run_strategy(lambda b: probability_threshold_strategy(b, args.buy, args.sell, args.amount))
    
    elif args.command == 'arbitrage':
        print(f"Running arbitrage strategy (min diff: {args.diff}, amount: {args.amount})")
        bot.run_strategy(lambda b: arbitrage_strategy(b, args.diff, args.amount))

if __name__ == "__main__":
    main()
