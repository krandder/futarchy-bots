# Futarchy Trading Bot

A modular bot for trading on Gnosis Chain futarchy markets with support for GNO/sDAI trading via CoW Swap.

## Features

- Trade between GNO and sDAI using CoW Swap's API
- Split tokens into YES/NO conditional tokens
- Execute trades on futarchy markets using SushiSwap V3
- Convert between xDAI, wxDAI, and sDAI
- Multiple trading strategies
  - Simple monitoring
  - Probability threshold-based trading
  - Arbitrage between YES and NO tokens
- Interactive command-line interface
- Modular, well-structured codebase

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/futarchy-trading.git
cd futarchy-trading
```

2. Install the package:
```
pip install -e .
```

3. Create a `.env` file with your configuration:
```
GNOSIS_RPC_URL=https://rpc.ankr.com/gnosis  # Or your preferred RPC endpoint
PRIVATE_KEY=your_private_key_here           # Without 0x prefix
```

## Usage

### Interactive Mode

Run the bot in interactive mode:

```
python -m futarchy_trading.main
```

Or using the installed command:

```
futarchy-bot
```

### Strategy Modes

Run specific strategies directly:

```
# Monitoring
futarchy-bot monitor --iterations 10 --interval 30

# Probability threshold strategy
futarchy-bot probability --buy 0.75 --sell 0.25 --amount 0.2

# Arbitrage strategy
futarchy-bot arbitrage --diff 0.03 --amount 0.15
```

## Project Structure

```
futarchy_trading/
├── config/
│   └── constants.py         # All constants, addresses, ABIs
├── core/
│   ├── base_bot.py          # Base bot functionality
│   └── futarchy_bot.py      # Main bot implementation
├── utils/
│   ├── web3_utils.py        # Web3 connection, middleware setup
│   └── helpers.py           # Helper functions
├── exchanges/
│   ├── cowswap.py           # CowSwap API integration
│   └── sushiswap.py         # SushiSwap integration
├── strategies/
│   ├── monitoring.py        # Simple monitoring strategy
│   ├── probability.py       # Probability threshold strategy
│   └── arbitrage.py         # Arbitrage strategy
├── cli/
│   └── menu.py              # Interactive CLI menu
└── main.py                  # Entry point
```

## CoW Swap Integration

This bot uses [CoW Swap API](https://docs.cow.fi/cow-protocol/reference/apis/orderbook) to trade between GNO and sDAI tokens. When submitting an order, it:

1. Estimates fee and minimum buy amount
2. Approves the settlement contract to spend tokens
3. Creates and signs the order
4. Submits it to the CoW Swap API
5. Returns the order UID for tracking

Orders on CoW Swap are settled off-chain and may take some time to execute.

## Adding New Strategies

To add a new strategy, create a new file in the `strategies` directory:

```python
# strategies/my_strategy.py

def my_strategy(bot, param1=default1, param2=default2):
    """
    My custom trading strategy.
    
    Args:
        bot: FutarchyBot instance
        param1: First parameter
        param2: Second parameter
        
    Returns:
        bool: Success or failure
    """
    print("Running my custom strategy")
    
    # Strategy implementation
    # ...
    
    return True
```

Then add it to the CLI menu or command-line interface as needed.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
