# Futarchy Bots

A collection of trading bots for interacting with Futarchy markets on Gnosis Chain.

## Project Structure

```
futarchy-bots/
├── core/                  # Core bot functionality
│   └── futarchy_bot.py    # Main bot class
├── exchanges/             # Exchange-specific implementations
│   ├── aave/              # AAVE lending protocol integration
│   └── balancer/          # Balancer DEX integration
│       ├── permit2.py     # Permit2 authorization handler
│       └── swap.py        # Balancer swap handler
├── scripts/               # Utility scripts
│   └── debug/             # Debugging tools
├── config/                # Configuration files
│   └── constants.py       # Contract addresses and constants
├── menu.py                # Interactive CLI menu
└── README.md              # This file
```

## Features

- **Permit2 Integration**: Efficient token approvals using Uniswap's Permit2 protocol
- **Balancer Swaps**: Execute token swaps on Balancer pools
- **Interactive Menu**: User-friendly command-line interface
- **Balance Tracking**: Automatic balance refreshing and display
- **Error Handling**: Comprehensive error handling and debugging

## Prerequisites

- Python 3.8+
- Web3.py
- Private key with access to tokens on Gnosis Chain
- RPC endpoint for Gnosis Chain
- XDAI for gas fees (native currency on Gnosis Chain)

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/futarchy-bots.git
cd futarchy-bots
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your configuration:
```
PRIVATE_KEY=your_private_key_here
RPC_URL=https://gnosis-mainnet.public.blastapi.io
```

## Usage

### Interactive Menu

Run the interactive menu to access all bot functions:

```bash
python menu.py
```

Add the `--verbose` flag for detailed debug information:

```bash
python menu.py --verbose
```

### Menu Options

1. **Refresh Balances**: View current token balances (sDAI, waGNO, XDAI)
2. **Check Permit2 Status**: Check current Permit2 authorizations
3. **Approve sDAI for Permit2**: Approve sDAI to be used with Permit2
4. **Create Permit for BatchRouter**: Create a Permit2 authorization for the BatchRouter
5. **Swap sDAI to waGNO**: Execute a swap from sDAI to waGNO
6. **Swap waGNO to sDAI**: Execute a swap from waGNO to sDAI

## Permit2 Workflow

1. Approve tokens for Permit2 (one-time setup)
2. Create a permit for a specific spender (e.g., BatchRouter)
3. Execute transactions through the spender without additional approvals

## Development

### Adding New Exchange Integrations

1. Create a new directory under `exchanges/`
2. Implement the necessary handler classes
3. Update the menu system to include the new functionality

### Configuration

Edit `config/constants.py` to update contract addresses and other constants.

## License

[MIT License](LICENSE)

## Acknowledgements

- [Uniswap Permit2](https://github.com/Uniswap/permit2)
- [Balancer Protocol](https://balancer.fi/)
- [Web3.py](https://web3py.readthedocs.io/)
