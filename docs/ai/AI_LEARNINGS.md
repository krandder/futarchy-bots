# AI Learnings and Insights

## Project Context
This document captures key learnings, insights, and goals while working on the Futarchy Bots project - a system for interacting with Balancer pools and conditional tokens on Gnosis Chain.

## Technical Insights

### Blockchain Integration Learnings

1. **Balancer V3 Architecture**:
   - The Balancer V3 architecture on Gnosis Chain uses a BatchRouter contract as the main entry point for swaps, rather than interacting directly with the Vault contract.
   - The BatchRouter provides functions like `swapExactIn` that handle the complexity of routing trades through pools.
   - Direct Vault interactions fail for certain pools, while BatchRouter interactions succeed.

2. **Permit2 Authorization Flow**:
   - Permit2 authorizations are specific to token-spender pairs.
   - Different spenders (BatchRouter vs. Balancer Vault) require separate Permit2 authorizations.
   - Permit2 authorizations have expiration times and nonces that need to be managed.
   - Permit2 authorizations work for conditional tokens (YES/NO tokens) in the same way as for regular tokens.

3. **Pool Liquidity Constraints**:
   - Small swaps (0.0001 tokens) succeed while larger swaps (0.01 tokens) fail, indicating limited liquidity in the pool.
   - This suggests the need for slippage protection and transaction size limits in production environments.
   - Conditional token swaps may fail with "SPL" errors, which likely indicates issues with SushiSwap pool liquidity or configuration.

4. **Contract Interaction Patterns**:
   - Query operations before executing transactions provide valuable information about expected outcomes.
   - Gas estimation failures often indicate that a transaction will fail on-chain.
   - Fallback mechanisms are important when interacting with external contracts.

5. **Conditional Tokens**:
   - Conditional tokens (YES/NO tokens) represent positions in prediction markets.
   - They can be traded on specialized pools like SushiSwap.
   - Permit2 authorizations work for conditional tokens, but the actual swaps may fail due to liquidity issues.
   - The balance structure for conditional tokens is nested: `balances["currency"]["yes"]` for sDAI YES tokens and `balances["company"]["no"]` for GNO NO tokens.

### Code Organization Insights

1. **Configuration Management**:
   - Separating user-specific information (private keys, RPC URLs) from constants (contract addresses, ABIs) improves security and maintainability.
   - Environment variables should be used for user-specific and sensitive information.
   - Constants files should contain non-sensitive, shared configuration values.

2. **Error Handling Strategies**:
   - Comprehensive error handling with informative messages helps diagnose issues.
   - Fallback mechanisms (like using default pool IDs) increase robustness.
   - Verbose logging options help with debugging complex interactions.

3. **Testing Structure**:
   - Organizing tests by category (read-only, write, conditional) helps with test management.
   - Creating a central test runner (`run_all_tests.py`) simplifies test execution.
   - Documenting test usage and flow in a README file helps users understand how to run tests.

## Collaboration Insights

1. **Effective Problem Solving Approach**:
   - When faced with failing transactions, comparing working implementations (simple_b_swap.py) with non-working ones (BalancerSwapHandler) revealed the key differences.
   - Testing with small amounts first helps identify issues before risking larger amounts.
   - Checking balances before and after operations confirms the success of transactions.

2. **Communication Patterns**:
   - Asking for guidance when uncertain about the correct approach is better than making assumptions.
   - Explaining the reasoning behind proposed changes helps build trust.
   - Providing detailed explanations of technical concepts helps bridge knowledge gaps.

## Goals for Future Improvement

1. **Short-term Goals**:
   - Implement better error handling for swap failures
   - Add support for multi-hop swaps through the BatchRouter
   - Improve gas estimation and optimization
   - Investigate and fix the "SPL" errors in conditional token swaps

2. **Medium-term Goals**:
   - Create comprehensive documentation for the Balancer integration
   - Implement automated tests for all swap scenarios
   - Add support for more token pairs
   - Improve the conditional token swap functionality

3. **Long-term Goals**:
   - Develop a more robust architecture for handling different DEXes
   - Implement price impact protection
   - Create a monitoring system for tracking swap performance
   - Build a comprehensive prediction market interface using conditional tokens

## Remarkable Instructions

1. **Guidance on Exchange Usage**:
   > "We should NOT use a different exchange! Don't make such decisions without approval."
   
   This instruction highlighted the importance of staying within project boundaries and not making architectural decisions without explicit approval.

2. **Problem-solving Approach**:
   > "Have you tested the simple_b_swap script? Is that one working? It used to work before."
   
   This guidance directed me to compare working implementations with non-working ones, which was key to identifying the solution.

3. **Asking for Help**:
   > "Its good that you are asking for guidance."
   
   This reinforced the value of acknowledging uncertainty and seeking guidance rather than proceeding with incomplete information.

## Progress Tracking

### 2025-03-05
- Successfully identified and fixed the issue with Balancer swaps
- Updated the BalancerSwapHandler to use the BatchRouter contract
- Confirmed that swaps work in both directions (sDAI to waGNO and waGNO to sDAI)
- Created this AI_LEARNINGS document to track insights and goals
- Verified that the menu interface works correctly with the updated BalancerSwapHandler

### 2025-03-06
- Created test scripts for conditional token swaps
- Created a test script for creating Permit2 authorizations for conditional tokens
- Updated the `run_all_tests.py` script to include conditional token tests
- Documented the test structure and usage in a README file
- Learned that Permit2 authorizations work for conditional tokens, but the actual swaps may fail due to liquidity issues

### Next Steps
- Review the entire codebase for similar patterns that might need updating
- Implement better error handling for swap failures
- Add support for multi-hop swaps if needed
- Improve documentation of the Balancer integration
- Investigate and fix the "SPL" errors in conditional token swaps

## Key Lessons for AI Assistants

1. **Comparative Analysis**:
   - When troubleshooting, comparing working implementations with non-working ones is a powerful diagnostic technique.
   - Look for subtle differences in approach rather than assuming fundamental flaws.

2. **Incremental Testing**:
   - Test with small values first before attempting larger operations.
   - Verify each step of a complex process independently.

3. **Boundary Recognition**:
   - Recognize when a decision exceeds your authority and requires user input.
   - Present options with pros and cons rather than making unilateral decisions on architecture.

4. **Documentation Value**:
   - Maintaining documentation like this file helps track progress and insights.
   - Recording unintuitive findings helps prevent repeating mistakes.

5. **Balance Between Initiative and Guidance**:
   - Take initiative to solve problems within established boundaries.
   - Seek guidance when facing architectural decisions or unexpected behavior.

6. **Structured Testing Approach**:
   - Organize tests by category to make them more manageable.
   - Create a central test runner to simplify test execution.
   - Document test usage and flow to help users understand how to run tests. 