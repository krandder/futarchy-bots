from core.futarchy_bot import FutarchyBot
from strategies.monitoring import simple_monitoring_strategy
from strategies.probability import probability_threshold_strategy
from strategies.arbitrage import arbitrage_strategy

class FutarchyMenu:
    """Interactive CLI menu for the Futarchy Trading Bot"""
    
    def __init__(self):
        """Initialize the menu and bot instance"""
        print("\n" + "="*50)
        print("🤖 Gnosis Futarchy Trading Bot")
        print("="*50)
        
        # Initialize bot
        self.bot = FutarchyBot()
        
        # Get and print balances
        balances = self.bot.get_balances()
        self.bot.print_balances(balances)
        
        # Get and print market prices
        prices = self.bot.get_market_prices()
        if prices:
            self.bot.print_market_prices(prices)
    
    def display_menu(self):
        """Display the main menu options"""
        print("\n" + "="*50)
        print("📋 Command Menu:")
        print("1. Refresh Balances")
        print("2. Refresh Market Prices")
        print("3. Convert XDAI to WXDAI")
        print("4. Convert WXDAI to SDAI")
        print("5. Add Collateral (GNO)")
        print("6. Remove Collateral (GNO)")
        print("7. Execute Swap")
        print("8. Add sDAI Collateral (Split into YES/NO tokens)")
        print("9. Wrap GNO to waGNO (Aave)")
        print("10. Unwrap waGNO to GNO")
        print("11. Swap sDAI for waGNO (Balancer)")
        print("12. Swap waGNO for sDAI (Balancer)")
        print("13. Check waGNO configuration")
        print("0. Exit")
    

    def handle_choice(self, choice):
        """
        Handle user's menu choice.
        
        Args:
            choice: User's menu selection
            
        Returns:
            bool: True to continue, False to exit
        """
        try:
            if choice == "0":
                print("Exiting...")
                return False
                
            elif choice == "1":
                balances = self.bot.get_balances()
                self.bot.print_balances(balances)
                
                # Also print Aave/Balancer token balances
                self.bot.aave_balancer.print_balances()
                
            elif choice == "2":
                prices = self.bot.get_market_prices()
                if prices:
                    self.bot.print_market_prices(prices)
                    
            elif choice == "3":
                # XDAI to WXDAI conversion
                amount = float(input("Enter amount of XDAI to convert to WXDAI: "))
                self.bot.convert_xdai_to_wxdai(amount)
                # Refresh balances after conversion
                balances = self.bot.get_balances()
                self.bot.print_balances(balances)
                
            elif choice == "4":
                # WXDAI to SDAI conversion
                amount = float(input("Enter amount of WXDAI to convert to SDAI: "))
                self.bot.convert_wxdai_to_sdai(amount)
                # Refresh balances after conversion
                balances = self.bot.get_balances()
                self.bot.print_balances(balances)
                
            elif choice == "5":
                amount = float(input("Enter amount of GNO to add as collateral: "))
                self.bot.add_collateral("company", amount)
                # Refresh balances after adding collateral
                balances = self.bot.get_balances()
                self.bot.print_balances(balances)
                
            elif choice == "6":
                amount = float(input("Enter amount of GNO to remove from collateral: "))
                self.bot.remove_collateral("company", amount)
                # Refresh balances after removing collateral
                balances = self.bot.get_balances()
                self.bot.print_balances(balances)
                
            elif choice == "7":
                # Swap Options:
                print("\nSwap Options:")
                print("1. Buy YES GNO tokens using YES sDAI")
                print("2. Sell YES GNO tokens for YES sDAI")
                print("3. Buy NO GNO tokens using NO sDAI")
                print("4. Sell NO GNO tokens for NO sDAI")
                swap_choice = input("\nEnter swap type (1-4): ")
                amount = float(input("Enter amount to swap: "))
                
                is_buy = swap_choice in ["1", "3"]
                is_yes = swap_choice in ["1", "2"]
                
                self.bot.execute_swap("company", is_buy, amount, is_yes)
                
                # Refresh balances after swap
                balances = self.bot.get_balances()
                self.bot.print_balances(balances)
                
            elif choice == "8":
                amount = float(input("Enter amount of sDAI to split into YES/NO tokens: "))
                self.bot.add_sdai_collateral(amount)
                # Refresh balances after adding collateral
                balances = self.bot.get_balances()
                self.bot.print_balances(balances)
                
            elif choice == "9":
                # Wrap GNO to waGNO
                amount = float(input("Enter amount of GNO to wrap: "))
                self.bot.aave_balancer.wrap_gno_to_wagno(amount)
                # Refresh balances
                self.bot.aave_balancer.print_balances()
                
            elif choice == "10":
                # Unwrap waGNO to GNO
                amount = float(input("Enter amount of waGNO to unwrap: "))
                self.bot.aave_balancer.unwrap_wagno_to_gno(amount)
                # Refresh balances
                self.bot.aave_balancer.print_balances()
                
            elif choice == "11":
                # Swap sDAI for waGNO on Balancer
                amount = float(input("Enter amount of sDAI to swap: "))
                min_amount = input("Enter minimum waGNO to receive (optional, leave blank for auto-calculation): ")
                min_amount_out = float(min_amount) if min_amount else None
                
                self.bot.aave_balancer.swap_sdai_to_wagno(amount, min_amount_out)
                # Refresh balances
                self.bot.aave_balancer.print_balances()
                
            elif choice == "12":
                # Swap waGNO for sDAI on Balancer
                amount = float(input("Enter amount of waGNO to swap: "))
                min_amount = input("Enter minimum sDAI to receive (optional, leave blank for auto-calculation): ")
                min_amount_out = float(min_amount) if min_amount else None
                
                self.bot.aave_balancer.swap_wagno_to_sdai(amount, min_amount_out)
                # Refresh balances
                self.bot.aave_balancer.print_balances()
            elif choice == "13":
                self.bot.aave_balancer.check_wagno_configuration()                
            else:
                print("Invalid choice, please try again.")
                
            return True
            
        except Exception as e:
            print(f"❌ Error handling menu choice: {e}")
            import traceback
            traceback.print_exc()
            print("\nPress Enter to continue...")
            input()  # Wait for user input before continuing
            return True  # Continue loop even after error


    def test_cowswap_api(self):
        """Test the CoW Swap API directly"""
        from config.constants import COWSWAP_API_URL
        import requests
        import json
        
        print("\n--- Testing CoW Swap API ---")
        
        # Test a simple API endpoint (price determination)
        test_url = f"{COWSWAP_API_URL}/api/v1/quote"
        
        # GNO and sDAI addresses
        sell_token = "0xaf204776c7245bF4147c2612BF6e5972Ee483701"  # sDAI
        buy_token = "0x9C58BAcC331c9aa871AFD802DB6379a98e80CEdb"   # GNO
        
        test_data = {
            "sellToken": sell_token,
            "buyToken": buy_token,
            "sellAmountBeforeFee": str(1000000000000000000),  # 1 token in wei
            "from": self.bot.address,
            "kind": "sell"
        }
        
        print(f"API URL: {test_url}")
        print(f"Test data: {json.dumps(test_data, indent=2)}")
        
        try:
            response = requests.post(test_url, json=test_data)
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Response text: {response.text}")
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"Parsed response: {json.dumps(response_data, indent=2)}")
        except Exception as e:
            print(f"Error testing API: {e}")
            import traceback
            traceback.print_exc()
        
        print("\nPress Enter to continue...")
        input()
    
    def run(self):
        """Run the main menu loop"""
        while True:
            self.display_menu()
            choice = input("\nEnter your choice: ")
            
            if not self.handle_choice(choice):
                break

