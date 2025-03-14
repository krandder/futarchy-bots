#!/bin/bash

# Rename files to proper Python conventions
mv config/constants-py.py config/constants.py
mv core/base-bot-py.py core/base_bot.py
mv core/futarchy-bot-py.txt core/futarchy_bot.py
mv exchanges/cowswap-py.py exchanges/cowswap.py
mv exchanges/sushiswap-py.py exchanges/sushiswap.py
mv main-py.py main.py
mv setup-py.py setup.py
mv strategies/strategies-arbitrage.py strategies/arbitrage.py
mv strategies/strategies-monitoring.py strategies/monitoring.py
mv strategies/strategies-probability.py strategies/probability.py
mv utils/utils-helpers.py utils/helpers.py
mv utils/web3-utils-py.py utils/web3_utils.py
mv cli/cli-menu.txt cli/menu.py
mv readme-md.md README.md

# Create __init__.py files in each directory
touch __init__.py
touch config/__init__.py
touch core/__init__.py
touch exchanges/__init__.py
touch strategies/__init__.py
touch utils/__init__.py
touch cli/__init__.py