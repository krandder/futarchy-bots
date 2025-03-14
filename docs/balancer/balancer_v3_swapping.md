# Balancer V3 Swapping with Custom Paths

This guide explains how to execute swaps through the Balancer V3 Router using custom paths. It covers both single and multi-path swap types, focusing on exactIn swaps.

## Core Concepts

- The sender must approve the **Vault** (not the Router) for each swap input token
- For V3 swaps, **Permit2** approvals are required (this is a key difference from V2)
- Token amount inputs/outputs are always in the raw token scale (e.g., 1 USDC should be sent as 1000000 because it has 6 decimals)
- Transactions are always sent to the Router
- Two swap kinds:
  - **ExactIn**: User provides an exact input token amount
  - **ExactOut**: User provides an exact output token amount
- Two swap subsets:
  - **Single Swap**: A swap (tokenIn > tokenOut) using a single pool (most gas efficient)
  - **Multi-path Swaps**: Swaps involving multiple paths executed in the same transaction

## Implementation Options

### 1. Using the Balancer SDK with Permit2 (Recommended for V3)

For Balancer V3, the recommended approach is to use the SDK with Permit2 for token approvals:

```javascript
import {
    Slippage,
    SwapKind,
    PERMIT2,
    TokenAmount,
    ChainId,
    Permit2Helper,
    SwapBuildCallInput,
    erc20Abi,
} from '@balancer/sdk';
import { parseUnits, parseEventLogs } from 'viem';

const swapV3 = async () => {
    // Setup client and user account
    const chainId = ChainId.SEPOLIA;
    const { client, rpcUrl, userAccount } = await setupExampleFork({ chainId });

    // Query swap results before sending transaction
    const { swap, queryOutput } = await queryCustomPath({
        rpcUrl,
        chainId,
        pools: [POOLS[chainId].MOCK_WETH_BAL_POOL.id],
        tokenIn: {
            address: TOKENS[chainId].WETH.address,
            decimals: TOKENS[chainId].WETH.decimals,
        },
        tokenOut: {
            address: TOKENS[chainId].BAL.address,
            decimals: TOKENS[chainId].BAL.decimals,
        },
        swapKind: SwapKind.GivenIn,
        protocolVersion: 3,
        inputAmountRaw: parseUnits('0.01', TOKENS[chainId].WETH.decimals),
        outputAmountRaw: parseUnits('1', TOKENS[chainId].BAL.decimals),
    });

    // Amount of tokenIn depends on swapKind
    let tokenIn;
    if (queryOutput.swapKind === SwapKind.GivenIn) {
        tokenIn = queryOutput.amountIn;
    } else {
        tokenIn = queryOutput.expectedAmountIn;
    }

    // Approve Permit2 contract as spender of tokenIn
    await approveSpenderOnToken(
        client,
        userAccount,
        tokenIn.token.address,
        PERMIT2[chainId],
    );

    // User defines the following params for sending swap transaction
    const sender = userAccount;
    const recipient = userAccount;
    const slippage = Slippage.fromPercentage('0.1');
    const deadline = 999999999999999999n; // Infinity
    const wethIsEth = false;

    const swapBuildCallInput = {
        sender,
        recipient,
        slippage,
        deadline,
        wethIsEth,
        queryOutput,
    };

    // Use signature to permit2 approve transfer of tokens to Balancer's canonical Router
    const signedPermit2Batch = await Permit2Helper.signSwapApproval({
        ...swapBuildCallInput,
        client,
        owner: sender,
    });

    // Build call with Permit2 signature
    const swapCall = swap.buildCallWithPermit2(
        swapBuildCallInput,
        signedPermit2Batch,
    );

    // Send the transaction
    const hash = await client.sendTransaction({
        account: userAccount,
        data: swapCall.callData,
        to: swapCall.to,
        value: swapCall.value,
    });

    // Wait for and process the transaction receipt
    const txReceipt = await client.waitForTransactionReceipt({ hash });
};
```

### 2. Using the Balancer SDK (Without Permit2)

The Balancer SDK provides functionality to easily fetch updated swap quotes and create swap transactions with user-defined slippage protection.

