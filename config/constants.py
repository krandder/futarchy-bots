# Constants, contract addresses, and ABIs for the Futarchy Trading Bot

# API Endpoints
COWSWAP_API_URL = "https://api.cow.fi/xdai"  # Gnosis Chain (Production)

# Contract addresses
CONTRACT_ADDRESSES = {
    "futarchyRouter": "0x7495a583ba85875d59407781b4958ED6e0E1228f",
    "sushiswap": "0x592abc3734cd0d458e6e44a2db2992a3d00283a4",
    "market": "0x6242AbA055957A63d682e9D3de3364ACB53D053A",
    "conditionalTokens": "0xCeAfDD6bc0bEF976fdCd1112955828E00543c0Ce",
    "wrapperService": "0xc14f5d2B9d6945EF1BA93f8dB20294b90FA5b5b1",
    "vaultRelayer": "0xC92E8bdf79f0507f65a392b0ab4667716BFE0110",
    "cowSettlement": "0x9008D19f58AAbD9eD0D60971565AA8510560ab41",
    "baseCurrencyToken": "0xaf204776c7245bF4147c2612BF6e5972Ee483701",  # SDAI
    "baseCompanyToken": "0x9C58BAcC331c9aa871AFD802DB6379a98e80CEdb",  # GNO
    "currencyYesToken": "0x493A0D1c776f8797297Aa8B34594fBd0A7F8968a",
    "currencyNoToken": "0xE1133Ef862f3441880adADC2096AB67c63f6E102",
    "companyYesToken": "0x177304d505eCA60E1aE0dAF1bba4A4c4181dB8Ad",
    "companyNoToken": "0xf1B3E5Ffc0219A4F8C0ac69EC98C97709EdfB6c9",
    "poolYes": "0x9a14d28909f42823ee29847f87a15fb3b6e8aed3",
    "poolNo": "0x6E33153115Ab58dab0e0F1E3a2ccda6e67FA5cD7",
    "sdaiRateProvider": "0x89C80A4540A00b5270347E02e2E144c71da2EceD",
    "wxdai": "0xe91D153E0b41518A2Ce8Dd3D7944Fa863463a97d",
    "permit2": "0x000000000022D473030F116dDEE9F6B43aC78BA3",
    "batchRouter": "0xe2fa4e1d17725e72dcdAfe943Ecf45dF4B9E285b",
    "balancerVault": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
    "balancerPool": "0xd1d7fa8871d84d0e77020fc28b7cd5718c446522",
    "wagno": "0x7c16f0185a26db0ae7a9377f23bc18ea7ce5d644",
    "sushiswapNFPM": "0xaB235da7f52d35fb4551AfBa11BFB56e18774A65",  # SushiSwap V3 NonFungiblePositionManager
}

# Pool configurations
POOL_CONFIG_YES = {
    "address": "0x9a14d28909f42823ee29847f87a15fb3b6e8aed3",
    "tokenCompanySlot": 0
}

POOL_CONFIG_NO = {
    "address": "0x6E33153115Ab58dab0e0F1E3a2ccda6e67FA5cD7",
    "tokenCompanySlot": 1
}

# Token configurations
TOKEN_CONFIG = {
    "currency": {
        "name": "SDAI",
        "address": "0xaf204776c7245bF4147c2612BF6e5972Ee483701",
        "decimals": 18,
        "yes_address": "0x493A0D1c776f8797297Aa8B34594fBd0A7F8968a",
        "no_address": "0xE1133Ef862f3441880adADC2096AB67c63f6E102"
    },
    "company": {
        "name": "GNO",
        "address": "0x9C58BAcC331c9aa871AFD802DB6379a98e80CEdb",
        "decimals": 18,
        "yes_address": "0x177304d505eCA60E1aE0dAF1bba4A4c4181dB8Ad",
        "no_address": "0xf1B3E5Ffc0219A4F8C0ac69EC98C97709EdfB6c9"
    },
    "wagno": {
        "name": "waGNO",
        "address": "0x7c16f0185a26db0ae7a9377f23bc18ea7ce5d644",
        "decimals": 18
    }
}

# Balancer configurations
BALANCER_CONFIG = {
    "vault_address": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
    "pool_address": "0xd1d7fa8871d84d0e77020fc28b7cd5718c446522",
    "pool_id": "0xd1d7fa8871d84d0e77020fc28b7cd5718c4465220000000000000000000001d7"
}

# Default swap configuration
DEFAULT_SWAP_CONFIG = {
    "amount_to_swap": 100000000000000,  # 0.0001 tokens with 18 decimals
    "slippage_percentage": 0.5,  # 0.5% slippage
}

