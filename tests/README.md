# Futarchy Bots Tests

This directory contains test scripts for the Futarchy Bots project. These tests are designed to verify the functionality of various components of the system.

## Available Tests

### Read-only Tests
- `test_balances.py`: Check token balances
- `test_permit2_status.py`: Check Permit2 authorization status

### Write Tests (modify state)
- `test_approve_sdai.py`: Approve sDAI for Permit2
- `test_create_permit.py`: Create Permit2 authorization for sDAI
- `test_swap_sdai_to_wagno.py`: Swap sDAI for waGNO
- `test_swap_wagno_to_sdai.py`: Swap waGNO for sDAI

### Conditional Token Tests
- `test_create_conditional_permit.py`: Create Permit2 authorization for conditional tokens
- `test_swap_sdai_yes_to_gno_yes.py`: Swap sDAI YES for GNO YES
- `test_swap_gno_yes_to_sdai_yes.py`: Swap GNO YES for sDAI YES
- `test_swap_sdai_yes_to_gno_no.py`: Swap sDAI YES for GNO NO
- `test_swap_gno_no_to_sdai_yes.py`: Swap GNO NO for sDAI YES

## Usage

### Running All Tests
```bash
python tests/run_all_tests.py
```

### Running Specific Test Categories
```bash
# Run read-only tests
python tests/run_all_tests.py --category read

# Run write tests
python tests/run_all_tests.py --category write

# Run conditional token tests
python tests/run_all_tests.py --category conditional
```

### Running Individual Tests
```bash
# Run a specific test
python tests/test_balances.py

# Run with verbose output
python tests/test_balances.py --verbose

# Run with a specific amount (for swap tests)
python tests/test_swap_sdai_to_wagno.py --amount 0.001
```

## Test Flow

For a complete test of the system, it's recommended to run the tests in the following order:

1. Read-only tests to check the current state
2. Write tests to modify the state
3. Conditional token tests to test conditional token functionality

```bash
# Run all tests in sequence
python tests/run_all_tests.py --verbose
```

## Notes

- The conditional token swap tests may fail with "SPL" errors, which likely means there's an issue with the SushiSwap pool liquidity or configuration.
- The Permit2 authorization for conditional tokens works correctly.
- The regular tests for swapping sDAI and waGNO are working correctly. 