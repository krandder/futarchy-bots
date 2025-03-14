# Uniswap V3 Documentation

This directory contains documentation related to working with Uniswap V3-style pools in the futarchy-bots project.

## Documentation Files

### uninitialized_ticks.md

Comprehensive documentation about the issue with uninitialized ticks in custom Uniswap V3-style pools. This document explains:

- The problem of uninitialized ticks
- Investigation findings
- Possible solutions
- Pool analysis for YES and NO pools
- Script usage for checking tick initialization status

### README_add_liquidity.md

Documentation for adding liquidity to Uniswap V3-style pools, including:

- Prerequisites
- Configuration
- Usage instructions
- Troubleshooting

### README_fix_liquidity.md

Documentation for fixing liquidity issues in Uniswap V3-style pools, including:

- Common problems
- Solutions
- Examples

## Related Scripts

The scripts referenced in this documentation can be found in the `scripts/uniswap_v3` directory:

- `check_ticks.py`: Script for checking if specific ticks are initialized
- `add_liquidity.py` and `add_liquidity_final.py`: Scripts for adding liquidity
- `check_pool_initialization.py`: Script for checking pool initialization
- `debug_pool.py` and `debug_pool_ticks.py`: Scripts for debugging pool issues
- `fix_liquidity_core.py`: Core functionality for fixing liquidity issues 