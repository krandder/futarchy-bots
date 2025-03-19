require('dotenv').config();
const express = require('express');
const cors = require('cors');
const { ethers } = require('ethers');
const { Token, CurrencyAmount, Percent } = require('@uniswap/sdk-core');
const { Pool, Position, nearestUsableTick, TickMath, NonfungiblePositionManager } = require('@uniswap/v3-sdk');
const { SwapRouter } = require('@uniswap/v3-sdk');

// Initialize Express app
const app = express();
app.use(cors());
app.use(express.json());

// Connect to the blockchain
const provider = new ethers.providers.JsonRpcProvider(process.env.RPC_URL);

// Initialize wallet if private key is provided
let wallet = null;
if (process.env.PRIVATE_KEY) {
  wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);
}

// Chain ID for Gnosis Chain
const CHAIN_ID = 100;

// ERC20 ABI for token interactions
const ERC20_ABI = [
  'function decimals() view returns (uint8)',
  'function symbol() view returns (string)',
  'function name() view returns (string)',
  'function balanceOf(address) view returns (uint256)',
  'function approve(address, uint256) returns (bool)'
];

// Uniswap V3 Pool ABI
const POOL_ABI = [
  'function token0() external view returns (address)',
  'function token1() external view returns (address)',
  'function fee() external view returns (uint24)',
  'function tickSpacing() external view returns (int24)',
  'function liquidity() external view returns (uint128)',
  'function slot0() external view returns (uint160 sqrtPriceX96, int24 tick, uint16 observationIndex, uint16 observationCardinality, uint16 observationCardinalityNext, uint8 feeProtocol, bool unlocked)',
  'function ticks(int24 tick) external view returns (uint128 liquidityGross, int128 liquidityNet, uint256 feeGrowthOutside0X128, uint256 feeGrowthOutside1X128, int56 tickCumulativeOutside, uint160 secondsPerLiquidityOutsideX128, uint32 secondsOutside, bool initialized)'
];

// Uniswap V3 Router ABI
const ROUTER_ABI = [
  'function exactInputSingle(tuple(address tokenIn, address tokenOut, uint24 fee, address recipient, uint256 deadline, uint256 amountIn, uint256 amountOutMinimum, uint160 sqrtPriceLimitX96)) external payable returns (uint256 amountOut)'
];

// Helper function to create a Token instance
async function createToken(address) {
  const tokenContract = new ethers.Contract(address, ERC20_ABI, provider);
  const [decimals, symbol, name] = await Promise.all([
    tokenContract.decimals(),
    tokenContract.symbol(),
    tokenContract.name()
  ]);
  
  return new Token(CHAIN_ID, address, decimals, symbol, name);
}

// Helper function to get pool data
async function getPoolData(poolAddress) {
  const poolContract = new ethers.Contract(poolAddress, POOL_ABI, provider);
  
  const [token0Address, token1Address, fee, tickSpacing, liquidity, slot0] = await Promise.all([
    poolContract.token0(),
    poolContract.token1(),
    poolContract.fee(),
    poolContract.tickSpacing(),
    poolContract.liquidity(),
    poolContract.slot0()
  ]);
  
  const [token0, token1] = await Promise.all([
    createToken(token0Address),
    createToken(token1Address)
  ]);
  
  return {
    token0,
    token1,
    fee,
    tickSpacing,
    liquidity,
    sqrtPriceX96: slot0.sqrtPriceX96,
    tick: slot0.tick
  };
}

// Helper function to check if a tick is initialized
async function isTickInitialized(poolAddress, tick) {
  const poolContract = new ethers.Contract(poolAddress, POOL_ABI, provider);
  try {
    const tickData = await poolContract.ticks(tick);
    return tickData.initialized;
  } catch (error) {
    console.error(`Error checking tick ${tick}:`, error);
    return false;
  }
}

// API endpoint to get pool information
app.get('/api/pool/:poolAddress', async (req, res) => {
  try {
    const { poolAddress } = req.params;
    const poolData = await getPoolData(poolAddress);
    
    res.json({
      token0: {
        address: poolData.token0.address,
        symbol: poolData.token0.symbol,
        decimals: poolData.token0.decimals
      },
      token1: {
        address: poolData.token1.address,
        symbol: poolData.token1.symbol,
        decimals: poolData.token1.decimals
      },
      fee: poolData.fee,
      tickSpacing: poolData.tickSpacing,
      liquidity: poolData.liquidity.toString(),
      sqrtPriceX96: poolData.sqrtPriceX96.toString(),
      tick: poolData.tick
    });
  } catch (error) {
    console.error('Error getting pool data:', error);
    res.status(500).json({ error: error.message });
  }
});

