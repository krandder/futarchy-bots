def probability_threshold_strategy(bot, buy_threshold=0.7, sell_threshold=0.3, amount=0.1):
    """
    Strategy that buys YES tokens when probability exceeds buy_threshold
    and sells YES tokens when probability falls below sell_threshold.
    
    Args:
        bot: FutarchyBot instance
        buy_threshold: Probability threshold to trigger buys
        sell_threshold: Probability threshold to trigger sells
        amount: Amount to trade
        
    Returns:
        bool: Success or failure
    """
    print(f"\n📊 Probability Threshold Strategy")
    print(f"🎯 Buy when probability > {buy_threshold:.2f}, Sell when probability < {sell_threshold:.2f}")
    
    # Get market prices
    prices = bot.get_market_prices()
    if not prices:
        print("❌ Failed to get market prices, cannot execute strategy")
        return False
    
    bot.print_market_prices(prices)
    
    probability = prices['event_probability']
    print(f"📊 Current probability: {probability:.2f}")
    
    # Execute strategy based on probability
    if probability > buy_threshold:
        print(f"🚀 Probability {probability:.2f} exceeds buy threshold {buy_threshold:.2f}")
        print(f"🔄 Buying {amount} YES GNO tokens")
        
        # Buy YES company tokens
        result = bot.execute_swap("company", True, amount, True)
        if result:
            print("✅ Buy successful")
            success = True
        else:
            print("❌ Buy failed")
            success = False
    
    elif probability < sell_threshold:
        print(f"📉 Probability {probability:.2f} below sell threshold {sell_threshold:.2f}")
        print(f"🔄 Selling {amount} YES GNO tokens")
        
        # Sell YES company tokens
        result = bot.execute_swap("company", False, amount, True)
        if result:
            print("✅ Sell successful")
            success = True
        else:
            print("❌ Sell failed")
            success = False
    
    else:
        print(f"⏸️ Probability {probability:.2f} is between thresholds, no action taken")
        success = True  # No action was required
    
    # Get updated balances
    balances = bot.get_balances()
    bot.print_balances(balances)
    
    return success
