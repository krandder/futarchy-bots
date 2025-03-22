"""
Tests for the Token Balance Checker module.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from web3 import Web3
from futarchy.balance_checker import (
    TokenBalanceChecker,
    get_balances,
    get_web3,
    get_address_from_env
)

class TestTokenBalanceChecker(unittest.TestCase):
    """Test cases for TokenBalanceChecker class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock Web3 instance with eth attribute
        self.w3 = Mock(spec=Web3)
        self.w3.to_checksum_address = lambda x: x  # Simple passthrough
        self.w3.from_wei = lambda x, unit: float(x) / 1e18  # Simple ether conversion
        
        # Create eth mock with contract method
        eth_mock = MagicMock()
        contract_mock = MagicMock()
        eth_mock.contract = contract_mock
        self.w3.eth = eth_mock
        
        # Sample token config
        self.token_config = {
            'currency': {
                'name': 'sDAI',
                'address': '0x1234',
                'yes_address': '0x5678',
                'no_address': '0x9abc'
            },
            'company': {
                'name': 'GNO',
                'address': '0xdef0',
                'yes_address': '0x1234',
                'no_address': '0x5678'
            },
            'wagno': {
                'name': 'waGNO',
                'address': '0x9abc'
            }
        }
        
        # Sample ERC20 ABI (minimal for testing)
        self.erc20_abi = [
            {
                "constant": True,
                "inputs": [{"name": "owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            }
        ]
        
        # Create balance checker instance
        self.checker = TokenBalanceChecker(self.w3, self.token_config, self.erc20_abi)
        
        # Mock contract instances
        for contract in self.checker.token_contracts.values():
            contract.functions.balanceOf = Mock()
            contract.functions.balanceOf.return_value = Mock()
            contract.functions.balanceOf.return_value.call = Mock(return_value=1000000000000000000)  # 1 token
    
    def test_initialization(self):
        """Test checker initialization with different configurations."""
        # Test with defaults
        checker = TokenBalanceChecker(self.w3)
        self.assertIsNotNone(checker.token_config)
        self.assertIsNotNone(checker.erc20_abi)
        
        # Test with custom config
        checker = TokenBalanceChecker(self.w3, self.token_config, self.erc20_abi)
        self.assertEqual(checker.token_config, self.token_config)
        self.assertEqual(checker.erc20_abi, self.erc20_abi)
    
    def test_get_balances(self):
        """Test getting balances for an address."""
        balances = self.checker.get_balances('0xtest')
        
        # Check structure
        self.assertIn('currency', balances)
        self.assertIn('company', balances)
        self.assertIn('wagno', balances)
        
        # Check currency balances
        self.assertIn('wallet', balances['currency'])
        self.assertIn('yes', balances['currency'])
        self.assertIn('no', balances['currency'])
        
        # Check company balances
        self.assertIn('wallet', balances['company'])
        self.assertIn('yes', balances['company'])
        self.assertIn('no', balances['company'])
        
        # Check wagno balance
        self.assertIn('wallet', balances['wagno'])
        
        # Check values (should all be 1.0 from our mock)
        self.assertEqual(balances['currency']['wallet'], 1.0)
        self.assertEqual(balances['currency']['yes'], 1.0)
        self.assertEqual(balances['currency']['no'], 1.0)
        self.assertEqual(balances['company']['wallet'], 1.0)
        self.assertEqual(balances['company']['yes'], 1.0)
        self.assertEqual(balances['company']['no'], 1.0)
        self.assertEqual(balances['wagno']['wallet'], 1.0)
    
    def test_floor_to_decimals(self):
        """Test decimal floor function."""
        test_cases = [
            (1.123456789, 6, 1.123456),
            (1.999999, 6, 1.999999),
            (1.9999999, 6, 1.999999),
            (0, 6, 0.0),
            (0.1234567, 4, 0.1234),
            (Decimal('1.123456789'), 6, 1.123456)
        ]
        
        for value, decimals, expected in test_cases:
            result = self.checker._floor_to_decimals(value, decimals)
            self.assertEqual(result, expected)
    
    def test_invalid_address(self):
        """Test error handling for invalid address."""
        with self.assertRaises(ValueError):
            self.checker.get_balances(None)
        
        with self.assertRaises(ValueError):
            self.checker.get_balances("")
    
    def test_print_balances(self):
        """Test balance printing functionality."""
        # Mock print function
        with patch('builtins.print') as mock_print:
            balances = self.checker.get_balances('0xtest')
            self.checker.print_balances(balances)
            
            # Verify print was called with expected headers
            mock_print.assert_any_call("\n=== Token Balances ===")
            mock_print.assert_any_call("\n🟢 sDAI (Currency):")
            mock_print.assert_any_call("\n🔵 GNO (Company):")
            mock_print.assert_any_call("\n🟣 waGNO (Wrapped GNO):")
    
    @patch('web3.Web3.HTTPProvider')
    def test_get_web3(self, mock_provider):
        """Test Web3 initialization."""
        # Mock successful connection
        mock_provider.return_value.is_connected.return_value = True
        w3 = get_web3()
        self.assertIsNotNone(w3)
        
        # Mock failed connection
        mock_provider.return_value.is_connected.return_value = False
        with self.assertRaises(ConnectionError):
            get_web3()
    
    @patch('os.getenv')
    def test_get_address_from_env(self, mock_getenv):
        """Test getting address from environment."""
        # Test with no private key
        mock_getenv.return_value = None
        self.assertIsNone(get_address_from_env())
        
        # Test with valid private key
        mock_getenv.return_value = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        address = get_address_from_env()
        self.assertIsNotNone(address)
        self.assertTrue(address.startswith('0x'))
    
    @patch('futarchy.balance_checker.get_web3')
    @patch('futarchy.balance_checker.get_address_from_env')
    def test_get_balances_helper(self, mock_get_address, mock_get_web3):
        """Test the get_balances helper function."""
        # Mock Web3 instance
        mock_get_web3.return_value = self.w3
        
        # Test with explicit address
        balances = get_balances('0xtest')
        self.assertIsNotNone(balances)
        
        # Test with address from env
        mock_get_address.return_value = '0xtest'
        balances = get_balances()
        self.assertIsNotNone(balances)
        
        # Test with no address available
        mock_get_address.return_value = None
        with self.assertRaises(ValueError):
            get_balances()

if __name__ == '__main__':
    unittest.main() 