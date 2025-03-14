#!/usr/bin/env python3
"""
Run script for the Futarchy Bot menu.
This script provides a convenient way to start the interactive menu.
"""

import sys
from menu import FutarchyMenu

if __name__ == "__main__":
    # Check if verbose mode is enabled
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    
    # Print welcome message
    print("=" * 60)
    print("Welcome to the Futarchy Bot on Gnosis Chain")
    print("=" * 60)
    print("This bot helps you interact with Futarchy markets on Gnosis Chain")
    print("- Trade between sDAI and waGNO tokens")
    print("- Manage Permit2 authorizations for efficient trading")
    print("- View balances of base tokens and conditional YES/NO tokens")
    print("- Execute swaps on Balancer pools")
    print("-" * 60)
    print("Starting in", "verbose mode" if verbose else "normal mode")
    print("XDAI is the native currency on Gnosis Chain and is used for gas fees")
    print("=" * 60)
    
    try:
        # Create and run the menu
        menu = FutarchyMenu(verbose=verbose)
        menu.run()
    except KeyboardInterrupt:
        print("\nExiting Futarchy Bot. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 