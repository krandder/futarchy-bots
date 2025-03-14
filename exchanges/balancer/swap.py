"""
Balancer swap handler for executing swaps on Balancer pools.
This module provides functionality to execute swaps on Balancer with automatic Permit2 handling.
"""

from web3 import Web3
import os
import json
from pathlib import Path
from .permit2 import BalancerPermit2Handler
from config.constants import BALANCER_CONFIG, TOKEN_CONFIG, CONTRACT_ADDRESSES

class BalancerSwapHandler:
    """Handler for Balancer swap operations."""
    
    def __init__(self, bot, verbose=False):
        """
        Initialize the Balancer swap handler.
        
        Args:
            bot: FutarchyBot instance with web3 connection and account
            verbose: Whether to print verbose debug information
        """
        self.bot = bot
        self.w3 = bot.w3
        self.account = bot.account
        self.address = bot.address
        self.verbose = verbose
        
        # Get Balancer addresses from constants
        self.balancer_vault_address = self.w3.to_checksum_address(
            os.environ.get('BALANCER_VAULT_ADDRESS', BALANCER_CONFIG["vault_address"])
        )
        self.balancer_pool_address = self.w3.to_checksum_address(
            os.environ.get('BALANCER_POOL_ADDRESS', BALANCER_CONFIG["pool_address"])
        )
        
        # Get BatchRouter address from constants
        self.batch_router_address = self.w3.to_checksum_address(
            os.environ.get('BATCH_ROUTER_ADDRESS', CONTRACT_ADDRESSES["batchRouter"])
        )
        
        # Initialize Permit2 handler
        self.permit2_handler = BalancerPermit2Handler(bot, verbose)
        
        # Initialize Balancer contracts
        self.init_contracts()
        
        if self.verbose:
            print(f"Initialized Balancer swap handler with vault: {self.balancer_vault_address}")
            print(f"Pool address: {self.balancer_pool_address}")
            print(f"BatchRouter address: {self.batch_router_address}")
    
    def init_contracts(self):
        """Initialize Balancer contract instances."""
        # Balancer Vault ABI (minimal for swaps)
        self.balancer_vault_abi = [
            {
                "inputs": [
                    {
                        "internalType": "bytes32",
                        "name": "poolId",
                        "type": "bytes32"
                    }
                ],
                "name": "getPoolTokens",
                "outputs": [
                    {
                        "internalType": "address[]",
                        "name": "tokens",
                        "type": "address[]"
                    },
                    {
                        "internalType": "uint256[]",
                        "name": "balances",
                        "type": "uint256[]"
                    },
                    {
                        "internalType": "uint256",
                        "name": "lastChangeBlock",
                        "type": "uint256"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        # Initialize Balancer Vault contract
        self.balancer_vault = self.w3.eth.contract(
            address=self.balancer_vault_address,
            abi=self.balancer_vault_abi
        )
        
        # Load BatchRouter ABI from file
        reference_path = Path(__file__).parent.parent.parent / ".reference" / "balancer_router.abi.json"
        if reference_path.exists():
            with open(reference_path, 'r') as f:
                self.batch_router_abi = json.load(f)
        else:
            raise FileNotFoundError(f"BatchRouter ABI file not found at {reference_path}")
        
        # Initialize BatchRouter contract
        self.batch_router = self.w3.eth.contract(
            address=self.batch_router_address,
            abi=self.batch_router_abi
        )
        
        # Get the pool ID from the pool contract
        try:
            # Balancer Pool ABI (minimal for getting pool ID)
            self.balancer_pool_abi = [
                {
                    "inputs": [],
                    "name": "getPoolId",
                    "outputs": [
                        {
                            "internalType": "bytes32",
                            "name": "",
                            "type": "bytes32"
                        }
                    ],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
            
            self.balancer_pool = self.w3.eth.contract(
                address=self.balancer_pool_address,
                abi=self.balancer_pool_abi
            )
            
            self.pool_id = self.balancer_pool.functions.getPoolId().call()
            if self.verbose:
                print(f"Retrieved Balancer pool ID: {self.pool_id.hex()}")
        except Exception as e:
            print(f"Warning: Could not retrieve pool ID: {e}")
            # Use a fallback pool ID if needed
            self.pool_id = bytes.fromhex(BALANCER_CONFIG["pool_id"][2:])
            print(f"Using fallback pool ID: {self.pool_id.hex()}")
    
    def get_pool_tokens(self):
        """
        Get the tokens in the Balancer pool.
        
        Returns:
            tuple: (token_addresses, token_balances)
        """
        try:
            tokens, balances, _ = self.balancer_vault.functions.getPoolTokens(self.pool_id).call()
            return tokens, balances
        except Exception as e:
            print(f"❌ Error getting pool tokens: {e}")
            return [], []
    
    def swap(self, token_in, token_out, amount_in, min_amount_out=None, auto_permit=True):
        """
        Execute a swap on Balancer using the BatchRouter.
        
        Args:
            token_in: Address of the token to swap from
            token_out: Address of the token to swap to
            amount_in: Amount to swap (in ether units)
            min_amount_out: Minimum amount to receive (in ether units, optional)
            auto_permit: Whether to automatically handle Permit2 authorization
            
        Returns:
            dict: Swap result information
        """
        try:
            # Convert addresses to checksummed form
            token_in_cs = self.w3.to_checksum_address(token_in)
            token_out_cs = self.w3.to_checksum_address(token_out)
            
            if self.verbose:
                print(f"Token in: {token_in_cs}")
                print(f"Token out: {token_out_cs}")
            
            # Convert amount to wei
            amount_in_wei = self.w3.to_wei(amount_in, 'ether')
            
            if self.verbose:
                print(f"Amount in wei: {amount_in_wei}")
            
            # Check token balance
            token_in_contract = self.bot.get_token_contract(token_in_cs)
            token_in_balance = token_in_contract.functions.balanceOf(self.address).call()
            
            if token_in_balance < amount_in_wei:
                print(f"❌ Insufficient balance. Required: {amount_in}, Available: {self.w3.from_wei(token_in_balance, 'ether')}")
                return {"success": False, "error": "Insufficient balance"}
            
            # Handle Permit2 if needed
            if auto_permit:
                # Check if we need a permit for BatchRouter
                permit_status = self.permit2_handler.check_permit(token_in_cs, self.batch_router_address, amount_in)
                
                if permit_status["needs_permit"]:
                    print("Creating Permit2 authorization for BatchRouter...")
                    permit_success = self.permit2_handler.ensure_permit(token_in_cs, self.batch_router_address, amount_in)
                    
                    if not permit_success:
                        print("❌ Failed to create Permit2 authorization")
                        return {"success": False, "error": "Permit2 authorization failed"}
            
            # Define swap parameters for BatchRouter
            paths = [
                {
                    "tokenIn": token_in_cs,
                    "steps": [
                        {
                            "pool": self.balancer_pool_address,
                            "tokenOut": token_out_cs,
                            "isBuffer": False
                        }
                    ],
                    "exactAmountIn": amount_in_wei,
                    "minAmountOut": 0  # Will be updated after query
                }
            ]
            
            # Query expected output
            print("Querying expected swap output...")
            try:
                expected_output = self.batch_router.functions.querySwapExactIn(
                    paths,
                    self.address,
                    '0x'  # empty user data
                ).call()
                
                if self.verbose:
                    print(f"Expected output: {expected_output}")
                
                if expected_output and expected_output[0]:
                    expected_amount = expected_output[0][0]
                    print(f"Expected output: {self.w3.from_wei(expected_amount, 'ether')} tokens")
                    
                    # Calculate min amount out if not provided
                    if min_amount_out is None:
                        min_amount_out = amount_in * 0.9  # 10% slippage
                        print(f"Using default minimum amount out: {min_amount_out} (with 10% slippage)")
                    
                    min_amount_out_wei = self.w3.to_wei(min_amount_out, 'ether')
                    
                    # Ensure min_amount_out is not higher than expected output
                    if min_amount_out_wei > expected_amount:
                        min_amount_out_wei = int(expected_amount * 0.9)  # 10% below expected
                        print(f"Adjusted min amount out to 90% of expected: {self.w3.from_wei(min_amount_out_wei, 'ether')}")
                    
                    # Update minAmountOut in paths
                    paths[0]["minAmountOut"] = min_amount_out_wei
                else:
                    print("Warning: Could not determine expected output")
                    # Set a very low minAmountOut
                    min_amount_out_wei = 1
                    paths[0]["minAmountOut"] = min_amount_out_wei
            except Exception as e:
                print(f"Error during query: {e}")
                # Set a very low minAmountOut
                min_amount_out_wei = 1
                paths[0]["minAmountOut"] = min_amount_out_wei
            
            if self.verbose:
                print(f"Min amount out wei: {min_amount_out_wei}")
            
            print(f"Swapping {amount_in} tokens for at least {self.w3.from_wei(min_amount_out_wei, 'ether')} tokens on Balancer...")
            
            # Set deadline to 10 minutes from now
            deadline = self.w3.eth.get_block('latest')['timestamp'] + 600
            wethIsEth = False  # Not using ETH directly
            userData = b""  # no additional data
            
            # Try to estimate gas first
            try:
                gas_estimate = self.batch_router.functions.swapExactIn(
                    paths,
                    deadline,
                    wethIsEth,
                    userData
                ).estimate_gas({
                    'from': self.address,
                    'value': 0
                })
                
                if self.verbose:
                    print(f"Estimated gas: {gas_estimate}")
                    
            except Exception as gas_error:
                print(f"❌ Gas estimation failed: {gas_error}")
                print("This usually indicates the transaction will fail, but proceeding anyway...")
                gas_estimate = 1000000  # Default value
            
            # Build the swap transaction
            swap_tx = self.batch_router.functions.swapExactIn(
                paths,
                deadline,
                wethIsEth,
                userData
            ).build_transaction({
                'from': self.address,
                'nonce': self.w3.eth.get_transaction_count(self.address),
                'gas': int(gas_estimate * 1.2) if gas_estimate != 1000000 else 1000000,  # Add 20% buffer if estimated
                'gasPrice': self.w3.eth.gas_price,
                'value': 0,
                'chainId': self.w3.eth.chain_id
            })
            
            # Sign and send transaction
            signed_tx = self.w3.eth.account.sign_transaction(swap_tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash_hex = tx_hash.hex()
            
            print(f"⏳ Swap transaction sent: {tx_hash_hex}")
            print(f"View on block explorer: https://gnosisscan.io/tx/{tx_hash_hex}")
            
            # Wait for transaction confirmation
            print("Waiting for transaction confirmation...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt['status'] == 1:
                # Get token balance after swap
                token_out_contract = self.bot.get_token_contract(token_out_cs)
                token_out_balance_before = token_out_contract.functions.balanceOf(self.address).call()
                
                print(f"✅ Swap successful! Gas used: {receipt['gasUsed']}")
                
                return {
                    "success": True,
                    "tx_hash": tx_hash_hex,
                    "gas_used": receipt['gasUsed'],
                    "token_out_balance": token_out_balance_before,
                    "token_out_balance_eth": self.w3.from_wei(token_out_balance_before, 'ether')
                }
            else:
                print("❌ Swap transaction failed!")
                
                return {
                    "success": False,
                    "tx_hash": tx_hash_hex,
                    "error": "Transaction failed on-chain"
                }
                
        except Exception as e:
            print(f"❌ Error executing swap: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "error": str(e)
            }
    
    def swap_sdai_to_wagno(self, amount, min_amount_out=None, auto_permit=True):
        """
        Swap sDAI for waGNO on Balancer.
        
        Args:
            amount: Amount of sDAI to swap (in ether units)
            min_amount_out: Minimum amount of waGNO to receive (in ether units, optional)
            auto_permit: Whether to automatically handle Permit2 authorization
            
        Returns:
            dict: Swap result information
        """
        # Get token addresses from constants
        sdai_address = os.environ.get('TOKEN_IN_ADDRESS', TOKEN_CONFIG["currency"]["address"])
        wagno_address = os.environ.get('TOKEN_OUT_ADDRESS', TOKEN_CONFIG["wagno"]["address"])
        
        print(f"Swapping {amount} sDAI for waGNO...")
        return self.swap(sdai_address, wagno_address, amount, min_amount_out, auto_permit)
    
    def swap_wagno_to_sdai(self, amount, min_amount_out=None, auto_permit=True):
        """
        Swap waGNO for sDAI on Balancer.
        
        Args:
            amount: Amount of waGNO to swap (in ether units)
            min_amount_out: Minimum amount of sDAI to receive (in ether units, optional)
            auto_permit: Whether to automatically handle Permit2 authorization
            
        Returns:
            dict: Swap result information
        """
        # Get token addresses from constants
        sdai_address = os.environ.get('TOKEN_IN_ADDRESS', TOKEN_CONFIG["currency"]["address"])
        wagno_address = os.environ.get('TOKEN_OUT_ADDRESS', TOKEN_CONFIG["wagno"]["address"])
        
        print(f"Swapping {amount} waGNO for sDAI...")
        return self.swap(wagno_address, sdai_address, amount, min_amount_out, auto_permit) 