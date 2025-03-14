# Debug Scripts

This directory contains scripts for debugging transactions and contracts on the blockchain.

## Scripts

### decode_transaction.py

A utility script to decode transaction data for better understanding of what a transaction is doing.

### debug_mint_transaction.py

A specialized script for debugging mint transactions in Uniswap V3-style pools.

### debug_transaction.py

A general-purpose script for debugging transactions on the blockchain.

## Usage

These scripts are primarily used for troubleshooting and understanding why certain transactions fail or behave unexpectedly.

Example usage:

```bash
# Decode a transaction
python scripts/debug/decode_transaction.py --tx <transaction_hash>

# Debug a mint transaction
python scripts/debug/debug_mint_transaction.py --tx <transaction_hash>

# Debug a general transaction
python scripts/debug/debug_transaction.py --tx <transaction_hash>
```

## Dependencies

These scripts depend on the Web3.py library and require access to a blockchain node. Make sure your `.env` file is properly configured with the RPC URL. 