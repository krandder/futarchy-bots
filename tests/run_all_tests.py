#!/usr/bin/env python3
"""
Script to run all tests in sequence.
This script allows running all tests or specific test categories.
"""

import os
import sys
import argparse
import subprocess

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_test(test_script, args):
    """Run a specific test script with the given arguments."""
    cmd = [sys.executable, test_script]
    
    if args.verbose:
        cmd.append('--verbose')
    
    if args.dry_run:
        cmd.append('--dry-run')
    
    print(f"\n{'='*50}")
    print(f"Running {os.path.basename(test_script)}")
    print(f"{'='*50}")
    
    result = subprocess.run(cmd)
    return result.returncode == 0

def main():
    """Run all tests or specific test categories."""
    parser = argparse.ArgumentParser(description='Run all tests or specific test categories')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Dry run (do not send transactions)')
    parser.add_argument('--category', '-c', choices=['read', 'write', 'conditional', 'all'], default='all',
                        help='Test category to run (read: read-only tests, write: tests that modify state, conditional: conditional token swaps, all: all tests)')
    args = parser.parse_args()
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define test scripts by category
    read_tests = [
        os.path.join(script_dir, 'test_balances.py'),
        os.path.join(script_dir, 'test_permit2_status.py')
    ]
    
    write_tests = [
        os.path.join(script_dir, 'test_approve_sdai.py'),
        os.path.join(script_dir, 'test_create_permit.py'),
        os.path.join(script_dir, 'test_swap_sdai_to_wagno.py'),
        os.path.join(script_dir, 'test_swap_wagno_to_sdai.py')
    ]
    
    conditional_tests = [
        os.path.join(script_dir, 'test_create_conditional_permit.py'),
        os.path.join(script_dir, 'test_swap_sdai_yes_to_gno_yes.py'),
        os.path.join(script_dir, 'test_swap_gno_yes_to_sdai_yes.py'),
        os.path.join(script_dir, 'test_swap_sdai_yes_to_gno_no.py'),
        os.path.join(script_dir, 'test_swap_gno_no_to_sdai_yes.py')
    ]
    
    # Determine which tests to run
    if args.category == 'read':
        tests_to_run = read_tests
    elif args.category == 'write':
        tests_to_run = write_tests
    elif args.category == 'conditional':
        tests_to_run = conditional_tests
    else:  # 'all'
        tests_to_run = read_tests + write_tests + conditional_tests
    
    # Run the tests
    success_count = 0
    failure_count = 0
    
    for test in tests_to_run:
        if run_test(test, args):
            success_count += 1
        else:
            failure_count += 1
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Test Summary: {success_count} succeeded, {failure_count} failed")
    print(f"{'='*50}")
    
    return 0 if failure_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main()) 