```javascript
import {
  ChainId,
  Slippage,
  SwapKind,
  Swap,
  SwapBuildOutputExactIn,
  ExactInQueryOutput
} from "@balancer/sdk";
import { Address } from "viem";

// User defined swap input
const swapInput = {
  chainId: ChainId.SEPOLIA,
  swapKind: SwapKind.GivenIn,
  paths: [
    {
      pools: ["0x1e5b830439fce7aa6b430ca31a9d4dd775294378" as Address],
      tokens: [
        {
          address: "0xb19382073c7a0addbb56ac6af1808fa49e377b75" as Address,
          decimals: 18,
        }, // tokenIn
        {
          address: "0xf04378a3ff97b3f979a46f91f9b2d5a1d2394773" as Address,
          decimals: 18,
        }, // tokenOut
      ],
      vaultVersion: 3 as const,
      inputAmountRaw: 1000000000000000000n,
      outputAmountRaw: 990000000000000000n,
    },
  ],
};

// Create Swap object
const swap = new Swap(swapInput);

// Get up-to-date swap result by querying onchain
const updatedOutputAmount = await swap.query(RPC_URL) as ExactInQueryOutput;

// Build call data using user-defined slippage
const callData = swap.buildCall({
    slippage: Slippage.fromPercentage("0.1"), // 0.1%
    deadline: 999999999999999999n, // Deadline for the swap
    queryOutput: updatedOutputAmount,
    wethIsEth: false
  }) as SwapBuildOutputExactIn;

// Transaction data
console.log(`To: ${callData.to}`);
console.log(`CallData: ${callData.callData}`);
console.log(`Value: ${callData.value}`);
```

#### Installing the SDK

```bash
npm add @balancer/sdk
# or
yarn add @balancer/sdk
# or
pnpm add @balancer/sdk
```

### 3. Direct Contract Interaction (Without SDK)

#### Single Swap

For a single token swap with exact input amount, use:
- `swapSingleTokenExactIn` - Execute the swap
- `querySwapSingleTokenExactIn` - Simulate the swap to get the expected output amount

```javascript
// Using Viem
import { createPublicClient, createWalletClient, http } from "viem";
import { sepolia } from "viem/chains";

// Query operation
const client = createPublicClient({
    transport: http(RPC_URL),
    chain: sepolia,
});

const { result: amountOut } = await client.simulateContract({
    address: routerAddress,
    abi: routerAbi,
    functionName: "querySwapSingleTokenExactIn",
    args: [
        "0x1e5b830439fce7aa6b430ca31a9d4dd775294378", // pool address
        "0xb19382073c7a0addbb56ac6af1808fa49e377b75", // tokenIn
        "0xf04378a3ff97b3f979a46f91f9b2d5a1d2394773", // tokenOut
        1000000000000000000n, // exactAmountIn
        "0x", // userData
    ],
});

// Sending transaction
const walletClient = createWalletClient({
    chain: sepolia,
    transport: http(RPC_URL),
});

const hash = await walletClient.writeContract({
    address: routerAddress,
    abi: routerAbi,
    functionName: "swapSingleTokenExactIn",
    args: [
        "0x1e5b830439fce7aa6b430ca31a9d4dd775294378", // pool address
        "0xb19382073c7a0addbb56ac6af1808fa49e377b75", // tokenIn
        "0xf04378a3ff97b3f979a46f91f9b2d5a1d2394773", // tokenOut
        1000000000000000000n, // exactAmountIn
        900000000000000000n, // minAmountOut
        999999999999999999n, // Deadline
        false, // wethIsEth
        "0x", // userData
    ],
    account: "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
});
```

#### Multi-Path Swap

For swaps involving multiple paths with exact input amounts, use:
- `swapExactIn` - Execute the multi-path swap
- `querySwapExactIn` - Simulate the multi-path swap

```javascript
// Multi-path swap example
const paths = [
{
    tokenIn: "0xf04378a3ff97b3f979a46f91f9b2d5a1d2394773",
    exactAmountIn: 1000000000000000000n,
    minAmountOut: 0n,
    steps: [
    {
        pool: "0xb816c48b18925881ce8b64717725c7c9842429e4",
        tokenOut: "0x7b79995e5f793a07bc00c21412e50ecae098e7f9",
        isBuffer: false,
    },
    {
        pool: "0x6ad4e679c5bd9a14c50a81bd5f928a2a5ba7ec80",
        tokenOut: "0xb19382073c7a0addbb56ac6af1808fa49e377b75",
        isBuffer: false,
    },
    ],
},
{
    tokenIn: "0xf04378a3ff97b3f979a46f91f9b2d5a1d2394773",
    exactAmountIn: 1000000000000000000n,
    minAmountOut: 0n,
    steps: [
    {
        pool: "0x1e5b830439fce7aa6b430ca31a9d4dd775294378",
        tokenOut: "0xb19382073c7a0addbb56ac6af1808fa49e377b75",
        isBuffer: false,
    },
    ],
},
];

// Query the expected output
const { result } = await client.simulateContract({
    address: batchRouterAddress,
    abi: batchRouterAbi,
    functionName: "querySwapExactIn",
    args: [
        paths,
        "0x", // userData
    ],
});

// Execute the swap
const hash = await walletClient.writeContract({
    address: batchRouterAddress,
    abi: batchRouterAbi,
    functionName: "swapExactIn",
    args: [
        paths,
        999999999999999999n, // Deadline
        false, // wethIsEth
        "0x", // userData
    ],
    account: "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
});
```

