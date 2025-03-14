# Futarchy Bots

A collection of tools for interacting with futarchy markets on Gnosis Chain.

## Tools

### Price Impact Calculator

A tool for calculating the price impact of trades in various pools:

- Balancer sDAI/waGNO pool
- SushiSwap YES conditional pool
- SushiSwap NO conditional pool

The calculator provides accurate price impact calculations for different trade sizes, helping traders make informed decisions.

### SushiSwap V3 Liquidity Provider

A tool for adding and managing concentrated liquidity positions in SushiSwap V3 pools:

- Create new concentrated liquidity positions with custom price ranges
- Increase liquidity in existing positions
- Decrease liquidity from positions
- Collect accumulated fees
- View detailed position information

This functionality allows users to provide liquidity to the YES and NO markets with greater capital efficiency.

## Usage

### Price Impact Calculator

```bash
python price_impact_calculator.py --amount 0.1
```

Options:
- `--amount`: Amount of GNO to calculate price impact for (default: 0.01)

### SushiSwap V3 Liquidity Provider

The liquidity provider functionality is integrated into the main futarchy bot and can be accessed through the CLI menu.

## Requirements

- Python 3.8+
- Web3.py
- Eth-account
- Python-dotenv
- Other dependencies listed in requirements.txt

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/futarchy-bots.git
cd futarchy-bots
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your configuration:
```
PRIVATE_KEY=your_private_key_here
RPC_URL=your_rpc_url_here
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This software is provided for educational and research purposes only. Use at your own risk. The authors are not responsible for any financial losses incurred through the use of these tools.
