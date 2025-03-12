from setuptools import setup, find_packages

setup(
    name="futarchy_trading",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "web3>=6.0.0",
        "eth-account>=0.8.0",
        "python-dotenv>=1.0.0",
        "requests>=2.28.0",
        "eth-utils>=2.1.0",
    ],
    entry_points={
        "console_scripts": [
            "futarchy-bot=futarchy_trading.main:main",
        ],
    },
    author="Futarchy Bot Team",
    author_email="info@example.com",
    description="A trading bot for Gnosis Chain Futarchy markets",
    keywords="blockchain, trading, futarchy, gnosis",
    python_requires=">=3.8",
)
