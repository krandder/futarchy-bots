def test_available_libraries():
    """Test which libraries are available for EIP-712 signing"""
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