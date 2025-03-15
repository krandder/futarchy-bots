# Uniswap V3 Bridge

This bridge provides a REST API that exposes Uniswap V3 SDK functionality to Python applications. It allows you to interact with Uniswap V3 pools, check tick initialization status, and add liquidity without having to reimplement the complex logic in Python.

## Features

- Get pool information (tokens, fee, current tick, etc.)
- Check if specific ticks are initialized
- Add liquidity with full range positions (MIN_TICK to MAX_TICK)
- Add liquidity with custom tick ranges

## Installation

1. Make sure you have Node.js installed (v14 or later recommended)
2. Clone this repository
3. Install dependencies:

```bash
cd js-bridges/uniswap-v3-bridge
npm install
```

4. Copy the `.env.example` file to `.env` and configure it:

```bash
cp .env.example .env
```

5. Edit the `.env` file to set your RPC URL and other configuration options

## Usage

### Starting the Bridge Server

```bash
npm start
```

Or for development with auto-restart:

```bash
npm run dev
```

### API Endpoints

#### GET /api/pool/:poolAddress

Get information about a Uniswap V3 pool.

Example response:
```json
{
  "token0": {
    "address": "0xaf204776c7245bF4147c2612BF6e5972Ee483701",
    "symbol": "sDAI",
    "decimals": 18
  },
  "token1": {
    "address": "0x493A0D1c776f8797297Aa8B34594fBd0A7F8968a",
    "symbol": "sDAI-YES",
    "decimals": 18
  },
  "fee": 3000,
  "tickSpacing": 60,
  "liquidity": "1234567890",
  "sqrtPriceX96": "1234567890123456789012345",
  "tick": 51299
}
```

#### POST /api/check-ticks

Check if specific ticks are initialized in a pool.

Request body:
```json
{
  "poolAddress": "0x9a14d28909f42823ee29847f87a15fb3b6e8aed3",
  "ticks": [51240, 51300, 51360]
}
```

Example response:
```json
{
  "poolAddress": "0x9a14d28909f42823ee29847f87a15fb3b6e8aed3",
  "currentTick": 51299,
  "tickSpacing": 60,
  "results": {
    "51240": false,
    "51300": false,
    "51360": false,
    "51299": false
  }
}
```

#### POST /api/add-full-range-liquidity

Add liquidity across the full price range (MIN_TICK to MAX_TICK).

Request body:
```json
{
  "poolAddress": "0x9a14d28909f42823ee29847f87a15fb3b6e8aed3",
  "amount0": "1.0",
  "amount1": "1.0"
}
```

Example response:
```json
{
  "transactionHash": "0x123...",
  "position": {
    "token0": "sDAI",
    "token1": "sDAI-YES",
    "fee": 3000,
    "tickLower": -887272,
    "tickUpper": 887272,
    "amount0": "1.0",
    "amount1": "1.0"
  }
}
```

#### POST /api/add-liquidity

Add liquidity within a specific tick range.

Request body:
```json
{
  "poolAddress": "0x9a14d28909f42823ee29847f87a15fb3b6e8aed3",
  "tickLower": 51240,
  "tickUpper": 51360,
  "amount0": "1.0",
  "amount1": "1.0"
}
```

Example response:
```json
{
  "transactionHash": "0x123...",
  "position": {
    "token0": "sDAI",
    "token1": "sDAI-YES",
    "fee": 3000,
    "tickLower": 51240,
    "tickUpper": 51360,
    "amount0": "1.0",
    "amount1": "1.0"
  }
}
```

## Python Client

A Python client for this bridge is available in the `scripts/uniswap_v3` directory. See the `uniswap_v3_client.py` file for details.

## Troubleshooting

- Make sure your RPC URL is correct and accessible
- If you're using a private key for transactions, ensure it has sufficient funds
- Check that the Uniswap V3 contract addresses in the `.env` file are correct for your network

## License

MIT 