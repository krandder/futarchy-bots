# Uniswap V3 Scripts

This directory contains scripts for working with Uniswap V3-style pools, particularly for diagnosing and fixing issues with custom pools.

## Scripts

### check_ticks.py

A utility script to check if specific ticks are initialized in a Uniswap V3-style pool. This is particularly useful for diagnosing issues with adding liquidity to custom pools.

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