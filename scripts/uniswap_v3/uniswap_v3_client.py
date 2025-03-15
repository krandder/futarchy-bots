#!/usr/bin/env python3
"""
Uniswap V3 Client

This module provides a client for interacting with the Uniswap V3 JavaScript bridge.
It allows Python code to leverage the Uniswap V3 SDK functionality.
"""

import os
import json
import requests
from typing import List, Dict, Any, Optional, Union
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class UniswapV3Client:
    """Client for interacting with the Uniswap V3 JavaScript bridge."""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the Uniswap V3 client.
        
        Args:
            base_url: The base URL of the Uniswap V3 bridge API. Defaults to environment variable or localhost.
        """
        self.base_url = base_url or os.getenv("UNISWAP_V3_BRIDGE_URL", "http://localhost:3001")
    
    def get_pool_info(self, pool_address: str) -> Dict[str, Any]:
        """
        Get information about a Uniswap V3 pool.
        
        Args:
            pool_address: The address of the pool.
            
        Returns:
            Dict containing pool information.
        """
        response = requests.get(f"{self.base_url}/api/pool/{pool_address}")
        response.raise_for_status()
        return response.json()
    
    def check_ticks(self, pool_address: str, ticks: List[int]) -> Dict[str, Any]:
        """
        Check if specific ticks are initialized in a pool.
        
        Args:
            pool_address: The address of the pool.
            ticks: List of tick indices to check.
            
        Returns:
            Dict containing results of tick initialization checks.
        """
        payload = {
            "poolAddress": pool_address,
            "ticks": ticks
        }
        response = requests.post(f"{self.base_url}/api/check-ticks", json=payload)
        response.raise_for_status()
        return response.json()
    
    def add_full_range_liquidity(self, pool_address: str, amount0: str, amount1: str) -> Dict[str, Any]:
        """
        Add liquidity across the full price range (MIN_TICK to MAX_TICK).
        
        Args:
            pool_address: The address of the pool.
            amount0: The amount of token0 to add.
            amount1: The amount of token1 to add.
            
        Returns:
            Dict containing transaction information.
        """
        payload = {
            "poolAddress": pool_address,
            "amount0": amount0,
            "amount1": amount1
        }
        response = requests.post(f"{self.base_url}/api/add-full-range-liquidity", json=payload)
        response.raise_for_status()
        return response.json()
    
    def add_liquidity(self, pool_address: str, tick_lower: int, tick_upper: int, 
                     amount0: str, amount1: str) -> Dict[str, Any]:
        """
        Add liquidity within a specific tick range.
        
        Args:
            pool_address: The address of the pool.
            tick_lower: The lower tick of the position.
            tick_upper: The upper tick of the position.
            amount0: The amount of token0 to add.
            amount1: The amount of token1 to add.
            
        Returns:
            Dict containing transaction information.
        """
        payload = {
            "poolAddress": pool_address,
            "tickLower": tick_lower,
            "tickUpper": tick_upper,
            "amount0": amount0,
            "amount1": amount1
        }
        response = requests.post(f"{self.base_url}/api/add-liquidity", json=payload)
        response.raise_for_status()
        return response.json()


def main():
    """Example usage of the Uniswap V3 client."""
    client = UniswapV3Client()
    
    # Example: Get pool information
    pool_address = os.getenv("POOL_YES", "0x9a14d28909f42823ee29847f87a15fb3b6e8aed3")
    try:
        pool_info = client.get_pool_info(pool_address)
        print(f"Pool Information for {pool_address}:")
        print(json.dumps(pool_info, indent=2))
        
        # Example: Check ticks
        current_tick = pool_info["tick"]
        ticks_to_check = [current_tick - 100, current_tick, current_tick + 100]
        tick_results = client.check_ticks(pool_address, ticks_to_check)
        print("\nTick Initialization Status:")
        print(json.dumps(tick_results, indent=2))
        
    except requests.RequestException as e:
        print(f"Error communicating with Uniswap V3 bridge: {e}")
        print("Make sure the bridge server is running.")


if __name__ == "__main__":
    main() 