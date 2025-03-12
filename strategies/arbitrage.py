def arbitrage_strategy(bot, min_difference=0.02, amount=0.1):
    """
    Strategy that looks for arbitrage opportunities between YES and NO tokens.
    
    Args:
        bot: FutarchyBot instance
        min_difference: Minimum price difference to trigger arbitrage
        amount: Amount to trade
        
    Returns:
        bool: Whether arbitrage was executed
    """
    print(f"\n📊 Arbitrage Strategy")
    print(f"🎯 Execute when |YES price - (1 - NO price)| > {min_difference:.2f}")
    
    # Get market prices
    prices = bot.get_market_prices()
    if not prices:
        print("❌ Failed to get market prices, cannot execute strategy")
        return False
    
    bot.print_market_prices(prices)
    
    # Check for arbitrage opportunity
    yes_price = prices['yes_company_price']
    no_price = prices['no_company_price']
    
    # In a perfect market, YES price + NO price should equal 1
    # If not, there's an arbitrage opportunity
    implied_yes_price = 1 - no_price
    price_difference = yes_price - implied_yes_price
    
    print(f"📊 YES price: {yes_price:.4f}, Implied YES price (1-NO): {implied_yes_price:.4f}")
    print(f"📊 Price difference: {price_difference:.4f}")
    
    arbitrage_executed = False
    
    if abs(price_difference) > min_difference:
        print(f"🎯 Arbitrage opportunity detected! Difference: {price_difference:.4f}")
        
        if price_difference > 0:
            # YES is overpriced compared to NO
            print(f"📉 YES is overpriced, selling YES and buying NO")
            
            # Sell YES
            yes_result = bot.execute_swap("company", False, amount, True)
            if yes_result:
                print("✅ Sold YES tokens successfully")
            else:
                print("❌ Failed to sell YES tokens")
                return False
            
            # Buy NO
            no_result = bot.execute_swap("company", True, amount, False)
            if no_result:
                print("✅ Bought NO tokens successfully")
                arbitrage_executed = True
            else:
                print("❌ Failed to buy NO tokens")
                arbitrage_executed = False
        else:
            # NO is overpriced compared to YES
            print(f"📉 NO is overpriced, selling NO and buying YES")
            
            # Sell NO
            no_result = bot.execute_swap("company", False, amount, False)
            if no_result:
                print("✅ Sold NO tokens successfully")
            else:
                print("❌ Failed to sell NO tokens")
                return False
            
            # Buy YES
            yes_result = bot.execute_swap("company", True, amount, True)
            if yes_result:
                print("✅ Bought YES tokens successfully")
                arbitrage_executed = True
            else:
                print("❌ Failed to buy YES tokens")
                arbitrage_executed = False
    else:
        print(f"⏸️ No arbitrage opportunity (difference: {price_difference:.4f} < threshold: {min_difference:.2f})")
    
    # Get updated balances
    balances = bot.get_balances()
    bot.print_balances(balances)
    
    return arbitrage_executed