// API endpoint to check if ticks are initialized
app.post('/api/check-ticks', async (req, res) => {
  try {
    const { poolAddress, ticks } = req.body;
    
    if (!poolAddress || !ticks || !Array.isArray(ticks)) {
      return res.status(400).json({ error: 'Invalid request. Provide poolAddress and ticks array.' });
    }
    
    const poolData = await getPoolData(poolAddress);
    const results = {};
    
    for (const tick of ticks) {
      // Adjust tick to be a multiple of tickSpacing
      const adjustedTick = Math.floor(tick / poolData.tickSpacing) * poolData.tickSpacing;
      results[adjustedTick] = await isTickInitialized(poolAddress, adjustedTick);
    }
    
    // Also check ticks around current tick
    const currentTick = poolData.tick;
    const ticksAroundCurrent = [];
    for (let i = -5; i <= 5; i++) {
      const tick = currentTick + (i * poolData.tickSpacing);
      ticksAroundCurrent.push(tick);
      results[tick] = await isTickInitialized(poolAddress, tick);
    }
    
    res.json({
      poolAddress,
      currentTick,
      tickSpacing: poolData.tickSpacing,
      results
    });
  } catch (error) {
    console.error('Error checking ticks:', error);
    res.status(500).json({ error: error.message });
  }
});

// API endpoint to create a full range position
app.post('/api/add-full-range-liquidity', async (req, res) => {
  try {
    const { poolAddress, amount0, amount1 } = req.body;
    
    if (!poolAddress || !amount0 || !amount1) {
      return res.status(400).json({ error: 'Invalid request. Provide poolAddress, amount0, and amount1.' });
    }
    
    if (!wallet) {
      return res.status(400).json({ error: 'No private key provided. Cannot sign transactions.' });
    }
    
    const poolData = await getPoolData(poolAddress);
    
    // Create Pool instance
    const pool = new Pool(
      poolData.token0,
      poolData.token1,
      poolData.fee,
      poolData.sqrtPriceX96.toString(),
      poolData.liquidity.toString(),
      poolData.tick
    );
    
    // Create Position with full range (MIN_TICK to MAX_TICK)
    const position = Position.fromAmounts({
      pool,
      tickLower: TickMath.MIN_TICK,
      tickUpper: TickMath.MAX_TICK,
      amount0: amount0,
      amount1: amount1,
      useFullPrecision: true
    });
    
    // Approve tokens if needed
    const token0Contract = new ethers.Contract(poolData.token0.address, ERC20_ABI, wallet);
    const token1Contract = new ethers.Contract(poolData.token1.address, ERC20_ABI, wallet);
    
    await token0Contract.approve(
      process.env.NONFUNGIBLE_POSITION_MANAGER,
      ethers.utils.parseUnits(amount0, poolData.token0.decimals)
    );
    
    await token1Contract.approve(
      process.env.NONFUNGIBLE_POSITION_MANAGER,
      ethers.utils.parseUnits(amount1, poolData.token1.decimals)
    );
    
    // Create mint options
    const mintOptions = {
      recipient: wallet.address,
      deadline: Math.floor(Date.now() / 1000) + 60 * 20, // 20 minutes from now
      slippageTolerance: new Percent(50, 10000) // 0.5%
    };
    
    // Get calldata for minting
    const { calldata, value } = NonfungiblePositionManager.addCallParameters(position, mintOptions);
    
    // Create and send transaction
    const transaction = {
      data: calldata,
      to: process.env.NONFUNGIBLE_POSITION_MANAGER,
      value: value,
      from: wallet.address,
      gasLimit: ethers.utils.hexlify(1000000) // Adjust as needed
    };
    
    const txResponse = await wallet.sendTransaction(transaction);
    
    res.json({
      transactionHash: txResponse.hash,
      position: {
        token0: poolData.token0.symbol,
        token1: poolData.token1.symbol,
        fee: poolData.fee,
        tickLower: TickMath.MIN_TICK,
        tickUpper: TickMath.MAX_TICK,
        amount0: amount0,
        amount1: amount1
      }
    });
  } catch (error) {
    console.error('Error adding liquidity:', error);
    res.status(500).json({ error: error.message });
  }
});