def display_main_menu():
    """Display the main menu options."""
    print("\n" + "=" * 50)
    print("🤖 FUTARCHY TRADING BOT - MAIN MENU")
    print("=" * 50)
    print("1. 💰 Manage Tokens")
    print("2. 🔄 Execute Trades")
    print("3. 📊 View Market Data")
    print("4. 📈 Run Strategies")
    print("5. 💧 Manage Liquidity")
    print("6. ⚙️  Settings")
    print("0. 🚪 Exit")
    print("=" * 50)

def handle_main_menu_choice(choice):
    """Handle the user's choice from the main menu."""
    if choice == "1":
        token_management_menu()
    elif choice == "2":
        trading_menu()
    elif choice == "3":
        market_data_menu()
    elif choice == "4":
        strategy_menu()
    elif choice == "5":
        liquidity_menu()
    elif choice == "6":
        settings_menu()
    elif choice == "0":
        print("Exiting... Goodbye! 👋")
        return False
    else:
        print("❌ Invalid choice. Please try again.")
    
    return True

def liquidity_menu():
    """Display and handle the liquidity management menu."""
    while True:
        print("\n" + "=" * 50)
        print("💧 LIQUIDITY MANAGEMENT MENU")
        print("=" * 50)
        print("1. 🏊 Add Liquidity to Balancer Pool")
        print("2. 🏊 Add Liquidity to SushiSwap YES Pool")
        print("3. 🏊 Add Liquidity to SushiSwap NO Pool")
        print("4. 📋 View My Liquidity Positions")
        print("5. 💰 Collect Fees from Position")
        print("6. 🔄 Increase Liquidity in Position")
        print("7. 📉 Decrease Liquidity from Position")
        print("0. 🔙 Back to Main Menu")
        print("=" * 50)
        
        choice = input("Enter your choice: ")
        
        if choice == "1":
            add_liquidity_to_balancer()
        elif choice == "2":
            add_liquidity_to_sushiswap_yes()
        elif choice == "3":
            add_liquidity_to_sushiswap_no()
        elif choice == "4":
            view_liquidity_positions()
        elif choice == "5":
            collect_fees_from_position()
        elif choice == "6":
            increase_liquidity_in_position()
        elif choice == "7":
            decrease_liquidity_from_position()
        elif choice == "0":
            break
        else:
            print("❌ Invalid choice. Please try again.")

