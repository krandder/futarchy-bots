# Uninitialized Ticks in Custom Uniswap V3-style Pools

## Overview

This document explains the issue with custom Uniswap V3-style pools where specific ticks are not initialized, and outlines possible solutions.

## The Problem: Uninitialized Ticks

In Uniswap V3-style pools (including SushiSwap V3), liquidity is concentrated within specific price ranges defined by "ticks". For a position to be valid, these ticks must be "initialized" in the pool. When a pool is new or has low liquidity, many ticks may not be initialized yet, which can cause transactions to fail when trying to add liquidity with specific tick boundaries.

When you see an error like:
```
Execution reverted: execution reverted
```

This often means that the ticks you're trying to use as boundaries for your position haven't been initialized yet.

## Our Investigation

We've investigated the YES and NO pools for our futarchy market and found that **none of the ticks are initialized**, including the current tick. This is why our attempts to add liquidity are failing.

Using our `check_ticks.py` script, we found:

```
Checking ticks around current tick:
Tick 51294 (-5 from current): Not Initialized
Tick 51295 (-4 from current): Not Initialized
Tick 51296 (-3 from current): Not Initialized
Tick 51297 (-2 from current): Not Initialized
Tick 51298 (-1 from current): Not Initialized
Tick 51299 (0 from current): Not Initialized
Tick 51300 (1 from current): Not Initialized
Tick 51301 (2 from current): Not Initialized
Tick 51302 (3 from current): Not Initialized
Tick 51303 (4 from current): Not Initialized
Tick 51304 (5 from current): Not Initialized
```

## Possible Solutions

There are several approaches to dealing with uninitialized ticks:

1. **Initialize the ticks first**: Before adding liquidity, we need to initialize the ticks we want to use. This typically requires a separate transaction.

2. **Use a different pool**: If there are other pools with the same token pair that already have initialized ticks, we could use those instead.

3. **Create a new pool**: If the existing pools are not suitable, we could create a new pool with initialized ticks.

4. **Modify the add_liquidity script**: We could modify the `add_liquidity_final.py` script to handle tick initialization as part of the liquidity addition process.

## Next Steps

Based on our findings, we recommend:

1. **Check with the pool creator**: The pool creator may have specific instructions for adding liquidity to these custom pools.

2. **Create a tick initialization script**: We could create a script that initializes specific ticks in the pool before adding liquidity.

3. **Explore alternative approaches**: There may be other ways to interact with these pools that don't require initialized ticks.

## Pool Analysis

We've analyzed both the YES and NO pools for our futarchy market:

### YES Pool (GNO YES / sDAI YES)

- Pool Address: `0x9a14d28909f42823ee29847f87a15fb3b6e8aed3`
- Token0: YES_GNO (`0x177304d505eCA60E1aE0dAF1bba4A4c4181dB8Ad`)
- Token1: YES_sDAI (`0x493A0D1c776f8797297Aa8B34594fBd0A7F8968a`)
- Current Price: 1 YES_GNO = 168.966512 YES_sDAI
- Current Tick: 51299 (Not Initialized)
- Fee: 0.01%
- Tick Spacing: 1

### NO Pool (sDAI NO / GNO NO)

- Pool Address: `0x6E33153115Ab58dab0e0F1E3a2ccda6e67FA5cD7`
- Token0: NO_sDAI (`0xE1133Ef862f3441880adADC2096AB67c63f6E102`)
- Token1: NO_GNO (`0xf1B3E5Ffc0219A4F8C0ac69EC98C97709EdfB6c9`)
- Current Price: 1 NO_sDAI = 0.007022 NO_GNO (or 1 NO_GNO = 142.406694 NO_sDAI)
- Fee: 0.01%
- Tick Spacing: 1

## Using the Check Ticks Script

We've created a script to check if specific ticks are initialized in a pool:

```bash
# Check default ticks in the YES pool
python check_ticks.py

# Check specific ticks
python check_ticks.py --ticks "51299,51300,51301"

# Check ticks in the NO pool
python check_ticks.py --pool 0x6E33153115Ab58dab0e0F1E3a2ccda6e67FA5cD7
```

This script will:
1. Connect to the specified pool
2. Check if the specified ticks are initialized
3. Also check ticks around the current tick

## Conclusion

Adding liquidity to these custom pools is currently not possible using the standard approach because none of the ticks are initialized. We need to either initialize the ticks first or find an alternative approach. 