# Default permit configuration
DEFAULT_PERMIT_CONFIG = {
    "amount": 1000000000000000,  # 0.001 tokens with 18 decimals
    "expiration_hours": 24,
    "sig_deadline_hours": 1
}

# Min and max sqrt ratios for Uniswap V3 style pools
MIN_SQRT_RATIO = 4295128739
MAX_SQRT_RATIO = 1461446703485210103287273052203988822378723970342

# Contract ABIs
ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": False, "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "payable": False, "stateMutability": "nonpayable", "type": "function"},
    {"constant": True, "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "payable": False, "stateMutability": "view", "type": "function"}
]

UNISWAP_V3_POOL_ABI = [
    {"inputs": [], "name": "token0", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "token1", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "slot0", "outputs": [{"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"}, {"internalType": "int24", "name": "tick", "type": "int24"}, {"internalType": "uint16", "name": "observationIndex", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"}, {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"}, {"internalType": "bool", "name": "unlocked", "type": "bool"}], "stateMutability": "view", "type": "function"}
]

SUSHISWAP_V3_ROUTER_ABI = [
    {"inputs": [{"internalType": "address", "name": "pool", "type": "address"}, {"internalType": "address", "name": "recipient", "type": "address"}, {"internalType": "bool", "name": "zeroForOne", "type": "bool"}, {"internalType": "int256", "name": "amountSpecified", "type": "int256"}, {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}, {"internalType": "bytes", "name": "data", "type": "bytes"}], "name": "swap", "outputs": [{"internalType": "int256", "name": "", "type": "int256"}, {"internalType": "int256", "name": "", "type": "int256"}], "stateMutability": "nonpayable", "type": "function"}
]

# SushiSwap V3 NonFungiblePositionManager ABI
SUSHISWAP_V3_NFPM_ABI = [
    {"inputs": [{"internalType": "address", "name": "token0", "type": "address"}, {"internalType": "address", "name": "token1", "type": "address"}, {"internalType": "uint24", "name": "fee", "type": "uint24"}, {"internalType": "int24", "name": "tickLower", "type": "int24"}, {"internalType": "int24", "name": "tickUpper", "type": "int24"}, {"internalType": "uint256", "name": "amount0Desired", "type": "uint256"}, {"internalType": "uint256", "name": "amount1Desired", "type": "uint256"}, {"internalType": "uint256", "name": "amount0Min", "type": "uint256"}, {"internalType": "uint256", "name": "amount1Min", "type": "uint256"}, {"internalType": "address", "name": "recipient", "type": "address"}, {"internalType": "uint256", "name": "deadline", "type": "uint256"}], "name": "mint", "outputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}, {"internalType": "uint128", "name": "liquidity", "type": "uint128"}, {"internalType": "uint256", "name": "amount0", "type": "uint256"}, {"internalType": "uint256", "name": "amount1", "type": "uint256"}], "stateMutability": "payable", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}, {"internalType": "uint256", "name": "amount0Desired", "type": "uint256"}, {"internalType": "uint256", "name": "amount1Desired", "type": "uint256"}, {"internalType": "uint256", "name": "amount0Min", "type": "uint256"}, {"internalType": "uint256", "name": "amount1Min", "type": "uint256"}, {"internalType": "uint256", "name": "deadline", "type": "uint256"}], "name": "increaseLiquidity", "outputs": [{"internalType": "uint128", "name": "liquidity", "type": "uint128"}, {"internalType": "uint256", "name": "amount0", "type": "uint256"}, {"internalType": "uint256", "name": "amount1", "type": "uint256"}], "stateMutability": "payable", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}, {"internalType": "uint128", "name": "liquidity", "type": "uint128"}, {"internalType": "uint256", "name": "amount0Min", "type": "uint256"}, {"internalType": "uint256", "name": "amount1Min", "type": "uint256"}, {"internalType": "uint256", "name": "deadline", "type": "uint256"}], "name": "decreaseLiquidity", "outputs": [{"internalType": "uint256", "name": "amount0", "type": "uint256"}, {"internalType": "uint256", "name": "amount1", "type": "uint256"}], "stateMutability": "payable", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}, {"internalType": "address", "name": "recipient", "type": "address"}, {"internalType": "uint128", "name": "amount0Max", "type": "uint128"}, {"internalType": "uint128", "name": "amount1Max", "type": "uint128"}], "name": "collect", "outputs": [{"internalType": "uint256", "name": "amount0", "type": "uint256"}, {"internalType": "uint256", "name": "amount1", "type": "uint256"}], "stateMutability": "payable", "type": "function"},
    {"inputs": [{"internalType": "address", "name": "token0", "type": "address"}, {"internalType": "address", "name": "token1", "type": "address"}, {"internalType": "uint24", "name": "fee", "type": "uint24"}], "name": "createAndInitializePoolIfNecessary", "outputs": [{"internalType": "address", "name": "pool", "type": "address"}], "stateMutability": "payable", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}], "name": "positions", "outputs": [{"internalType": "uint96", "name": "nonce", "type": "uint96"}, {"internalType": "address", "name": "operator", "type": "address"}, {"internalType": "address", "name": "token0", "type": "address"}, {"internalType": "address", "name": "token1", "type": "address"}, {"internalType": "uint24", "name": "fee", "type": "uint24"}, {"internalType": "int24", "name": "tickLower", "type": "int24"}, {"internalType": "int24", "name": "tickUpper", "type": "int24"}, {"internalType": "uint128", "name": "liquidity", "type": "uint128"}, {"internalType": "uint256", "name": "feeGrowthInside0LastX128", "type": "uint256"}, {"internalType": "uint256", "name": "feeGrowthInside1LastX128", "type": "uint256"}, {"internalType": "uint128", "name": "tokensOwed0", "type": "uint128"}, {"internalType": "uint128", "name": "tokensOwed1", "type": "uint128"}], "stateMutability": "view", "type": "function"}
]