def add_liquidity_to_balancer():
    """Add liquidity to the Balancer pool."""
    print("\n" + "=" * 50)
    print("🏊 ADD LIQUIDITY TO BALANCER POOL")
    print("=" * 50)
    
    # Initialize the bot
    bot = initialize_bot()
    if bot is None:
        return
    
    # Get the amount of GNO to add
    gno_amount = get_float_input("Enter amount of GNO to add: ")
    if gno_amount <= 0:
        print("❌ Amount must be greater than 0.")
        return
    
    # Add liquidity to Balancer
    success = bot.add_liquidity_to_balancer(gno_amount)
    
    if success:
        print("✅ Successfully added liquidity to Balancer pool!")
    else:
        print("❌ Failed to add liquidity to Balancer pool.")

def add_liquidity_to_sushiswap_yes():
    """Add liquidity to the SushiSwap YES pool."""
    print("\n" + "=" * 50)
    print("🏊 ADD LIQUIDITY TO SUSHISWAP YES POOL")
    print("=" * 50)
    
    # Initialize the bot
    bot = initialize_bot()
    if bot is None:
        return
    
    # Get the amount of GNO YES tokens to add
    gno_amount = get_float_input("Enter amount of GNO YES tokens to add: ")
    if gno_amount <= 0:
        print("❌ Amount must be greater than 0.")
        return
    
    # Get the amount of sDAI YES tokens to add
    sdai_amount = get_float_input("Enter amount of sDAI YES tokens to add: ")
    if sdai_amount <= 0:
        print("❌ Amount must be greater than 0.")
        return
    
    # Get the price range percentage
    price_range = get_float_input("Enter price range percentage (e.g., 10 for ±10%): ", default=10)
    if price_range <= 0:
        print("❌ Price range must be greater than 0.")
        return
    
    # Get the slippage percentage
    slippage = get_float_input("Enter slippage tolerance percentage: ", default=0.5)
    if slippage <= 0:
        print("❌ Slippage must be greater than 0.")
        return
    
    # Add liquidity to SushiSwap YES pool
    result = bot.add_liquidity_to_yes_pool(gno_amount, sdai_amount, price_range, slippage)
    
    if result:
        print("✅ Successfully added liquidity to SushiSwap YES pool!")
        print(f"Position NFT ID: {result['tokenId']}")
        print(f"Liquidity: {result['liquidity']}")
    else:
        print("❌ Failed to add liquidity to SushiSwap YES pool.")

