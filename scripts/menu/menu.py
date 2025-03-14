"""
Menu system for the Futarchy Bot.
This module provides a command-line interface for interacting with the bot.
"""

import os
import sys
import time
from web3 import Web3
from core.futarchy_bot import FutarchyBot
from exchanges.balancer.swap import BalancerSwapHandler
from exchanges.balancer.permit2 import BalancerPermit2Handler
from config.constants import (
    CONTRACT_ADDRESSES, TOKEN_CONFIG, BALANCER_CONFIG
)

class FutarchyMenu:
    """Command-line menu for the Futarchy Bot."""
    
    def __init__(self, verbose=False):
        """
        Initialize the menu system.
        
        Args:
            verbose: Whether to print verbose debug information
        """
        self.verbose = verbose
        self.bot = None
        self.balancer_swap = None
        self.permit2_handler = None
        
        # Initialize the bot
        self.initialize_bot()
        
        # Token addresses from constants
        self.sdai_address = self.bot.w3.to_checksum_address(TOKEN_CONFIG["currency"]["address"])
        self.wagno_address = self.bot.w3.to_checksum_address(TOKEN_CONFIG["wagno"]["address"])
        
        # Initialize token contracts
        self.sdai_contract = self.bot.get_token_contract(self.sdai_address)
        self.wagno_contract = self.bot.get_token_contract(self.wagno_address)
        
        # Balancer vault address from constants
        self.balancer_vault_address = self.bot.w3.to_checksum_address(BALANCER_CONFIG["vault_address"])
        
        # BatchRouter address from constants
        self.batch_router_address = self.bot.w3.to_checksum_address(CONTRACT_ADDRESSES["batchRouter"])
    
    def initialize_bot(self):
        """Initialize the Futarchy Bot and related components."""
        try:
            # Create the bot instance
            self.bot = FutarchyBot(verbose=self.verbose)
            
            # Initialize Balancer swap handler
            self.balancer_swap = BalancerSwapHandler(self.bot, verbose=self.verbose)
            
            # Initialize Permit2 handler
            self.permit2_handler = BalancerPermit2Handler(self.bot, verbose=self.verbose)
            
            print(f"✅ Bot initialized with address: {self.bot.address}")
            
        except Exception as e:
            print(f"❌ Error initializing bot: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    def refresh_balances(self):
        """Refresh and display token balances."""
        try:
            # Get base token balances
            sdai_balance = self.sdai_contract.functions.balanceOf(self.bot.address).call()
            sdai_balance_eth = self.bot.w3.from_wei(sdai_balance, 'ether')
            
            wagno_balance = self.wagno_contract.functions.balanceOf(self.bot.address).call()
            wagno_balance_eth = self.bot.w3.from_wei(wagno_balance, 'ether')
            
            # Get XDAI balance (native currency on Gnosis Chain)
            xdai_balance = self.bot.w3.eth.get_balance(self.bot.address)
            xdai_balance_eth = self.bot.w3.from_wei(xdai_balance, 'ether')
            
            # Get conditional token balances (YES/NO tokens)
            # Get addresses from constants
            sdai_yes_address = self.bot.w3.to_checksum_address(TOKEN_CONFIG["currency"]["yes_address"])
            sdai_no_address = self.bot.w3.to_checksum_address(TOKEN_CONFIG["currency"]["no_address"])
            gno_yes_address = self.bot.w3.to_checksum_address(TOKEN_CONFIG["company"]["yes_address"])
            gno_no_address = self.bot.w3.to_checksum_address(TOKEN_CONFIG["company"]["no_address"])
            
            # Initialize conditional token balances
            conditional_balances = {
                "sdai_yes": 0,
                "sdai_no": 0,
                "gno_yes": 0,
                "gno_no": 0
            }
            
            # Check if addresses are valid (not zero address)
            if sdai_yes_address != '0x0000000000000000000000000000000000000000':
                sdai_yes_contract = self.bot.get_token_contract(sdai_yes_address)
                sdai_yes_balance = sdai_yes_contract.functions.balanceOf(self.bot.address).call()
                conditional_balances["sdai_yes"] = self.bot.w3.from_wei(sdai_yes_balance, 'ether')
            
            if sdai_no_address != '0x0000000000000000000000000000000000000000':
                sdai_no_contract = self.bot.get_token_contract(sdai_no_address)
                sdai_no_balance = sdai_no_contract.functions.balanceOf(self.bot.address).call()
                conditional_balances["sdai_no"] = self.bot.w3.from_wei(sdai_no_balance, 'ether')
            
            if gno_yes_address != '0x0000000000000000000000000000000000000000':
                gno_yes_contract = self.bot.get_token_contract(gno_yes_address)
                gno_yes_balance = gno_yes_contract.functions.balanceOf(self.bot.address).call()
                conditional_balances["gno_yes"] = self.bot.w3.from_wei(gno_yes_balance, 'ether')
            
            if gno_no_address != '0x0000000000000000000000000000000000000000':
                gno_no_contract = self.bot.get_token_contract(gno_no_address)
                gno_no_balance = gno_no_contract.functions.balanceOf(self.bot.address).call()
                conditional_balances["gno_no"] = self.bot.w3.from_wei(gno_no_balance, 'ether')
            
            # Display balances
            print("\n=== Token Balances ===")
            print(f"sDAI: {sdai_balance_eth:.6f}")
            print(f"waGNO: {wagno_balance_eth:.6f}")
            print(f"XDAI: {xdai_balance_eth:.6f}")
            
            # Display conditional token balances (only if non-zero)
            has_conditional = False
            
            if conditional_balances["sdai_yes"] > 0 or conditional_balances["sdai_no"] > 0:
                has_conditional = True
                print("\n--- Conditional sDAI Tokens ---")
                if conditional_balances["sdai_yes"] > 0:
                    print(f"sDAI YES: {conditional_balances['sdai_yes']:.6f}")
                if conditional_balances["sdai_no"] > 0:
                    print(f"sDAI NO: {conditional_balances['sdai_no']:.6f}")
            
            if conditional_balances["gno_yes"] > 0 or conditional_balances["gno_no"] > 0:
                has_conditional = True
                print("\n--- Conditional GNO Tokens ---")
                if conditional_balances["gno_yes"] > 0:
                    print(f"GNO YES: {conditional_balances['gno_yes']:.6f}")
                if conditional_balances["gno_no"] > 0:
                    print(f"GNO NO: {conditional_balances['gno_no']:.6f}")
            
            if not has_conditional and self.verbose:
                print("\nNo conditional tokens (YES/NO) found in wallet")
                
            print("=====================\n")
            
            return {
                "sdai": sdai_balance_eth,
                "wagno": wagno_balance_eth,
                "xdai": xdai_balance_eth,
                "conditional": conditional_balances
            }
            
        except Exception as e:
            print(f"❌ Error refreshing balances: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def check_permit2_status(self):
        """Check and display Permit2 authorization status."""
        try:
            # Check sDAI -> Permit2
            sdai_permit2_status = self.permit2_handler.check_permit(
                self.sdai_address, 
                self.permit2_handler.permit2_address,
                float('inf')  # Check for maximum allowance
            )
            
            # Check sDAI -> BatchRouter via Permit2
            sdai_batchrouter_status = self.permit2_handler.check_permit(
                self.sdai_address,
                self.batch_router_address,
                1.0  # Check for any allowance
            )
            
            # Display status
            print("\n=== Permit2 Status ===")
            print(f"sDAI -> Permit2: {'✅ APPROVED' if sdai_permit2_status['token_approved_for_permit2'] else '❌ NOT APPROVED'}")
            if sdai_permit2_status['token_approved_for_permit2']:
                print(f"  Allowance: {self.bot.w3.from_wei(sdai_permit2_status['permit2_allowance']['amount'], 'ether'):.2f}" if sdai_permit2_status['permit2_allowance'] else "  Allowance: 0")
            
            print(f"sDAI -> BatchRouter (via Permit2): {'✅ APPROVED' if not sdai_batchrouter_status['needs_permit'] else '❌ NOT APPROVED'}")
            if not sdai_batchrouter_status['needs_permit'] and sdai_batchrouter_status['permit2_allowance']:
                print(f"  Allowance: {self.bot.w3.from_wei(sdai_batchrouter_status['permit2_allowance']['amount'], 'ether'):.2f}")
                print(f"  Expires: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(sdai_batchrouter_status['permit2_allowance']['expiration']))}")
            print("=====================\n")
            
            return {
                "sdai_permit2": sdai_permit2_status,
                "sdai_batchrouter": sdai_batchrouter_status
            }
            
        except Exception as e:
            print(f"❌ Error checking Permit2 status: {e}")
            return None
    
    def approve_sdai_for_permit2(self):
        """Approve sDAI for Permit2."""
        try:
            print("Approving sDAI for Permit2...")
            
            # Get the maximum uint256 value for unlimited approval
            max_uint256 = 2**256 - 1
            
            # Approve the token
            tx_hash = self.bot.approve_token(
                self.sdai_contract,
                self.permit2_handler.permit2_address,
                max_uint256
            )
            
            if tx_hash:
                print(f"✅ sDAI approved for Permit2. Transaction: {tx_hash}")
                return True
            else:
                print("❌ Failed to approve sDAI for Permit2")
                return False
                
        except Exception as e:
            print(f"❌ Error approving sDAI for Permit2: {e}")
            return False
    
    def create_permit_for_batchrouter(self, amount=1.0, expiration_hours=24):
        """Create a Permit2 authorization for the BatchRouter."""
        try:
            print(f"Creating Permit2 authorization for BatchRouter (amount: {amount} sDAI, expiration: {expiration_hours} hours)...")
            
            # Create the permit
            result = self.permit2_handler.create_permit(
                self.sdai_address,
                self.batch_router_address,
                amount,
                expiration_hours
            )
            
            if result:
                print(f"✅ Permit2 authorization created for BatchRouter. Transaction: {result}")
                return True
            else:
                print(f"❌ Failed to create Permit2 authorization")
                return False
                
        except Exception as e:
            print(f"❌ Error creating Permit2 authorization: {e}")
            return False
    
    def swap_sdai_to_wagno(self, amount=0.1, min_amount_out=None):
        """Swap sDAI for waGNO."""
        try:
            print(f"Swapping {amount} sDAI for waGNO...")
            
            # Execute the swap
            result = self.balancer_swap.swap_sdai_to_wagno(amount, min_amount_out)
            
            if result and result.get("success", False):
                print(f"✅ Swap successful! Received {result['token_out_balance_eth']} waGNO")
                return True
            else:
                error_msg = result.get("error", "Unknown error") if result else "Swap failed"
                print(f"❌ Swap failed: {error_msg}")
                return False
                
        except Exception as e:
            print(f"❌ Error swapping sDAI to waGNO: {e}")
            return False
    
    def swap_wagno_to_sdai(self, amount=0.1, min_amount_out=None):
        """Swap waGNO for sDAI."""
        try:
            print(f"Swapping {amount} waGNO for sDAI...")
            
            # Execute the swap
            result = self.balancer_swap.swap_wagno_to_sdai(amount, min_amount_out)
            
            if result and result.get("success", False):
                print(f"✅ Swap successful! Received {result['token_out_balance_eth']} sDAI")
                return True
            else:
                error_msg = result.get("error", "Unknown error") if result else "Swap failed"
                print(f"❌ Swap failed: {error_msg}")
                return False
                
        except Exception as e:
            print(f"❌ Error swapping waGNO to sDAI: {e}")
            return False
    
    def display_menu(self):
        """Display the main menu."""
        print("\n=== Futarchy Bot Menu ===")
        print("1. Refresh Balances")
        print("2. Check Permit2 Status")
        print("3. Approve sDAI for Permit2")
        print("4. Create Permit for BatchRouter")
        print("5. Swap sDAI to waGNO")
        print("6. Swap waGNO to sDAI")
        print("7. Exit")
        print("========================\n")
    
    def run(self):
        """Run the menu loop."""
        while True:
            # Refresh balances automatically
            self.refresh_balances()
            
            # Display the menu
            self.display_menu()
            
            # Get user choice
            choice = input("Enter your choice (1-7): ")
            
            if choice == "1":
                self.refresh_balances()
            elif choice == "2":
                self.check_permit2_status()
            elif choice == "3":
                self.approve_sdai_for_permit2()
            elif choice == "4":
                amount = float(input("Enter amount to authorize (in sDAI): ") or "1.0")
                expiration = int(input("Enter expiration in hours (default 24): ") or "24")
                self.create_permit_for_batchrouter(amount, expiration)
            elif choice == "5":
                amount = float(input("Enter amount to swap (in sDAI): ") or "0.1")
                self.swap_sdai_to_wagno(amount)
            elif choice == "6":
                amount = float(input("Enter amount to swap (in waGNO): ") or "0.1")
                self.swap_wagno_to_sdai(amount)
            elif choice == "7":
                print("Exiting Futarchy Bot. Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")
            
            # Pause before showing the menu again
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    # Check if verbose mode is enabled
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    
    # Create and run the menu
    menu = FutarchyMenu(verbose=verbose)
    menu.run() 