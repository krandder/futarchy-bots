# Import this at the top of exchanges/cowswap.py
import os
import json
import time
import requests
import sys

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import time
import json
from eth_utils import to_checksum_address
from eth_account.messages import encode_defunct
from config.constants import COWSWAP_API_URL, CONTRACT_ADDRESSES
from utils.web3_utils import get_raw_transaction


class CowSwapExchange:
    """Class for interacting with CoW Swap API"""

    def __init__(self, bot):
        """
        Initialize CowSwap exchange handler.
        
        Args:
            bot: FutarchyBot instance with web3 connection and account
        """
        self.bot = bot
        self.w3 = bot.w3
        self.account = bot.account
        self.address = bot.address
        self.settlement_contract = CONTRACT_ADDRESSES["cowSettlement"]
    

    def create_order_digest(self, order, chain_id=100):
        """
        Create an order digest strictly following EIP-712 implementation.
        
        Args:
            order: Order parameters
            chain_id: Chain ID (100 for Gnosis Chain)
            
        Returns:
            str: Order digest hex string
        """
        try:
            from eth_utils import keccak, to_bytes
            import json
            
            print("Creating EIP-712 order digest...")
            
            # 1. Create domain separator
            domain_data = {
                "name": "Gnosis Protocol",
                "version": "v2",
                "chainId": chain_id,
                "verifyingContract": CONTRACT_ADDRESSES["cowSettlement"]
            }
            
            # 2. Encode the domain - EXACTLY as specified in EIP-712
            domain_type_hash = keccak(to_bytes(text="EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"))
            name_hash = keccak(to_bytes(text=domain_data["name"]))
            version_hash = keccak(to_bytes(text=domain_data["version"]))
            
            domain_separator = keccak(
                domain_type_hash +
                name_hash +
                version_hash +
                int(domain_data["chainId"]).to_bytes(32, byteorder='big') +
                bytes.fromhex(domain_data["verifyingContract"][2:].rjust(64, '0'))
            )
            
            print(f"Domain separator: 0x{domain_separator.hex()}")
            
            # 3. Define the complete Order type hash using exact string representation from CoW Swap
            # The exact string representation is critical
            order_type_string = "Order(" + \
                "address sellToken," + \
                "address buyToken," + \
                "uint256 sellAmount," + \
                "uint256 buyAmount," + \
                "uint32 validTo," + \
                "bytes32 appData," + \
                "uint256 feeAmount," + \
                "string kind," + \
                "bool partiallyFillable," + \
                "address receiver" + \
                ")"
            order_type_hash = keccak(to_bytes(text=order_type_string))
            
            print(f"Order type string: {order_type_string}")
            print(f"Order type hash: 0x{order_type_hash.hex()}")
            
            # 4. Important: normalize the data
            # Ensure addresses are checksummed
            sell_token = self.w3.to_checksum_address(order["sellToken"])
            buy_token = self.w3.to_checksum_address(order["buyToken"])
            # Ensure receiver is set (default to the sender if not specified)
            receiver = self.w3.to_checksum_address(order.get("receiver", self.address))
            
            # 5. Hash the string "kind" value
            kind_hash = keccak(to_bytes(text=order["kind"]))
            
            # 6. Encode the order data EXACTLY as specified in EIP-712
            # Each element must be exactly 32 bytes
            encoded_data = b''
            # Add typeHash
            encoded_data += order_type_hash
            # Add sellToken (address)
            encoded_data += bytes.fromhex(sell_token[2:].rjust(64, '0'))
            # Add buyToken (address)
            encoded_data += bytes.fromhex(buy_token[2:].rjust(64, '0'))
            # Add sellAmount (uint256)
            encoded_data += int(order["sellAmount"]).to_bytes(32, byteorder='big')
            # Add buyAmount (uint256)
            encoded_data += int(order["buyAmount"]).to_bytes(32, byteorder='big')
            # Add validTo (uint32 - but padded to 32 bytes)
            encoded_data += int(order["validTo"]).to_bytes(32, byteorder='big')
            # Add appData (bytes32)
            encoded_data += bytes.fromhex(order["appData"][2:])
            # Add feeAmount (uint256)
            encoded_data += int(order["feeAmount"]).to_bytes(32, byteorder='big')
            # Add kind (string - hashed)
            encoded_data += kind_hash
            # Add partiallyFillable (bool)
            encoded_data += (1).to_bytes(32, byteorder='big') if order["partiallyFillable"] else (0).to_bytes(32, byteorder='big')
            # Add receiver (address)
            encoded_data += bytes.fromhex(receiver[2:].rjust(64, '0'))
            
            # 7. Hash the encoded data
            struct_hash = keccak(encoded_data)
            print(f"Struct hash: 0x{struct_hash.hex()}")
            
            # 8. Create the final EIP-712 digest
            # "\x19\x01" ‖ domainSeparator ‖ hashStruct(message)
            eip712_prefix = b"\x19\x01"
            digest = keccak(eip712_prefix + domain_separator + struct_hash)
            
            digest_hex = f"0x{digest.hex()}"
            print(f"Final EIP-712 digest: {digest_hex}")
            
            return digest_hex
            
        except Exception as e:
            print(f"❌ Error creating order digest: {e}")
            import traceback
            traceback.print_exc()
            return None

    def create_order_digest_v2(self, order, chain_id=100):
        """
        Create an order digest following the exact CoW Protocol EIP-712 implementation.
        
        Args:
            order: Order parameters
            chain_id: Chain ID (100 for Gnosis Chain)
            
        Returns:
            str: Order digest hex string
        """
        try:
            from eth_utils import keccak, to_bytes
            import json
            
            print("Creating EIP-712 order digest...")
            
            # 1. Create domain separator exactly matching CoW Protocol's structure
            domain_data = {
                "name": "Gnosis Protocol",
                "version": "v2",
                "chainId": chain_id,
                "verifyingContract": "0x9008D19f58AAbD9eD0D60971565AA8510560ab41"
            }
            
            print(f"Domain data: {json.dumps(domain_data, indent=2)}")
            
            # 2. Hash the domain exactly like CoW Protocol does
            # Using ethers.js _TypedDataEncoder.hashDomain approach
            from eth_account._utils.structured_data import encode_data
            from eth_utils import to_checksum_address
            
            # Order type string exactly matching CoW Protocol's structure
            order_type = [
                {"name": "sellToken", "type": "address"},
                {"name": "buyToken", "type": "address"},
                {"name": "receiver", "type": "address"},
                {"name": "sellAmount", "type": "uint256"},
                {"name": "buyAmount", "type": "uint256"},
                {"name": "validTo", "type": "uint32"},
                {"name": "appData", "type": "bytes32"},
                {"name": "feeAmount", "type": "uint256"},
                {"name": "kind", "type": "string"},
                {"name": "partiallyFillable", "type": "bool"},
                {"name": "sellTokenBalance", "type": "string"},
                {"name": "buyTokenBalance", "type": "string"},
            ]
            
            # Define EIP-712 type data
            type_data = {
                "types": {
                    "EIP712Domain": [
                        {"name": "name", "type": "string"},
                        {"name": "version", "type": "string"},
                        {"name": "chainId", "type": "uint256"},
                        {"name": "verifyingContract", "type": "address"},
                    ],
                    "Order": order_type,
                },
                "primaryType": "Order",
                "domain": domain_data,
                "message": {
                    "sellToken": to_checksum_address(order["sellToken"]),
                    "buyToken": to_checksum_address(order["buyToken"]),
                    "receiver": to_checksum_address(order.get("receiver", self.address)),
                    "sellAmount": order["sellAmount"],
                    "buyAmount": order["buyAmount"],
                    "validTo": order["validTo"],
                    "appData": order["appData"],
                    "feeAmount": order["feeAmount"],
                    "kind": order["kind"],
                    "partiallyFillable": order["partiallyFillable"],
                    "sellTokenBalance": order.get("sellTokenBalance", "erc20"),
                    "buyTokenBalance": order.get("buyTokenBalance", "erc20"),
                }
            }
            
            # Use eth_account's EIP-712 implementation
            from eth_account._utils.structured_data import hash_domain
            from eth_account._utils.structured_data import hash_structured_data
            
            # Calculate the domain separator
            domain_hash = hash_domain(type_data)
            print(f"Domain separator: 0x{domain_hash.hex()}")
            
            # Calculate the structured data hash
            structured_hash = hash_structured_data(type_data)
            print(f"Structured hash: 0x{structured_hash.hex()}")
            
            # Final digest is prefix + domain_hash + structured_hash
            eip712_prefix = b"\x19\x01"
            final_digest = keccak(eip712_prefix + domain_hash + structured_hash)
            
            digest_hex = f"0x{final_digest.hex()}"
            print(f"Final EIP-712 digest: {digest_hex}")
            
            return digest_hex
            
        except Exception as e:
            print(f"❌ Error creating order digest: {e}")
            import traceback
            traceback.print_exc()
            return None


    def compare_order_hashes(self, quote_result, expected_hash=None):
        """
        Compare our calculated order hash with CoW Swap's expected hash.
        
        Args:
            quote_result: Quote data from CoW Swap
            expected_hash: Expected hash from error message (optional)
            
        Returns:
            dict: Comparison results
        """
        quote = quote_result["quote"]
        
        # Create order from quote
        order = {
            "sellToken": quote["sellToken"],
            "buyToken": quote["buyToken"],
            "sellAmount": quote["sellAmount"],
            "buyAmount": quote["buyAmount"],
            "validTo": quote["validTo"],
            "appData": quote["appData"],
            "feeAmount": quote["feeAmount"],
            "kind": quote["kind"],
            "partiallyFillable": quote["partiallyFillable"],
            "receiver": self.address if quote.get("receiver") is None else quote["receiver"],
            "from": self.address
        }
        
        # Calculate our order digest
        our_digest = self.create_order_digest(order)
        
        # Compare with expected hash if provided
        if expected_hash:
            match = our_digest.lower() == expected_hash.lower()
            print(f"\nDigest match: {match}")
            print(f"Our digest:    {our_digest}")
            print(f"Expected hash: {expected_hash}")
            
            if not match:
                print("\nTrying alternative order representations...")
                
                # Try different variations of the order
                variations = []
                
                # Variation 1: Without "from" field
                order_var1 = {k: v for k, v in order.items() if k != "from"}
                digest_var1 = self.create_order_digest(order_var1)
                match_var1 = digest_var1.lower() == expected_hash.lower()
                variations.append(("Without 'from' field", digest_var1, match_var1))
                
                # Variation 2: With lowercase addresses
                order_var2 = {**order}
                for field in ["sellToken", "buyToken", "receiver"]:
                    if field in order_var2 and order_var2[field]:
                        order_var2[field] = order_var2[field].lower()
                digest_var2 = self.create_order_digest(order_var2)
                match_var2 = digest_var2.lower() == expected_hash.lower()
                variations.append(("Lowercase addresses", digest_var2, match_var2))
                
                # Print results
                print("\nVariation results:")
                for desc, digest, match in variations:
                    result = "✅ MATCH" if match else "❌ NO MATCH"
                    print(f"{result} - {desc}: {digest}")
        
        return {
            "our_digest": our_digest,
            "expected_hash": expected_hash,
            "match": our_digest.lower() == expected_hash.lower() if expected_hash else None
        }

    
    def test_libraries(self):
        """Test which signing libraries are available"""
        print("\n===== TESTING AVAILABLE LIBRARIES =====")
        
        libraries = {
            "eth_account": False,
            "eth_account.messages": False,
            "eth_account.messages.encode_defunct": False,
            "eth_account._utils.structured_data": False,
            "eth_abi": False,
            "coincurve": False,
            "eth_utils": False,
            "eth_utils.keccak": False
        }
        
        # Test eth_account
        try:
            import eth_account
            libraries["eth_account"] = True
            print("✅ eth_account is available")
            
            # Test eth_account.messages
            try:
                from eth_account import messages
                libraries["eth_account.messages"] = True
                print("✅ eth_account.messages is available")
                
                # Test encode_defunct
                try:
                    from eth_account.messages import encode_defunct
                    libraries["eth_account.messages.encode_defunct"] = True
                    print("✅ eth_account.messages.encode_defunct is available")
                except ImportError:
                    print("❌ eth_account.messages.encode_defunct is not available")
            except ImportError:
                print("❌ eth_account.messages is not available")
            
            # Test structured_data
            try:
                from eth_account._utils import structured_data
                libraries["eth_account._utils.structured_data"] = True
                print("✅ eth_account._utils.structured_data is available")
            except ImportError:
                print("❌ eth_account._utils.structured_data is not available")
        except ImportError:
            print("❌ eth_account is not available")
        
        # Test eth_abi
        try:
            import eth_abi
            libraries["eth_abi"] = True
            print("✅ eth_abi is available")
        except ImportError:
            print("❌ eth_abi is not available")
        
        # Test coincurve
        try:
            import coincurve
            libraries["coincurve"] = True
            print("✅ coincurve is available")
        except ImportError:
            print("❌ coincurve is not available")
        
        # Test eth_utils
        try:
            import eth_utils
            libraries["eth_utils"] = True
            print("✅ eth_utils is available")
            
            # Test keccak
            try:
                from eth_utils import keccak
                libraries["eth_utils.keccak"] = True
                print("✅ eth_utils.keccak is available")
            except ImportError:
                print("❌ eth_utils.keccak is not available")
        except ImportError:
            print("❌ eth_utils is not available")
        
        print("\nLibrary availability summary:")
        for lib, available in libraries.items():
            status = "✅ Available" if available else "❌ Not available"
            print(f"{lib}: {status}")
        
        print("===== END OF LIBRARY TEST =====\n")
        return libraries
        pass
    
    def get_quote(self, sell_token, buy_token, sell_amount):
        """
        Get a quote for swapping tokens from CoW Swap.
        
        Args:
            sell_token: Address of token to sell
            buy_token: Address of token to buy
            sell_amount: Amount to sell in base units (wei)
            
        Returns:
            dict: Quote data or None if request fails
        """
        try:
            print("Requesting quote from CoW Swap...")
            quote_url = f"{COWSWAP_API_URL}/api/v1/quote"
            quote_data = {
                "sellToken": sell_token,
                "buyToken": buy_token,
                "sellAmountBeforeFee": str(sell_amount),
                "from": self.address,
                "kind": "sell"
            }
            
            quote_response = requests.post(quote_url, json=quote_data)
            
            if quote_response.status_code != 200:
                print(f"❌ Failed to get quote: {quote_response.text}")
                return None
                
            quote_result = quote_response.json()
            print(f"Quote result: {quote_result}")
            
            if "quote" not in quote_result:
                print(f"❌ Invalid quote response: {quote_result}")
                return None
                
            # Extract and print the quote data
            quote = quote_result["quote"]
            print(f"Quote received:")
            print(f"- Sell amount: {quote['sellAmount']}")
            print(f"- Buy amount: {quote['buyAmount']}")
            print(f"- Fee amount: {quote['feeAmount']}")
            
            return quote_result
            
        except Exception as e:
            print(f"❌ Error getting quote: {e}")
            return None
    
    def sign_with_ethsign(self, message_text):
        """
        Sign a message using the ethsign (personal_sign) format.
        
        Args:
            message_text: Text to sign
            
        Returns:
            str: Signature or None if signing fails
        """
        try:
            # Sign with ethsign (personal_sign) format
            message = encode_defunct(text=message_text)
            signed = self.w3.eth.account.sign_message(message, private_key=self.account.key)
            signature = signed.signature.hex()
            
            # Make sure signature has 0x prefix
            if not signature.startswith('0x'):
                signature = '0x' + signature
                
            print(f"ethsign Signature: {signature}")
            return signature
            
        except Exception as e:
            print(f"❌ Error signing with ethsign: {e}")
            return None
        


    def sign_with_eip712(self, digest):
        """
        Sign a digest using EIP-712.
        
        Args:
            digest: Digest to sign (hex string)
            
        Returns:
            str: Signature hex string
        """
        try:
            # Convert the digest to bytes
            digest_hex = digest[2:] if digest.startswith('0x') else digest
            digest_bytes = bytes.fromhex(digest_hex)
            
            # Use eth_account.messages.encode_defunct with hexstr
            from eth_account.messages import encode_defunct
            message = encode_defunct(hexstr=digest)
            
            # Sign the message
            signed = self.w3.eth.account.sign_message(message, private_key=self.account.key)
            signature = signed.signature.hex()
            
            # Ensure 0x prefix
            if not signature.startswith('0x'):
                signature = '0x' + signature
                
            print(f"EIP-712 signature: {signature}")
            
            # Verify the signature
            recovered = self.w3.eth.account.recover_message(message, signature=signature)
            print(f"Recovered address: {recovered}")
            print(f"Our address: {self.address}")
            print(f"Match: {recovered.lower() == self.address.lower()}")
            
            return signature
        except Exception as e:
            print(f"❌ Error signing with EIP-712: {e}")
            import traceback
            traceback.print_exc()
            return None


    def create_order_with_ethsign(self, quote_result, expected_hash=None):
        """
        Create an order using ethsign signing scheme.
        
        Args:
            quote_result: Quote data from get_quote
            expected_hash: Expected hash from error message (optional)
            
        Returns:
            dict: Order data or None if creation fails
        """
        try:
            quote = quote_result["quote"]
            
            # Create the order struct
            order = {
                "sellToken": quote["sellToken"],
                "buyToken": quote["buyToken"],
                "sellAmount": quote["sellAmount"],
                "buyAmount": quote["buyAmount"],
                "validTo": quote["validTo"],
                "appData": quote["appData"],
                "feeAmount": quote["feeAmount"],
                "kind": quote["kind"],
                "partiallyFillable": quote["partiallyFillable"],
                "receiver": self.address if quote.get("receiver") is None else quote["receiver"],
                "from": self.address
            }
            
            # Use the expected hash directly if provided
            digest_to_sign = expected_hash if expected_hash else self.create_order_digest(order)
            if not digest_to_sign:
                print("❌ Failed to get order digest")
                return None
            
            # Sign using standard eth_sign approach
            from eth_account.messages import encode_defunct
            message = encode_defunct(hexstr=digest_to_sign)
            signature = self.w3.eth.account.sign_message(message, private_key=self.account.key).signature.hex()
            
            if not signature.startswith('0x'):
                signature = '0x' + signature
                
            print(f"ethsign Signature: {signature}")
            
            # Verify the signature
            recovered = self.w3.eth.account.recover_message(message, signature=signature)
            print(f"Recovered address: {recovered}")
            print(f"Our address: {self.address}")
            print(f"Match: {recovered.lower() == self.address.lower()}")
            
            # Create the order
            final_order = {
                "sellToken": quote["sellToken"],
                "buyToken": quote["buyToken"],
                "sellAmount": quote["sellAmount"],
                "buyAmount": quote["buyAmount"],
                "validTo": quote["validTo"],
                "appData": quote["appData"],
                "feeAmount": quote["feeAmount"],
                "kind": quote["kind"],
                "partiallyFillable": quote["partiallyFillable"],
                "receiver": self.address if quote.get("receiver") is None else quote["receiver"],
                "from": self.address,
                "sellTokenBalance": quote["sellTokenBalance"],
                "buyTokenBalance": quote["buyTokenBalance"],
                "signingScheme": "ethsign",
                "signature": signature
            }
            
            return final_order
            
        except Exception as e:
            print(f"❌ Error creating ethsign order: {e}")
            import traceback
            traceback.print_exc()
            return None

    
    def create_order_with_presign(self, sell_token, buy_token, sell_amount, buy_amount, validity_hours=24):
        """
        Create an order using presign signing scheme (fallback).
        
        Args:
            sell_token: Address of token to sell
            buy_token: Address of token to buy
            sell_amount: Amount to sell in base units (wei)
            buy_amount: Amount to buy in base units (wei)
            validity_hours: How long the order is valid for in hours
            
        Returns:
            dict: Order data
        """
        try:
            # Calculate validity timestamp
            now = int(time.time())
            valid_to = now + (validity_hours * 60 * 60)
            
            # Create the order
            order = {
                "sellToken": to_checksum_address(sell_token),
                "buyToken": to_checksum_address(buy_token),
                "sellAmount": str(sell_amount),
                "buyAmount": str(buy_amount),
                "validTo": valid_to,
                "appData": "0x0000000000000000000000000000000000000000000000000000000000000000",
                "feeAmount": "0",  # Fee must be zero for presign
                "kind": "sell",
                "partiallyFillable": False,
                "receiver": self.address,
                "from": self.address,
                "sellTokenBalance": "erc20",
                "buyTokenBalance": "erc20",
                "signingScheme": "presign",
                "signature": "0x"  # Empty signature for presign
            }
            
            print(f"Created presigned order: {order}")
            return order
            
        except Exception as e:
            print(f"❌ Error creating presign order: {e}")
            return None
    

    def create_order(self, sell_token, buy_token, sell_amount, buy_amount_min, validity_hours=24, expected_hash=None):
        """
        Create and sign an order for CoW Swap.
        
        Args:
            sell_token: Address of token to sell
            buy_token: Address of token to buy
            sell_amount: Amount to sell in base units (wei)
            buy_amount_min: Minimum amount to receive in base units (wei)
            validity_hours: How long the order is valid for in hours
            expected_hash: Expected hash from error message (optional)
            
        Returns:
            dict: Signed order ready for submission or None if failed
        """
        if self.account is None:
            raise ValueError("No account configured for transactions")
        
        # Convert addresses to checksum format
        sell_token = to_checksum_address(sell_token)
        buy_token = to_checksum_address(buy_token)
        
        print(f"Creating order to sell {sell_amount} of {sell_token} for at least {buy_amount_min} of {buy_token}")
        
        # Step 1: Get a quote
        quote_result = self.get_quote(sell_token, buy_token, sell_amount)
        
        if not quote_result:
            return None
            
        quote = quote_result["quote"]
        
        # Check if the quoted buy amount is acceptable
        if int(quote["buyAmount"]) < int(buy_amount_min):
            print(f"❌ Quoted buy amount {quote['buyAmount']} is less than minimum {buy_amount_min}")
            return None
        
        # Step 2: Try the different signing methods
        
        # If we have an expected hash, use that directly
        if expected_hash:
            print("\n--- Using provided expected hash for signing ---")
            order = self.create_order_with_ethsign(quote_result, expected_hash)
            if order:
                return order
        
        # Otherwise try normal ethsign
        print("\n--- Trying ethsign method ---")
        order = self.create_order_with_ethsign(quote_result)
        
        if order:
            return order
            
        # If all else fails, fall back to presign
        print("\n--- Falling back to presign method ---")
        return self.create_order_with_presign(
            sell_token, 
            buy_token, 
            sell_amount,  # Use original amount for presign
            quote["buyAmount"],
            validity_hours=24
        )
    
    def submit_order(self, order):
        """
        Submit a signed order to CoW Swap.
        
        Args:
            order: Signed order dict
            
        Returns:
            str: Order UID if successful, None otherwise
        """
        try:
            print("Submitting order to CoW Swap...")
            submit_url = f"{COWSWAP_API_URL}/api/v1/orders"
            
            # Print the order for debugging
            print(f"Order data: {order}")
            
            # Special handling for presign orders
            if order.get("signingScheme") == "presign":
                print("\n===== PRESIGNED ORDER INFORMATION =====")
                print("This is a presigned order. After submission, you will need to:")
                print("1. Visit the Explorer URL to view your order")
                print("2. Connect your wallet to the Explorer")
                print("3. Click the 'Sign Order' button to confirm the transaction")
                print("4. The order will be executed when a solver includes it in a batch")
                print("======================================\n")
                
            # Make the submission request
            response = requests.post(submit_url, json=order)
            
            print(f"Response status: {response.status_code}")
            print(f"Response text: {response.text}")
            
            if response.status_code == 200 or response.status_code == 201:
                try:
                    # If the response is a string, use it directly
                    if isinstance(response.text, str) and response.text.startswith('"0x'):
                        # Remove the quotes if present
                        order_uid = response.text.strip('"')
                        print(f"✅ Order submitted successfully! Order UID: {order_uid}")
                        print(f"   Explorer URL: https://explorer.cow.fi/orders/{order_uid}?tab=overview&network=xdai")
                        return order_uid
                    
                    # Otherwise, try to parse as JSON
                    order_data = response.json()
                    
                    # Extract order UID/ID
                    if isinstance(order_data, dict) and "id" in order_data:
                        order_uid = order_data["id"]
                    elif isinstance(order_data, str) and order_data.startswith("0x"):
                        order_uid = order_data
                    else:
                        order_uid = str(order_data)  # Fallback
                    
                    print(f"✅ Order submitted successfully! Order UID: {order_uid}")
                    print(f"   Explorer URL: https://explorer.cow.fi/orders/{order_uid}?tab=overview&network=xdai")
                    return order_uid
                except ValueError:
                    # If the response is not valid JSON but status code is OK, 
                    # it might still be successful
                    if response.text and '"0x' in response.text:
                        order_uid = response.text.strip('"')
                        print(f"✅ Order submitted, UID from text: {order_uid}")
                        print(f"   Explorer URL: https://explorer.cow.fi/orders/{order_uid}?tab=overview&network=xdai")
                        return order_uid
                    return None
            else:
                print(f"❌ Order submission error: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error submitting order: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def check_order_status(self, order_uid):
        """
        Check the status of a CoW Swap order.
        
        Args:
            order_uid: The UID of the order to check
            
        Returns:
            dict: Order status information or None if check fails
        """
        try:
            print(f"Checking order status for {order_uid}...")
            response = requests.get(f"{COWSWAP_API_URL}/api/v1/orders/{order_uid}")
            
            if response.status_code == 200:
                order_data = response.json()
                status = order_data.get("status")
                print(f"Order status: {status}")
                return order_data
            else:
                print(f"❌ Error checking order status: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error checking order status: {e}")
            return None
    
    def estimate_price(self, sell_token, buy_token, sell_amount):
        """
        Estimate price for a swap without creating an order.
        
        Args:
            sell_token: Address of token to sell
            buy_token: Address of token to buy
            sell_amount: Amount to sell in base units (wei)
            
        Returns:
            dict: Price information or None if failed
        """
        quote_result = self.get_quote(sell_token, buy_token, sell_amount)
        
        if not quote_result or "quote" not in quote_result:
            return None
            
        quote = quote_result["quote"]
        
        # Extract and calculate price information
        result = {
            "sellAmount": quote.get("sellAmount"),
            "buyAmount": quote.get("buyAmount"),
            "fee": quote.get("feeAmount"),
            "feePercent": None
        }
        
        # Calculate price
        if "buyAmount" in quote and "sellAmount" in quote:
            sell_amount_after_fee = int(quote["sellAmount"])
            buy_amount = int(quote["buyAmount"])
            
            if sell_amount_after_fee > 0:
                # Calculate price: how much buy token per sell token
                price = sell_amount_after_fee / buy_amount
                result["price"] = price
                print(f"Estimated price: {price} (sell token per buy token)")
                
                # Calculate fee percent
                if "feeAmount" in quote:
                    fee_amount = int(quote["feeAmount"])
                    if sell_amount_after_fee + fee_amount > 0:
                        fee_percent = fee_amount / (sell_amount_after_fee + fee_amount)
                        result["feePercent"] = fee_percent
                        print(f"Fee percent: {fee_percent * 100:.4f}%")
        
        return result

    def sign_order_with_eip712(self, order_digest):
        """
        Sign an order digest using EIP-712.
        
        Args:
            order_digest: Order digest to sign
            
        Returns:
            str: Signature hex string
        """
        try:
            from eth_account.messages import encode_defunct
            
            # Remove 0x prefix if present
            digest_hex = order_digest[2:] if order_digest.startswith('0x') else order_digest
            digest_bytes = bytes.fromhex(digest_hex)
            
            # Method 1: Using encode_defunct with hexstr
            # This still adds the Ethereum signed message prefix
            message = encode_defunct(hexstr=order_digest)
            signature = self.w3.eth.account.sign_message(message, private_key=self.account.key)
            sig_hex = signature.signature.hex()
            
            if not sig_hex.startswith('0x'):
                sig_hex = '0x' + sig_hex
                
            print(f"EIP-712 signature: {sig_hex}")
            
            # Verify the signature by recovering the address
            recovered = self.w3.eth.account.recover_message(message, signature=sig_hex)
            print(f"Recovered address: {recovered}")
            print(f"Our address: {self.address}")
            print(f"Match: {recovered.lower() == self.address.lower()}")
            
            return sig_hex
            
        except Exception as e:
            print(f"❌ Error signing with EIP-712: {e}")
            import traceback
            traceback.print_exc()
            return None
            
    def create_order_with_eip712(self, quote_result):
        """
        Create an order using EIP-712 signing scheme.
        
        Args:
            quote_result: Quote data from get_quote
            
        Returns:
            dict: Order data or None if creation fails
        """
        try:
            quote = quote_result["quote"]
            
            # Create order structure exactly matching CoW Swap's expected format
            order = {
                "sellToken": quote["sellToken"],
                "buyToken": quote["buyToken"],
                "sellAmount": quote["sellAmount"],
                "buyAmount": quote["buyAmount"],
                "validTo": quote["validTo"],
                "appData": quote["appData"],
                "feeAmount": quote["feeAmount"],
                "kind": quote["kind"],
                "partiallyFillable": quote["partiallyFillable"],
                "receiver": self.address if quote.get("receiver") is None else quote["receiver"],
                "from": self.address
            }
            
            # Calculate the order digest
            order_digest = self.create_order_digest(order)
            if not order_digest:
                print("❌ Failed to create order digest")
                return None
            
            # Sign with EIP-712
            signature = self.sign_with_eip712(order_digest)
            if not signature:
                print("❌ Failed to sign order digest")
                return None
            
            # Create the complete order with signature
            final_order = {
                "sellToken": quote["sellToken"],
                "buyToken": quote["buyToken"],
                "sellAmount": quote["sellAmount"],
                "buyAmount": quote["buyAmount"],
                "validTo": quote["validTo"],
                "appData": quote["appData"],
                "feeAmount": quote["feeAmount"],
                "kind": quote["kind"],
                "partiallyFillable": quote["partiallyFillable"],
                "receiver": self.address if quote.get("receiver") is None else quote["receiver"],
                "from": self.address,
                "sellTokenBalance": quote["sellTokenBalance"],
                "buyTokenBalance": quote["buyTokenBalance"],
                "signingScheme": "eip712",  # Use eip712 scheme here, not ethsign
                "signature": signature
            }
            
            print(f"✅ Order created with EIP-712 signature: {final_order}")
            return final_order
            
        except Exception as e:
            print(f"❌ Error creating EIP-712 order: {e}")
            import traceback
            traceback.print_exc()
            return None
            

    def test_fixed_order_signing(self):
        """
        Test signing a completely fixed order to debug the hash calculation.
        
        Returns:
            dict: Results of the test
        """
        try:
            print("\n=== TESTING FIXED ORDER SIGNING ===")
            
            # Create a completely fixed order (all values hard-coded)
            fixed_order = {
                "sellToken": "0xaf204776c7245bf4147c2612bf6e5972ee483701",  # sDAI
                "buyToken": "0x9c58bacc331c9aa871afd802db6379a98e80cedb",   # GNO
                "sellAmount": "100000000000000000",  # 0.1 sDAI
                "buyAmount": "900000000000000",      # Fixed buy amount
                "validTo": 1741670000,               # Fixed valid to timestamp (far in the future)
                "appData": "0x0000000000000000000000000000000000000000000000000000000000000000",
                "feeAmount": "1000000000000",        # Fixed fee
                "kind": "sell",                      # Always sell
                "partiallyFillable": False,          # Not partially fillable
                "receiver": self.address,            # Our address as receiver
                "from": self.address,                # Our address as sender
                "sellTokenBalance": "erc20",
                "buyTokenBalance": "erc20"
            }
            
            print(f"Fixed order: {json.dumps(fixed_order, indent=2)}")
            
            # Calculate our order digest
            print("\nCalculating our EIP-712 order digest...")
            our_digest = self.create_order_digest(fixed_order)
            print(f"Our calculated digest: {our_digest}")
            
            # Sign the order with EIP-712
            signature = self.sign_with_eip712(our_digest)
            if not signature:
                print("❌ Failed to sign order digest")
                return None
                
            # Create the complete order with the CORRECT signing scheme (eip712)
            final_order = {
                **fixed_order,
                "signingScheme": "eip712",  # IMPORTANT: Use eip712, not ethsign
                "signature": signature
            }
            
            # Ask for expected hash
            expected_hash = input("\nEnter expected hash from error message (or press Enter to submit without hash): ")
            
            if expected_hash and expected_hash.startswith("0x"):
                print(f"\nComparing our digest with expected hash:")
                print(f"Our digest:     {our_digest}")
                print(f"Expected hash:  {expected_hash}")
                print(f"Match: {our_digest.lower() == expected_hash.lower()}")
                
                # If they don't match, sign the expected hash instead
                if our_digest.lower() != expected_hash.lower():
                    print("\nSigning the expected hash instead...")
                    signature = self.sign_with_eip712(expected_hash)
                    if signature:
                        final_order["signature"] = signature
            
            # Ask whether to submit
            submit = input("\nSubmit this fixed order? (y/n): ")
            if submit.lower() == 'y':
                print(f"Submitting fixed order with signingScheme: {final_order['signingScheme']}")
                result = self.submit_order(final_order)
                return result
                
            return {
                "our_digest": our_digest,
                "expected_hash": expected_hash if expected_hash else None,
                "order": final_order
            }
            
        except Exception as e:
            print(f"❌ Error in fixed order test: {e}")
            import traceback
            traceback.print_exc()
            return None
            

    def sign_cow_order(self, order):
        """
        Sign an order using CoW Protocol's EIP-712 implementation.
        
        Args:
            order: Order parameters
            
        Returns:
            tuple: (signature, signingScheme)
        """
        try:
            print("Signing order with CoW Protocol's EIP-712 implementation...")
            
            # Calculate the order digest
            digest = self.create_order_digest_v2(order)
            if not digest:
                print("❌ Failed to create order digest")
                return None, None
            
            # Use ethers.js compatible signing through eth_account
            from eth_account import Account
            from eth_account._utils.typed_data import TypedData
            
            # Prepare the type data
            type_data = {
                "types": {
                    "EIP712Domain": [
                        {"name": "name", "type": "string"},
                        {"name": "version", "type": "string"},
                        {"name": "chainId", "type": "uint256"},
                        {"name": "verifyingContract", "type": "address"},
                    ],
                    "Order": [
                        {"name": "sellToken", "type": "address"},
                        {"name": "buyToken", "type": "address"},
                        {"name": "receiver", "type": "address"},
                        {"name": "sellAmount", "type": "uint256"},
                        {"name": "buyAmount", "type": "uint256"},
                        {"name": "validTo", "type": "uint32"},
                        {"name": "appData", "type": "bytes32"},
                        {"name": "feeAmount", "type": "uint256"},
                        {"name": "kind", "type": "string"},
                        {"name": "partiallyFillable", "type": "bool"},
                        {"name": "sellTokenBalance", "type": "string"},
                        {"name": "buyTokenBalance", "type": "string"},
                    ],
                },
                "primaryType": "Order",
                "domain": {
                    "name": "Gnosis Protocol",
                    "version": "v2",
                    "chainId": 100,
                    "verifyingContract": "0x9008D19f58AAbD9eD0D60971565AA8510560ab41",
                },
                "message": {
                    "sellToken": self.w3.to_checksum_address(order["sellToken"]),
                    "buyToken": self.w3.to_checksum_address(order["buyToken"]),
                    "receiver": self.w3.to_checksum_address(order.get("receiver", self.address)),
                    "sellAmount": order["sellAmount"],
                    "buyAmount": order["buyAmount"],
                    "validTo": order["validTo"],
                    "appData": order["appData"],
                    "feeAmount": order["feeAmount"],
                    "kind": order["kind"],
                    "partiallyFillable": order["partiallyFillable"],
                    "sellTokenBalance": order.get("sellTokenBalance", "erc20"),
                    "buyTokenBalance": order.get("buyTokenBalance", "erc20"),
                }
            }
            
            # Sign the typed data
            private_key = self.account.key.hex() if hasattr(self.account.key, 'hex') else self.account.key
            if private_key.startswith('0x'):
                private_key = private_key[2:]
            
            # Create a signature using eth_account's sign_typed_data
            try:
                from eth_account import Account
                
                # Sign using eth_account directly
                account = Account.from_key(private_key)
                signature = account._sign_typed_data(type_data)
                
                # Format as hex string
                signature_hex = signature.signature.hex()
                if not signature_hex.startswith('0x'):
                    signature_hex = '0x' + signature_hex
                    
                print(f"EIP-712 signature: {signature_hex}")
                return signature_hex, "eip712"
                
            except Exception as sign_error:
                print(f"Error using _sign_typed_data: {sign_error}")
                
                # Fallback to using encode_defunct with the digest
                from eth_account.messages import encode_defunct
                
                message = encode_defunct(hexstr=digest)
                signed = self.w3.eth.account.sign_message(message, private_key=self.account.key)
                signature = signed.signature.hex()
                
                if not signature.startswith('0x'):
                    signature = '0x' + signature
                    
                print(f"Fallback signature: {signature}")
                return signature, "ethsign"
                
        except Exception as e:
            print(f"❌ Error signing order: {e}")
            import traceback
            traceback.print_exc()
            return None, None
            
    def create_and_sign_fixed_order_v2(self):
        """Test creating and signing a fixed order with CoW Protocol's exact EIP-712 implementation."""
        try:
            print("\n=== TESTING COW PROTOCOL EIP-712 SIGNING ===")
            
            # Create a fixed order that exactly matches their structure
            fixed_order = {
                "sellToken": "0xaf204776c7245bf4147c2612bf6e5972ee483701",  # sDAI
                "buyToken": "0x9c58bacc331c9aa871afd802db6379a98e80cedb",   # GNO
                "receiver": self.address,
                "sellAmount": "100000000000000000",  # 0.1 sDAI
                "buyAmount": "900000000000000",      # Fixed buy amount
                "validTo": 1741670000,               # Fixed valid to timestamp
                "appData": "0x0000000000000000000000000000000000000000000000000000000000000000",
                "feeAmount": "1000000000000",        # Fixed fee
                "kind": "sell",                      # Always sell
                "partiallyFillable": False,          # Not partially fillable
                "sellTokenBalance": "erc20",
                "buyTokenBalance": "erc20"
            }
            
            print(f"Fixed order: {json.dumps(fixed_order, indent=2)}")
            
            # Sign the order with their implementation
            signature, signing_scheme = self.sign_cow_order(fixed_order)
            
            if not signature:
                print("❌ Failed to sign order")
                return None
                
            # Create the final order
            final_order = {
                **fixed_order,
                "from": self.address,
                "signingScheme": signing_scheme,
                "signature": signature
            }
            
            # Ask if user wants to try submitting
            submit = input("\nSubmit this CoW Protocol signed order? (y/n): ")
            if submit.lower() == 'y':
                result = self.submit_order(final_order)
                return result
                
            return {
                "order": final_order,
                "signature": signature,
                "signing_scheme": signing_scheme
            }
            
        except Exception as e:
            print(f"❌ Error in CoW Protocol EIP-712 test: {e}")
            import traceback
            traceback.print_exc()
            return None