def add_liquidity_to_sushiswap_no():
    """Add liquidity to the SushiSwap NO pool."""
    print("\n" + "=" * 50)
    print("🏊 ADD LIQUIDITY TO SUSHISWAP NO POOL")
    print("=" * 50)
    
    # Initialize the bot
    bot = initialize_bot()
    if bot is None:
        return
    
    # Get the amount of GNO NO tokens to add
    gno_amount = get_float_input("Enter amount of GNO NO tokens to add: ")
    if gno_amount <= 0:
        print("❌ Amount must be greater than 0.")
        return
    
    # Get the amount of sDAI NO tokens to add
    sdai_amount = get_float_input("Enter amount of sDAI NO tokens to add: ")
    if sdai_amount <= 0:
        print("❌ Amount must be greater than 0.")
        return
    
    # Get the price range percentage
    price_range = get_float_input("Enter price range percentage (e.g., 10 for ±10%): ", default=10)
    if price_range <= 0:
        print("❌ Price range must be greater than 0.")
        return
    
    # Get the slippage percentage
    slippage = get_float_input("Enter slippage tolerance percentage: ", default=0.5)
    if slippage <= 0:
        print("❌ Slippage must be greater than 0.")
        return
    
    # Add liquidity to SushiSwap NO pool
    result = bot.add_liquidity_to_no_pool(gno_amount, sdai_amount, price_range, slippage)
    
    if result:
        print("✅ Successfully added liquidity to SushiSwap NO pool!")
        print(f"Position NFT ID: {result['tokenId']}")
        print(f"Liquidity: {result['liquidity']}")
    else:
        print("❌ Failed to add liquidity to SushiSwap NO pool.")

def view_liquidity_positions():
    """View the user's liquidity positions."""
    print("\n" + "=" * 50)
    print("📋 VIEW LIQUIDITY POSITIONS")
    print("=" * 50)
    
    # Initialize the bot
    bot = initialize_bot()
    if bot is None:
        return
    
    # Get the position ID
    position_id = get_int_input("Enter position NFT ID (or 0 to cancel): ")
    if position_id == 0:
        return
    
    # Get position information
    position_info = bot.get_position_info_v3(position_id)
    
    if position_info:
        print("\n" + "=" * 50)
        print(f"POSITION #{position_info['tokenId']} DETAILS")
        print("=" * 50)
        print(f"Token0: {position_info['token0']['symbol']} ({position_info['token0']['address']})")
        print(f"Token1: {position_info['token1']['symbol']} ({position_info['token1']['address']})")
        print(f"Fee Tier: {position_info['fee'] / 10000}%")
        print(f"Tick Range: {position_info['tickLower']} to {position_info['tickUpper']}")
        print(f"Price Range: {position_info['priceLower']:.6f} to {position_info['priceUpper']:.6f}")
        print(f"Liquidity: {position_info['liquidity']}")
        print(f"Tokens Owed0: {bot.w3.from_wei(position_info['tokensOwed0'], 'ether')}")
        print(f"Tokens Owed1: {bot.w3.from_wei(position_info['tokensOwed1'], 'ether')}")
        print("=" * 50)
    else:
        print("❌ Failed to get position information.")

def collect_fees_from_position():
    """Collect fees from a liquidity position."""
    print("\n" + "=" * 50)
    print("💰 COLLECT FEES FROM POSITION")
    print("=" * 50)
    
    # Initialize the bot
    bot = initialize_bot()
    if bot is None:
        return
    
    # Get the position ID
    position_id = get_int_input("Enter position NFT ID (or 0 to cancel): ")
    if position_id == 0:
        return
    
    # Collect fees
    result = bot.collect_fees_v3(position_id)
    
    if result:
        print("✅ Successfully collected fees!")
        print(f"Amount0: {bot.w3.from_wei(result['amount0'], 'ether')}")
        print(f"Amount1: {bot.w3.from_wei(result['amount1'], 'ether')}")
    else:
        print("❌ Failed to collect fees.")

