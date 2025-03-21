"""
Conditional token interface ABI.

This module is in DEVELOPMENT status.
Contains functions needed for splitting and merging conditional tokens.
"""

CONDITIONAL_TOKEN_ABI = [
    # splitPosition - to split tokens into conditional tokens
    {
        "inputs": [
            {"name": "collateralToken", "type": "address"},
            {"name": "parentCollectionId", "type": "bytes32"},
            {"name": "conditionId", "type": "bytes32"},
            {"name": "partition", "type": "uint256[]"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "splitPosition",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    # mergePositions - to merge conditional tokens back
    {
        "inputs": [
            {"name": "collateralToken", "type": "address"},
            {"name": "parentCollectionId", "type": "bytes32"},
            {"name": "conditionId", "type": "bytes32"},
            {"name": "partition", "type": "uint256[]"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "mergePositions",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    # getOutcomeSlotCount - to get number of outcome slots for a condition
    {
        "inputs": [{"name": "conditionId", "type": "bytes32"}],
        "name": "getOutcomeSlotCount",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    # prepareCondition - to prepare a condition
    {
        "inputs": [
            {"name": "oracle", "type": "address"},
            {"name": "questionId", "type": "bytes32"},
            {"name": "outcomeSlotCount", "type": "uint256"}
        ],
        "name": "prepareCondition",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
] 