### 4. Python Implementation

Here's how to implement a multi-path swap in Python using web3.py:

```python
import json
import os
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to the blockchain
rpc_url = os.getenv('RPC_URL')
w3 = Web3(Web3.HTTPProvider(rpc_url))

# Load private key
private_key = os.getenv('PRIVATE_KEY')
account = Account.from_key(private_key)
address = account.address

# Contract addresses
BATCH_ROUTER_ADDRESS = w3.to_checksum_address('0xe2fa4e1d17725e72dcdafe943ecf45df4b9e285b')
TOKEN_IN_ADDRESS = w3.to_checksum_address('0xaf204776c7245bF4147c2612BF6e5972Ee483701')  # sDAI
INTERMEDIATE_TOKEN_ADDRESS = w3.to_checksum_address('0x7c16F0185A26Db0AE7a9377f23BC18ea7ce5d644')  # waGNO
TOKEN_OUT_ADDRESS = w3.to_checksum_address('0x9c58bacc331c9aa871afd802db6379a98e80cedb')  # GNO
POOL_ADDRESS = w3.to_checksum_address('0xD1D7Fa8871d84d0E77020fc28B7Cd5718C446522')

# Load BatchRouter ABI
with open('config/batch_router_abi.json', 'r') as abi_file:
    batch_router_abi = json.load(abi_file)

# Initialize contract
batch_router = w3.eth.contract(address=BATCH_ROUTER_ADDRESS, abi=batch_router_abi)

# Amount to swap
amount_to_swap = w3.to_wei(0.01, 'ether')

# Define swap path with multiple steps
paths = [{
    'tokenIn': TOKEN_IN_ADDRESS,
    'steps': [
        # Step 1: TOKEN_IN → INTERMEDIATE_TOKEN through pool
        {
            'pool': POOL_ADDRESS,
            'tokenOut': INTERMEDIATE_TOKEN_ADDRESS,
            'isBuffer': False
        },
        # Step 2: INTERMEDIATE_TOKEN → TOKEN_OUT using buffer
        {
            'pool': INTERMEDIATE_TOKEN_ADDRESS,
            'tokenOut': TOKEN_OUT_ADDRESS,
            'isBuffer': True
        }
    ],
    'exactAmountIn': amount_to_swap,
    'minAmountOut': int(amount_to_swap * 0.9)  # 10% slippage
}]

# Set deadline to a very large value
deadline = 9007199254740991

# Execute swap with swapExactIn
swap_tx = batch_router.functions.swapExactIn(
    paths,
    deadline,
    False,  # wethIsEth
    b''     # userData
).build_transaction({
    'from': address,
    'nonce': w3.eth.get_transaction_count(address),
    'gas': 700000,
    'gasPrice': w3.eth.gas_price,
    'value': 0
})

# Sign and send transaction
signed_tx = account.sign_transaction(swap_tx)
tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
print(f"Swap transaction sent: {tx_hash.hex()}")

# Wait for transaction confirmation
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(f"Transaction status: {'Success' if receipt['status'] == 1 else 'Failed'}")
```

## Important Notes

1. **Permit2 for V3**: Balancer V3 swaps require Permit2 approvals, which is a key difference from V2.
2. **Approval**: For V2, approve the Vault (not the Router) to spend your tokens before swapping.
3. **Slippage Protection**: Set a reasonable `minAmountOut` to protect against price movements.
4. **Deadline**: Set an appropriate deadline to prevent transactions from being executed after market conditions change.
5. **Gas Estimation**: Multi-path swaps consume more gas than single swaps.
6. **Buffer Usage**: The `isBuffer` flag indicates whether the "pool" is actually an ERC4626 Buffer used for wrapping/unwrapping tokens.

## Troubleshooting

- If a swap fails, check that you have sufficient token balance and that the appropriate approvals are in place (Vault for V2, Permit2 for V3).
- Verify that the pool has sufficient liquidity for the swap.
- Ensure that all addresses are correctly checksummed.
- For complex swaps, try using the Balancer SDK which handles many edge cases automatically.
- If using Python with web3.py for V3 swaps, you may need to implement Permit2 approvals, which can be complex. Consider using the JavaScript SDK for V3 swaps if possible. 