def increase_liquidity_in_position():
    """Increase liquidity in a position."""
    print("\n" + "=" * 50)
    print("🔄 INCREASE LIQUIDITY IN POSITION")
    print("=" * 50)
    
    # Initialize the bot
    bot = initialize_bot()
    if bot is None:
        return
    
    # Get the position ID
    position_id = get_int_input("Enter position NFT ID (or 0 to cancel): ")
    if position_id == 0:
        return
    
    # Get position information
    position_info = bot.get_position_info_v3(position_id)
    if not position_info:
        print("❌ Failed to get position information.")
        return
    
    print(f"\nPosition #{position_id} uses {position_info['token0']['symbol']} and {position_info['token1']['symbol']}")
    
    # Get the amount of token0 to add
    token0_amount = get_float_input(f"Enter amount of {position_info['token0']['symbol']} to add: ")
    if token0_amount <= 0:
        print("❌ Amount must be greater than 0.")
        return
    
    # Get the amount of token1 to add
    token1_amount = get_float_input(f"Enter amount of {position_info['token1']['symbol']} to add: ")
    if token1_amount <= 0:
        print("❌ Amount must be greater than 0.")
        return
    
    # Get the slippage percentage
    slippage = get_float_input("Enter slippage tolerance percentage: ", default=0.5)
    if slippage <= 0:
        print("❌ Slippage must be greater than 0.")
        return
    
    # Convert to wei
    token0_amount_wei = bot.w3.to_wei(token0_amount, 'ether')
    token1_amount_wei = bot.w3.to_wei(token1_amount, 'ether')
    
    # Increase liquidity
    result = bot.increase_liquidity_v3(position_id, token0_amount_wei, token1_amount_wei, slippage)
    
    if result:
        print("✅ Successfully increased liquidity!")
    else:
        print("❌ Failed to increase liquidity.")

def decrease_liquidity_from_position():
    """Decrease liquidity from a position."""
    print("\n" + "=" * 50)
    print("📉 DECREASE LIQUIDITY FROM POSITION")
    print("=" * 50)
    
    # Initialize the bot
    bot = initialize_bot()
    if bot is None:
        return
    
    # Get the position ID
    position_id = get_int_input("Enter position NFT ID (or 0 to cancel): ")
    if position_id == 0:
        return
    
    # Get the percentage of liquidity to remove
    percentage = get_float_input("Enter percentage of liquidity to remove (1-100): ")
    if percentage <= 0 or percentage > 100:
        print("❌ Percentage must be between 1 and 100.")
        return
    
    # Get the slippage percentage
    slippage = get_float_input("Enter slippage tolerance percentage: ", default=0.5)
    if slippage <= 0:
        print("❌ Slippage must be greater than 0.")
        return
    
    # Decrease liquidity
    result = bot.decrease_liquidity_v3(position_id, percentage, slippage)
    
    if result:
        print("✅ Successfully decreased liquidity!")
        print(f"Liquidity Removed: {result['liquidityRemoved']}")
        print(f"Tokens Owed0: {bot.w3.from_wei(result['tokensOwed0'], 'ether')}")
        print(f"Tokens Owed1: {bot.w3.from_wei(result['tokensOwed1'], 'ether')}")
        
        # Ask if the user wants to collect the tokens
        collect = input("\nDo you want to collect the tokens now? (y/n): ").lower()
        if collect == 'y':
            collect_result = bot.collect_fees_v3(position_id)
            if collect_result:
                print("✅ Successfully collected tokens!")
                print(f"Amount0: {bot.w3.from_wei(collect_result['amount0'], 'ether')}")
                print(f"Amount1: {bot.w3.from_wei(collect_result['amount1'], 'ether')}")
            else:
                print("❌ Failed to collect tokens.")
    else:
        print("❌ Failed to decrease liquidity.")