// API endpoint to create a position with custom tick range
app.post('/api/add-liquidity', async (req, res) => {
  try {
    const { poolAddress, tickLower, tickUpper, amount0, amount1 } = req.body;
    
    if (!poolAddress || tickLower === undefined || tickUpper === undefined || !amount0 || !amount1) {
      return res.status(400).json({ error: 'Invalid request. Provide poolAddress, tickLower, tickUpper, amount0, and amount1.' });
    }
    
    if (!wallet) {
      return res.status(400).json({ error: 'No private key provided. Cannot sign transactions.' });
    }
    
    const poolData = await getPoolData(poolAddress);
    
    // Create Pool instance
    const pool = new Pool(
      poolData.token0,
      poolData.token1,
      poolData.fee,
      poolData.sqrtPriceX96.toString(),
      poolData.liquidity.toString(),
      poolData.tick
    );
    
    // Adjust ticks to be multiples of tickSpacing
    const adjustedTickLower = Math.floor(tickLower / poolData.tickSpacing) * poolData.tickSpacing;
    const adjustedTickUpper = Math.floor(tickUpper / poolData.tickSpacing) * poolData.tickSpacing;
    
    // Create Position
    const position = Position.fromAmounts({
      pool,
      tickLower: adjustedTickLower,
      tickUpper: adjustedTickUpper,
      amount0: amount0,
      amount1: amount1,
      useFullPrecision: true
    });
    
    // Approve tokens if needed
    const token0Contract = new ethers.Contract(poolData.token0.address, ERC20_ABI, wallet);
    const token1Contract = new ethers.Contract(poolData.token1.address, ERC20_ABI, wallet);
    
    await token0Contract.approve(
      process.env.NONFUNGIBLE_POSITION_MANAGER,
      ethers.utils.parseUnits(amount0, poolData.token0.decimals)
    );
    
    await token1Contract.approve(
      process.env.NONFUNGIBLE_POSITION_MANAGER,
      ethers.utils.parseUnits(amount1, poolData.token1.decimals)
    );
    
    // Create mint options
    const mintOptions = {
      recipient: wallet.address,
      deadline: Math.floor(Date.now() / 1000) + 60 * 20, // 20 minutes from now
      slippageTolerance: new Percent(50, 10000) // 0.5%
    };
    
    // Get calldata for minting
    const { calldata, value } = NonfungiblePositionManager.addCallParameters(position, mintOptions);
    
    // Create and send transaction
    const transaction = {
      data: calldata,
      to: process.env.NONFUNGIBLE_POSITION_MANAGER,
      value: value,
      from: wallet.address,
      gasLimit: ethers.utils.hexlify(1000000) // Adjust as needed
    };
    
    const txResponse = await wallet.sendTransaction(transaction);
    
    res.json({
      transactionHash: txResponse.hash,
      position: {
        token0: poolData.token0.symbol,
        token1: poolData.token1.symbol,
        fee: poolData.fee,
        tickLower: adjustedTickLower,
        tickUpper: adjustedTickUpper,
        amount0: amount0,
        amount1: amount1
      }
    });
  } catch (error) {
    console.error('Error adding liquidity:', error);
    res.status(500).json({ error: error.message });
  }
});

// API endpoint to get pool information
app.get('/pool-info', async (req, res) => {
  try {
    const { poolAddress, token0Address, token1Address } = req.query;
    
    if (!poolAddress || !token0Address || !token1Address) {
      return res.status(400).json({ error: 'Invalid request. Provide poolAddress, token0Address, and token1Address.' });
    }
    
    const poolData = await getPoolData(poolAddress);
    
    // Verify token addresses match
    if (poolData.token0.address.toLowerCase() !== token0Address.toLowerCase() ||
        poolData.token1.address.toLowerCase() !== token1Address.toLowerCase()) {
      return res.status(400).json({ error: 'Token addresses do not match pool tokens.' });
    }
    
    res.json({
      token0: {
        address: poolData.token0.address,
        symbol: poolData.token0.symbol,
        decimals: poolData.token0.decimals
      },
      token1: {
        address: poolData.token1.address,
        symbol: poolData.token1.symbol,
        decimals: poolData.token1.decimals
      },
      fee: poolData.fee,
      tickSpacing: poolData.tickSpacing,
      liquidity: poolData.liquidity.toString(),
      sqrtPriceX96: poolData.sqrtPriceX96.toString(),
      tick: poolData.tick,
      minTick: TickMath.MIN_TICK,
      maxTick: TickMath.MAX_TICK
    });
  } catch (error) {
    console.error('Error getting pool data:', error);
    res.status(500).json({ error: error.message });
  }
});

