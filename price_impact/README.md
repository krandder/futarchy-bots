# Price Impact Calculator

This package provides tools for calculating price impact for fixed trade sizes in Balancer and SushiSwap pools.

## Features

- Calculate the GNO to waGNO conversion rate using ERC4626 functions
- Calculate price impact for Balancer pools using eth_call simulation
- Calculate price impact for SushiSwap (Uniswap V3-style) pools using the Quoter contract
- Display current prices and estimated price impacts for trades

## Structure

The package is organized into several modules:

- `config/constants.py`: Contains ABIs and default configuration values
- `utils/web3_utils.py`: Provides Web3 connection and transaction simulation utilities
- `gno_converter.py`: Calculates the GNO to waGNO conversion rate
- `balancer_calculator.py`: Calculates price impact for Balancer pools
- `sushiswap_calculator.py`: Calculates price impact for SushiSwap pools

## Usage

```bash
python price_impact_calculator.py [--amount AMOUNT] [--verbose]
```

### Options

- `--amount AMOUNT`: Trade amount in GNO equivalent (default: 0.01)
- `--verbose, -v`: Enable verbose output
- `--help, -h`: Show help message and exit

## Example

```bash
python price_impact_calculator.py --amount 0.05 --verbose
```

This will calculate the price impact of trading 0.05 GNO in the Balancer sDAI/waGNO pool and SushiSwap conditional token pools.

## Implementation Details

### Balancer Price Impact Calculation

For Balancer pools, we use eth_call to simulate swaps and calculate price impact. This provides accurate results that include fees and slippage.

### SushiSwap Price Impact Calculation

For SushiSwap pools (which use Uniswap V3-style concentrated liquidity), we use the Quoter contract to simulate swaps. If the Quoter contract is not available, we provide estimated price impacts based on trade size.

### GNO to waGNO Conversion

We calculate the GNO to waGNO conversion rate using the ERC4626 standard functions `convertToAssets` and `convertToShares`. If these functions fail, we default to a 1:1 conversion rate. 