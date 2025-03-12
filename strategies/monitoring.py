import time

def simple_monitoring_strategy(bot, iterations=5, interval=60):
    """
    Simple strategy that monitors prices and balances.
    
    Args:
        bot: FutarchyBot instance
        iterations: Number of monitoring iterations
        interval: Time between updates in seconds
        
    Returns:
        dict: Final price data
    """
    print("\n📊 Monitoring prices and balances")
    
    # Get initial balances
    balances = bot.get_balances()
    bot.print_balances(balances)
    
    # Get market prices
    prices = bot.get_market_prices()
    if prices:
        bot.print_market_prices(prices)
    else:
        print("❌ Failed to get initial market prices")
        return None
    
    # Monitor for iterations with interval seconds between updates
    for i in range(iterations):
        print(f"\n⏳ Monitoring iteration {i+1}/{iterations}, waiting {interval} seconds...")
        time.sleep(interval)
        
        # Get updated prices and balances
        updated_prices = bot.get_market_prices()
        updated_balances = bot.get_balances()
        
        # Calculate price changes
        if prices and updated_prices:
            prob_change = updated_prices['event_probability'] - prices['event_probability']
            print(f"\n📈 Probability change: {prob_change:.2%}")
            
            yes_price_change = updated_prices['yes_company_price'] - prices['yes_company_price']
            no_price_change = updated_prices['no_company_price'] - prices['no_company_price']
            print(f"📈 YES price change: {yes_price_change:.6f}")
            print(f"📈 NO price change: {no_price_change:.6f}")
            
            # Update for next iteration
            prices = updated_prices
        
        # Print updated balances
        bot.print_balances(updated_balances)
        if updated_prices:
            bot.print_market_prices(updated_prices)
    
    return prices
