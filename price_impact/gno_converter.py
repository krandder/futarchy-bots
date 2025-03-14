"""
Module for calculating the GNO to waGNO conversion rate.
"""

from .config.constants import EXTENDED_ERC20_ABI, ERC4626_ABI

class GnoConverter:
    """Class to calculate the GNO to waGNO conversion rate."""
    
    def __init__(self, w3, gno_address, wagno_address, verbose=False):
        """
        Initialize the GNO converter.
        
        Args:
            w3: Web3 instance
            gno_address: Address of the GNO token
            wagno_address: Address of the waGNO token
            verbose: Whether to print verbose output
        """
        self.w3 = w3
        self.gno_address = self.w3.to_checksum_address(gno_address)
        self.wagno_address = self.w3.to_checksum_address(wagno_address)
        self.verbose = verbose
        
        # Initialize token contracts
        self.gno_token = self.w3.eth.contract(
            address=self.gno_address,
            abi=EXTENDED_ERC20_ABI
        )
        
        self.wagno_token = self.w3.eth.contract(
            address=self.wagno_address,
            abi=ERC4626_ABI
        )
    
    def calculate_conversion_rate(self):
        """
        Calculate the conversion rate from GNO to waGNO using the ERC4626 convertToAssets function.
        
        Returns:
            float: The conversion rate (1 GNO = X waGNO)
        """
        try:
            # Get decimals for both tokens
            try:
                gno_decimals = self.gno_token.functions.decimals().call()
                wagno_decimals = self.wagno_token.functions.decimals().call()
            except Exception as e:
                print(f"Error getting token decimals: {e}")
                gno_decimals = 18
                wagno_decimals = 18
                
            # Use the ERC4626 convertToAssets function to get the conversion rate
            # For 1 waGNO share, how many GNO assets do we get?
            try:
                one_wagno_in_wei = 10 ** wagno_decimals  # 1 waGNO in wei
                gno_assets = self.wagno_token.functions.convertToAssets(one_wagno_in_wei).call()
                gno_assets_decimal = gno_assets / (10 ** gno_decimals)
                
                # The conversion rate is 1/gno_assets_decimal (1 GNO = X waGNO)
                if gno_assets_decimal > 0:
                    conversion_rate = 1 / gno_assets_decimal
                else:
                    conversion_rate = 1.0  # Default to 1:1 if calculation fails
                    
                if self.verbose:
                    print(f"GNO to waGNO conversion rate: {conversion_rate}")
                    if conversion_rate == 1.0:
                        print(f"Note: Using simplified 1:1 conversion rate. For accurate rates, implement Aave StaticAToken contract integration.")
                
                return conversion_rate
            except Exception as e:
                print(f"Error using convertToAssets: {e}")
                # Try alternative method using convertToShares
                try:
                    one_gno_in_wei = 10 ** gno_decimals  # 1 GNO in wei
                    wagno_shares = self.wagno_token.functions.convertToShares(one_gno_in_wei).call()
                    wagno_shares_decimal = wagno_shares / (10 ** wagno_decimals)
                    
                    # The conversion rate is wagno_shares_decimal (1 GNO = X waGNO)
                    if wagno_shares_decimal > 0:
                        conversion_rate = wagno_shares_decimal
                    else:
                        conversion_rate = 1.0  # Default to 1:1 if calculation fails
                        
                    if self.verbose:
                        print(f"GNO to waGNO conversion rate (using convertToShares): {conversion_rate}")
                        if conversion_rate == 1.0:
                            print(f"Note: Using simplified 1:1 conversion rate. For accurate rates, implement Aave StaticAToken contract integration.")
                    
                    return conversion_rate
                except Exception as e:
                    print(f"Error using convertToShares: {e}")
                    conversion_rate = 1.0  # Default to 1:1 if all calculations fail
            
            if self.verbose:
                print(f"GNO to waGNO conversion rate: {conversion_rate}")
                print(f"Note: Using simplified 1:1 conversion rate. For accurate rates, implement Aave StaticAToken contract integration.")
            
            return conversion_rate
        except Exception as e:
            print(f"Error calculating GNO to waGNO conversion rate: {e}")
            # Default to 1:1 if there's an error
            return 1.0 