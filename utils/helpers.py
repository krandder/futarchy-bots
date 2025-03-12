"""Helper utilities for the Futarchy Trading Bot"""

def format_float(value, decimals=6):
    """
    Format a float value with specified number of decimal places.
    
    Args:
        value: Float value to format
        decimals: Number of decimal places
        
    Returns:
        str: Formatted value
    """
    return f"{value:.{decimals}f}"

def format_percentage(value, decimals=2):
    """
    Format a float as percentage.
    
    Args:
        value: Float value to format (0.5 = 50%)
        decimals: Number of decimal places
        
    Returns:
        str: Formatted percentage
    """
    return f"{value * 100:.{decimals}f}%"

def wei_to_ether(wei_value):
    """
    Convert wei to ether (10^18).
    
    Args:
        wei_value: Value in wei
        
    Returns:
        float: Value in ether
    """
    return float(wei_value) / 10**18

def ether_to_wei(ether_value):
    """
    Convert ether to wei.
    
    Args:
        ether_value: Value in ether
        
    Returns:
        int: Value in wei
    """
    return int(float(ether_value) * 10**18)

def safe_float_input(prompt, default=None):
    """
    Safely get a float input from the user.
    
    Args:
        prompt: Prompt to display
        default: Default value if input is empty
        
    Returns:
        float: Parsed input or default value
    """
    while True:
        try:
            user_input = input(prompt)
            if not user_input and default is not None:
                return default
            return float(user_input)
        except ValueError:
            print("Invalid input. Please enter a number.")

def calculate_price_impact(amount, price_before, price_after):
    """
    Calculate the price impact of a trade.
    
    Args:
        amount: Trade amount
        price_before: Price before trade
        price_after: Price after trade
        
    Returns:
        float: Price impact as percentage
    """
    if price_before == 0:
        return 0
    return (price_after - price_before) / price_before

def truncate_address(address, chars=4):
    """
    Truncate an Ethereum address for display.
    
    Args:
        address: Ethereum address
        chars: Number of characters to keep at start and end
        
    Returns:
        str: Truncated address (e.g., 0x1234...5678)
    """
    if not address:
        return ""
    return f"{address[:chars+2]}...{address[-chars:]}"
