# Add Liquidity to SushiSwap V3 Pools

This script provides a streamlined solution for adding liquidity to SushiSwap V3 pools on Gnosis Chain, specifically designed for the futarchy prediction market pools.

## Key Features

- Automatically detects pool parameters (fee, tick spacing)
- Properly calculates tick ranges based on desired price range
- Handles token approvals
- Provides detailed transaction information for debugging
- Includes balance checks and user confirmation

## Prerequisites

1. Python 3.7+
2. Required packages:
   ```
   pip install web3 python-dotenv
   ```

3. A `.env` file with:
   ```
   RPC_URL=https://rpc.gnosischain.com
   PRIVATE_KEY=your_private_key_here  # Without 0x prefix
   ```

## Usage

```bash
python add_liquidity_final.py --token0 0.01 --token1 1.0 --pool 0x9a14d28909f42823ee29847f87a15fb3b6e8aed3 --range 10 --slippage 0.5
```

### Command Line Arguments

- `--token0`: Amount of token0 to add (default: 0.01)
- `--token1`: Amount of token1 to add (default: 1.0)
- `--pool`: Pool address (default: YES pool from CONTRACT_ADDRESSES)
- `--range`: Price range percentage around current price (default: 10.0)
- `--slippage`: Slippage tolerance percentage (default: 0.5)
- `--yes`: Skip confirmation prompt

## Example: Adding Liquidity to the YES Pool

The YES pool contains GNO YES and sDAI YES tokens. To add liquidity:

```bash
python add_liquidity_final.py --token0 0.01 --token1 1.7 --range 15
```

This will:
1. Add 0.01 GNO YES and 1.7 sDAI YES to the pool
2. Set a price range of ±15% around the current price
3. Use the default slippage tolerance of 0.5%

## Troubleshooting

If your transaction fails, try:

1. **Increase the price range**: Use a wider range (e.g., `--range 20`) to ensure your position includes the current price.
2. **Increase slippage tolerance**: If the pool is volatile, try `--slippage 1.0`.
3. **Check token balances**: Ensure you have sufficient tokens.
4. **Verify token approvals**: The script handles this, but you can check manually.

## Pool Information

The script automatically fetches and displays important pool information:
- Current tick
- Tick spacing
- Fee tier
- Token addresses and symbols

This information helps ensure your liquidity position is created correctly.

## Notes

- The script uses a high gas limit (3,000,000) to ensure the transaction has enough gas to complete.
- Token amounts are converted to the appropriate decimals automatically.
- The script calculates the appropriate tick range based on the pool's tick spacing. 