FUTARCHY_ROUTER_ABI = [
    {"inputs": [{"internalType": "contract FutarchyProposal", "name": "proposal", "type": "address"}, {"internalType": "contract IERC20", "name": "collateralToken", "type": "address"}, {"internalType": "uint256", "name": "amount", "type": "uint256"}], "name": "splitPosition", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"internalType": "contract FutarchyProposal", "name": "proposal", "type": "address"}, {"internalType": "contract IERC20", "name": "collateralToken", "type": "address"}, {"internalType": "uint256", "name": "amount", "type": "uint256"}], "name": "mergePositions", "outputs": [], "stateMutability": "nonpayable", "type": "function"}
]

SDAI_RATE_PROVIDER_ABI = [
    {"inputs": [], "name": "getRate", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}
]

WXDAI_ABI = [
    {"constant": False, "inputs": [], "name": "deposit", "outputs": [], "payable": True, "stateMutability": "payable", "type": "function"},
    {"constant": True, "inputs": [{"name": "", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": False, "inputs": [{"name": "guy", "type": "address"}, {"name": "wad", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "payable": False, "stateMutability": "nonpayable", "type": "function"}
]

SDAI_DEPOSIT_ABI = [
    {"inputs":[{"internalType":"uint256","name":"assets","type":"uint256"},{"internalType":"address","name":"receiver","type":"address"}],"name":"deposit","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"}
]

# ABIs for Balancer and Aave contracts
BALANCER_VAULT_ABI = [
    {"inputs":[{"components":[{"internalType":"bytes32","name":"poolId","type":"bytes32"},{"internalType":"address","name":"assetIn","type":"address"},{"internalType":"address","name":"assetOut","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"bytes","name":"userData","type":"bytes"}],"internalType":"struct IVault.SingleSwap","name":"singleSwap","type":"tuple"},{"components":[{"internalType":"address","name":"sender","type":"address"},{"internalType":"bool","name":"fromInternalBalance","type":"bool"},{"internalType":"address payable","name":"recipient","type":"address"},{"internalType":"bool","name":"toInternalBalance","type":"bool"}],"internalType":"struct IVault.FundManagement","name":"funds","type":"tuple"},{"internalType":"uint256","name":"limit","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swap","outputs":[{"internalType":"uint256","name":"amountCalculated","type":"uint256"}],"stateMutability":"payable","type":"function"},
    {"inputs":[{"internalType":"bytes32","name":"poolId","type":"bytes32"}],"name":"getPoolTokens","outputs":[{"internalType":"address[]","name":"tokens","type":"address[]"},{"internalType":"uint256[]","name":"balances","type":"uint256[]"},{"internalType":"uint256","name":"lastChangeBlock","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"bytes32","name":"poolId","type":"bytes32"},{"internalType":"address","name":"tokenIn","type":"address"},{"internalType":"address","name":"tokenOut","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"querySwap","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"}
]

BALANCER_POOL_ABI = [
    {"inputs":[],"name":"getPoolId","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"}
]

BALANCER_BATCH_ROUTER_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {
                        "internalType": "contract IERC20",
                        "name": "tokenIn",
                        "type": "address"
                    },
                    {
                        "components": [
                            {
                                "internalType": "address",
                                "name": "pool",
                                "type": "address"
                            },
                            {
                                "internalType": "contract IERC20",
                                "name": "tokenOut",
                                "type": "address"
                            },
                            {
                                "internalType": "bool",
                                "name": "isBuffer",
                                "type": "bool"
                            }
                        ],
                        "internalType": "struct IBatchRouter.SwapPathStep[]",
                        "name": "steps",
                        "type": "tuple[]"
                    },
                    {
                        "internalType": "uint256",
                        "name": "exactAmountIn",
                        "type": "uint256"
                    },
                    {
                        "internalType": "uint256",
                        "name": "minAmountOut",
                        "type": "uint256"
                    }
                ],
                "internalType": "struct IBatchRouter.SwapPathExactAmountIn[]",
                "name": "paths",
                "type": "tuple[]"
            },
            {
                "internalType": "uint256",
                "name": "deadline",
                "type": "uint256"
            },
            {
                "internalType": "bool",
                "name": "wethIsEth",
                "type": "bool"
            },
            {
                "internalType": "bytes",
                "name": "userData",
                "type": "bytes"
            }
        ],
        "name": "swapExactIn",
        "outputs": [
            {
                "internalType": "uint256[]",
                "name": "pathAmountsOut",
                "type": "uint256[]"
            },
            {
                "internalType": "address[]",
                "name": "tokensOut",
                "type": "address[]"
            },
            {
                "internalType": "uint256[]",
                "name": "amountsOut",
                "type": "uint256[]"
            }
        ],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "components": [
                    {
                        "internalType": "contract IERC20",
                        "name": "tokenIn",
                        "type": "address"
                    },
                    {
                        "components": [
                            {
                                "internalType": "address",
                                "name": "pool",
                                "type": "address"
                            },
                            {
                                "internalType": "contract IERC20",
                                "name": "tokenOut",
                                "type": "address"
                            },
                            {
                                "internalType": "bool",
                                "name": "isBuffer",
                                "type": "bool"
                            }
                        ],
                        "internalType": "struct IBatchRouter.SwapPathStep[]",
                        "name": "steps",
                        "type": "tuple[]"
                    },
                    {
                        "internalType": "uint256",
                        "name": "exactAmountIn",
                        "type": "uint256"
                    },
                    {
                        "internalType": "uint256",
                        "name": "minAmountOut",
                        "type": "uint256"
                    }
                ],
                "internalType": "struct IBatchRouter.SwapPathExactAmountIn[]",
                "name": "paths",
                "type": "tuple[]"
            },
            {
                "internalType": "address",
                "name": "sender",
                "type": "address"
            },
            {
                "internalType": "bytes",
                "name": "userData",
                "type": "bytes"
            }
        ],
        "name": "querySwapExactIn",
        "outputs": [
            {
                "internalType": "uint256[]",
                "name": "pathAmountsOut",
                "type": "uint256[]"
            },
            {
                "internalType": "address[]",
                "name": "tokensOut",
                "type": "address[]"
            },
            {
                "internalType": "uint256[]",
                "name": "amountsOut",
                "type": "uint256[]"
            }
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

WAGNO_ABI = [
    {"inputs":[{"name":"assets","type":"uint256"},{"name":"receiver","type":"address"}],"name":"deposit","outputs":[{"name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"shares","type":"uint256"},{"name":"receiver","type":"address"},{"name":"owner","type":"address"}],"name":"redeem","outputs":[{"name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"}
]

PERMIT2_ABI = [
    {
        "inputs": [
            {"name": "owner", "type": "address"},
            {
                "components": [
                    {
                        "components": [
                            {"name": "token", "type": "address"},
                            {"name": "amount", "type": "uint160"},
                            {"name": "expiration", "type": "uint48"},
                            {"name": "nonce", "type": "uint48"}
                        ],
                        "name": "details",
                        "type": "tuple"
                    },
                    {"name": "spender", "type": "address"},
                    {"name": "sigDeadline", "type": "uint256"}
                ],
                "name": "permitSingle",
                "type": "tuple"
            },
            {"name": "signature", "type": "bytes"}
        ],
        "name": "permit",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "from", "type": "address"},
            {"name": "to", "type": "address"},
            {"name": "amount", "type": "uint160"},
            {"name": "token", "type": "address"}
        ],
        "name": "transferFrom",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "owner", "type": "address"}
        ],
        "name": "nonces",
        "outputs": [
            {"name": "", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "DOMAIN_SEPARATOR",
        "outputs": [
            {"name": "", "type": "bytes32"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "components": [
                    {"name": "token", "type": "address"},
                    {"name": "amount", "type": "uint160"},
                    {"name": "expiration", "type": "uint48"},
                    {"name": "nonce", "type": "uint48"}
                ],
                "name": "details",
                "type": "tuple"
            },
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [
            {
                "components": [
                    {"name": "amount", "type": "uint160"},
                    {"name": "expiration", "type": "uint48"},
                    {"name": "nonce", "type": "uint48"}
                ],
                "name": "",
                "type": "tuple"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "token", "type": "address"},
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint160"},
            {"name": "expiration", "type": "uint48"}
        ],
        "name": "approve",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]