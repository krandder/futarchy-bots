# Price Impact Calculator for Futarchy Pools

This script calculates the price impact of trading a fixed amount of GNO (or its waGNO equivalent) in the Balancer sDAI/waGNO pool and SushiSwap conditional token pools.

## Features

- Calculates current prices in three pools:
  - Balancer sDAI/waGNO pool
  - SushiSwap YES conditional pool (GNO YES/sDAI YES)
  - SushiSwap NO conditional pool (sDAI NO/GNO NO)
- Calculates price impact for buying and selling a specified amount of GNO
- Provides detailed information about effective prices after trades
- Includes GNO to waGNO conversion rate

## Usage

```bash
python calculate_price_impact.py [--amount AMOUNT] [--verbose]
```

### Options

- `--amount AMOUNT`: Trade amount in GNO equivalent (default: 0.01)
- `--verbose, -v`: Enable verbose output
- `--help, -h`: Show help message and exit

## Example Output

```
=== Price Impact Summary ===
Trade amount: 0.01 GNO
GNO to waGNO conversion rate: 1.0

Balancer sDAI/waGNO Pool:
  Current price: 1 sDAI = 0.009607212911949973 waGNO
  Buy impact: 0.0000% for 0.01 waGNO
  Sell impact: 0.4997% for 0.01 waGNO

SushiSwap YES Conditional Pool:
  Current price: 1 GNO YES = 168.96651233252754 sDAI YES
  Estimated buy impact: 5-15% (rough estimate)
  Estimated sell impact: 5-15% (rough estimate)

SushiSwap NO Conditional Pool:
  Current price: 1 sDAI NO = 0.007022141798273148 GNO NO
  Estimated buy impact: 5-15% (rough estimate)
  Estimated sell impact: 5-15% (rough estimate)
```

## Notes on Conditional Pools

For Uniswap V3 style pools like SushiSwap, calculating exact price impact requires:
1. Analyzing liquidity distribution across price ticks
2. Simulating the swap through the actual contract
3. Accounting for concentrated liquidity at different price ranges

The script provides rough estimates for these pools. For more accurate calculations, consider:
1. Using on-chain simulation via 'eth_call'
2. Querying the SushiSwap router directly
3. Implementing a full Uniswap V3 SDK for price impact calculation

## Dependencies

- web3.py
- Python 3.6+

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the script: `python calculate_price_impact.py` 