# Fix Liquidity Addition for Uniswap V3-style Pools

This script provides a robust solution for adding liquidity to Uniswap V3-style pools (including SushiSwap V3) with proper tick alignment and error handling.

## Key Improvements

The script addresses several common issues that can cause liquidity addition transactions to revert:

1. **Proper Tick Alignment**: Ensures ticks are properly aligned with the pool's tick spacing.
2. **Token Order Handling**: Automatically detects and handles token0/token1 ordering.
3. **Decimal Precision**: Correctly handles token decimals for accurate amount calculations.
4. **Allowance Reset**: Resets token allowances to zero before setting new allowances (required by some tokens).
5. **Enhanced Error Handling**: Provides detailed error messages and transaction debugging.
6. **Gas Estimation**: Dynamically adjusts gas limits based on transaction complexity.

## Prerequisites

1. Python 3.7+
2. Required packages (install via `pip install -r requirements.txt`):
   - web3
   - python-dotenv

3. A `.env` file with the following variables:
   ```
   RPC_URL=https://rpc.gnosischain.com  # Or your preferred RPC endpoint
   PRIVATE_KEY=your_private_key_here    # Without 0x prefix
   ```

## Usage

```bash
python fix_liquidity_core.py --token0 0.01 --token1 1.0 --pool 0x9a14d28909f42823ee29847f87a15fb3b6e8aed3 --range 10 --slippage 0.5
```

### Command Line Arguments

- `--token0`: Amount of token0 to add (default: 0.01)
- `--token1`: Amount of token1 to add (default: 1.0)
- `--pool`: Pool address (default: YES pool from CONTRACT_ADDRESSES)
- `--range`: Price range percentage around current price (default: 10.0)
- `--slippage`: Slippage tolerance percentage (default: 0.5)
- `--yes`: Skip confirmation prompt

## Troubleshooting

If your transaction still fails, try the following:

1. **Increase Price Range**: Use a wider price range (e.g., `--range 20`) to ensure your position includes the current price.
2. **Increase Slippage**: If the pool is volatile, increase slippage tolerance (e.g., `--slippage 1.0`).
3. **Check Token Balances**: Ensure you have sufficient token balances.
4. **Check Pool Existence**: Verify that the pool exists and is initialized.
5. **Debug Transaction**: Review the detailed transaction information printed before sending.

## Common Errors

- **"execution reverted"**: This generic error can have multiple causes. The script attempts to provide more context through detailed logging.
- **"tickLower < tickUpper"**: Ensure your price range is positive.
- **"tick not initialized"**: The pool might not be initialized at the specified ticks.
- **"insufficient input amount"**: The amounts provided might not be sufficient for the current price.

## Example

```bash
# Add 0.01 GNO YES and 1.7 sDAI YES to the YES pool with a ±15% price range
python fix_liquidity_core.py --token0 0.01 --token1 1.7 --range 15
```

This will:
1. Connect to the blockchain
2. Get pool information
3. Calculate the appropriate tick range
4. Approve tokens for spending
5. Submit the mint transaction
6. Wait for confirmation and display the result 