# Uniswap V3 Scripts

This directory contains scripts for working with Uniswap V3-style pools, particularly for diagnosing and fixing issues with custom pools.

## New JavaScript Bridge-based Scripts

These scripts use the Uniswap V3 JavaScript bridge to leverage the official Uniswap V3 SDK:

### uniswap_v3_client.py

A Python client for interacting with the Uniswap V3 JavaScript bridge. This client provides methods for:
- Getting pool information
- Checking tick initialization status
- Adding liquidity with full range positions
- Adding liquidity with custom tick ranges

### check_tick_initialization.py

A script to check if specific ticks are initialized in a Uniswap V3 pool. This is particularly useful for diagnosing issues with adding liquidity to custom pools.

Usage:
```bash
# Check ticks around the current tick in the YES pool
python scripts/uniswap_v3/check_tick_initialization.py

# Check specific ticks
python scripts/uniswap_v3/check_tick_initialization.py --ticks "51299,51300,51301"

# Check ticks in a different pool
python scripts/uniswap_v3/check_tick_initialization.py --pool <pool_address>

# Check more ticks around the current tick
python scripts/uniswap_v3/check_tick_initialization.py --range 20
```

### add_full_range_liquidity.py

A script to add liquidity across the full price range (MIN_TICK to MAX_TICK) to a Uniswap V3 pool. This approach works even with uninitialized ticks.

Usage:
```bash
# Add liquidity to the YES pool
python scripts/uniswap_v3/add_full_range_liquidity.py --amount0 1.0 --amount1 1.0

# Add liquidity to a different pool
python scripts/uniswap_v3/add_full_range_liquidity.py --pool <pool_address> --amount0 1.0 --amount1 1.0

# Dry run (do not execute transaction)
python scripts/uniswap_v3/add_full_range_liquidity.py --amount0 1.0 --amount1 1.0 --dry-run
```

## Original Python-only Scripts

These scripts use direct Web3 calls without the Uniswap V3 SDK:

### check_ticks.py

A utility script to check if specific ticks are initialized in a Uniswap V3-style pool.

Usage:
```bash
# Check default ticks in YES pool
python scripts/uniswap_v3/check_ticks.py

# Check specific ticks
python scripts/uniswap_v3/check_ticks.py --ticks "51299,51300,51301"

# Check ticks in a different pool
python scripts/uniswap_v3/check_ticks.py --pool <pool_address>
```

### add_liquidity.py and add_liquidity_final.py

Scripts for adding liquidity to Uniswap V3-style pools. Note that these scripts may fail if the ticks are not initialized.

### check_pool_initialization.py

Checks the initialization status of a Uniswap V3-style pool.

### debug_pool.py and debug_pool_ticks.py

Scripts for debugging issues with Uniswap V3-style pools, particularly focusing on tick initialization and liquidity.

### fix_liquidity_core.py

Core functionality for fixing liquidity issues in Uniswap V3-style pools.

## Documentation

For more detailed documentation, see the files in the `docs/uniswap_v3` directory:

- `uninitialized_ticks.md`: Explains the issue with uninitialized ticks in custom Uniswap V3-style pools
- `README_add_liquidity.md`: Documentation for adding liquidity to Uniswap V3-style pools
- `README_fix_liquidity.md`: Documentation for fixing liquidity issues in Uniswap V3-style pools

## JavaScript Bridge

The JavaScript bridge that these scripts use is located in the `js-bridges/uniswap-v3-bridge` directory. See the README in that directory for more information on how to set up and use the bridge.

## Show All Prices Script (`show_all_prices.py`)

This script displays current prices from three different pools in terms of sDAI per GNO:
1. YES Pool (Uniswap V3)
2. NO Pool (Uniswap V3)
3. Balancer Pool (spot price)

### Usage
```bash
python scripts/uniswap_v3/show_all_prices.py
```

### Output Example
```
YES Pool: 168.966512 sDAI-YES/GNO-YES
NO Pool: 142.406694 sDAI-NO/GNO-NO

Balancer Price Calculation:
1. For 1 sDAI input -> 0.009207 waGNO output
2. Therefore 1 waGNO = 108.612955 sDAI
3. Conversion rate: 1 waGNO = 1.001271 GNO
4. Final price: 108.750958 sDAI/GNO

Balancer: 108.750958 sDAI/GNO
```

### Features
- Displays prices in a consistent format (sDAI per GNO)
- Shows intermediate calculations for Balancer pool price
- Uses contract addresses from configuration files
- Includes error handling for failed queries
- Supports both wrapped and unwrapped GNO tokens 