// API endpoint to add liquidity
app.post('/add-liquidity', async (req, res) => {
  try {
    const {
      poolAddress,
      token0Address,
      token1Address,
      amount0,
      amount1,
      useFullRange,
      slippageTolerance,
      deadline,
      signer
    } = req.body;
    
    if (!poolAddress || !token0Address || !token1Address || !amount0 || !amount1 || !signer) {
      return res.status(400).json({
        error: 'Invalid request. Provide poolAddress, token0Address, token1Address, amount0, amount1, and signer.'
      });
    }
    
    // Create wallet from provided signer
    const signerWallet = new ethers.Wallet(signer.privateKey, provider);
    
    const poolData = await getPoolData(poolAddress);
    
    // Verify token addresses match
    if (poolData.token0.address.toLowerCase() !== token0Address.toLowerCase() ||
        poolData.token1.address.toLowerCase() !== token1Address.toLowerCase()) {
      return res.status(400).json({ error: 'Token addresses do not match pool tokens.' });
    }
    
    // Create Pool instance
    const pool = new Pool(
      poolData.token0,
      poolData.token1,
      poolData.fee,
      poolData.sqrtPriceX96.toString(),
      poolData.liquidity.toString(),
      poolData.tick
    );
    
    // Calculate tick range
    const tickLower = useFullRange ? TickMath.MIN_TICK : nearestUsableTick(poolData.tick - 100 * poolData.tickSpacing, poolData.tickSpacing);
    const tickUpper = useFullRange ? TickMath.MAX_TICK : nearestUsableTick(poolData.tick + 100 * poolData.tickSpacing, poolData.tickSpacing);
    
    // Create Position
    const position = Position.fromAmounts({
      pool,
      tickLower,
      tickUpper,
      amount0,
      amount1,
      useFullPrecision: true
    });
    
    // Create mint options
    const mintOptions = {
      recipient: signer.address,
      deadline: deadline || Math.floor(Date.now() / 1000) + 3600, // 1 hour from now if not specified
      slippageTolerance: new Percent(
        Math.floor((slippageTolerance || 0.05) * 10000),
        10000
      )
    };
    
    // Get calldata for minting
    const { calldata, value } = NonfungiblePositionManager.addCallParameters(position, mintOptions);
    
    // Create and send transaction
    const transaction = {
      data: calldata,
      to: process.env.NONFUNGIBLE_POSITION_MANAGER,
      value: value,
      from: signer.address,
      gasLimit: ethers.utils.hexlify(1000000) // Adjust as needed
    };
    
    const txResponse = await signerWallet.sendTransaction(transaction);
    
    res.json({
      hash: txResponse.hash,
      position: {
        token0: poolData.token0.symbol,
        token1: poolData.token1.symbol,
        fee: poolData.fee,
        tickLower,
        tickUpper,
        amount0,
        amount1
      }
    });
  } catch (error) {
    console.error('Error adding liquidity:', error);
    res.status(500).json({ error: error.message });
  }
});

// API endpoint to get NFT manager address
app.get('/nft-manager', async (req, res) => {
  try {
    if (!process.env.NONFUNGIBLE_POSITION_MANAGER) {
      return res.status(500).json({ error: 'NFT manager address not configured' });
    }
    
    res.json({
      address: process.env.NONFUNGIBLE_POSITION_MANAGER
    });
  } catch (error) {
    console.error('Error getting NFT manager address:', error);
    res.status(500).json({ error: error.message });
  }
});

// API endpoint to perform swaps
app.post('/api/swap', async (req, res) => {
  try {
    const {
      poolAddress,
      tokenIn,
      tokenOut,
      fee,
      recipient,
      amountIn,
      amountOutMinimum,
      sqrtPriceLimitX96,
      signer
    } = req.body;
    
    if (!poolAddress || !tokenIn || !tokenOut || !fee || !recipient || !amountIn || !signer) {
      return res.status(400).json({
        error: 'Invalid request. Provide poolAddress, tokenIn, tokenOut, fee, recipient, amountIn, and signer.'
      });
    }
    
    // Create wallet from provided signer
    const signerWallet = new ethers.Wallet(signer.privateKey, provider);
    
    // Get pool data
    const poolData = await getPoolData(poolAddress);
    
    // Create Router contract instance
    const router = new ethers.Contract(process.env.SWAP_ROUTER, ROUTER_ABI, signerWallet);
    
    // Create swap parameters
    const params = {
      tokenIn,
      tokenOut,
      fee,
      recipient,
      deadline: Math.floor(Date.now() / 1000) + 1800, // 30 minutes from now
      amountIn,
      amountOutMinimum: amountOutMinimum || '0',
      sqrtPriceLimitX96: sqrtPriceLimitX96 || '0'
    };
    
    // Estimate gas
    const gasLimit = await router.estimateGas.exactInputSingle(params);
    
    // Send transaction
    const txResponse = await router.exactInputSingle(params, {
      gasLimit: gasLimit.mul(120).div(100) // Add 20% buffer
    });
    
    res.json({
      hash: txResponse.hash,
      swap: {
        tokenIn: poolData.token0.address === tokenIn ? poolData.token0.symbol : poolData.token1.symbol,
        tokenOut: poolData.token0.address === tokenOut ? poolData.token0.symbol : poolData.token1.symbol,
        amountIn,
        fee: poolData.fee
      }
    });
  } catch (error) {
    console.error('Error performing swap:', error);
    res.status(500).json({ error: error.message });
  }
});

// Start the server
const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`Uniswap V3 Bridge server running on port ${PORT}`);
}); 