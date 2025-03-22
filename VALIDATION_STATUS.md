# Validation Status Tracking

## Validation Levels

### 🧪 Experimental
- Initial stage for all new code
- May have incomplete or no tests
- Can import from any validation level

### 🔨 Development
- Complete AI-generated test coverage
- Documented functionality
- Can import from development and stable levels
- Requirements for promotion:
  1. Complete AI-generated test suite
  2. Documentation of all public functions
  3. No known major bugs

### ✅ Stable
- Human-reviewed code and tests
- Production-ready
- Can only import from other stable modules
- Requirements for promotion:
  1. Human review of code
  2. Human review of tests
  3. Successful test runs
  4. No modifications without human review

## Current Status

### Experimental Modules
- `futarchy.experimental.core.*` (from core/)
- `futarchy.experimental.exchanges.*` (from exchanges/)
- `futarchy.experimental.utils.*` (from utils/)
- `futarchy.experimental.scripts.*` (from scripts/)
- `futarchy.experimental.cli.*` (from cli/)
- `futarchy.experimental.strategies.*` (from strategies/)

Individual files:
- `main.py` → `futarchy.experimental.main`
- `check_transaction.py` → `futarchy.experimental.core.transaction`
- `transfer_sdai_no.py` → `futarchy.experimental.core.transfers`
- `check_pool_price.py` → `futarchy.experimental.exchanges.pool_price`
- `sell_sdai_yes_sushi.py` → `futarchy.experimental.exchanges.sushi_trades`
- `add_sdai_yes_liquidity.py` → `futarchy.experimental.exchanges.liquidity`
- `diagnose_pool.py` → `futarchy.experimental.exchanges.diagnostics`
- `sdai_no_swap_test.py` → `futarchy.experimental.exchanges.swap_test`
- `verify_key.py` → `futarchy.experimental.utils.key_verification`

### Development Modules
*(None yet)*

### Stable Modules
*(None yet)*

## Promotion Candidates
Files that could be promoted to development soon (already have some tests):
1. Swap-related functionality (multiple swap test files exist)
2. Permit-related functionality
3. Balance checking functionality

## Next Steps
1. ⏳ Move all files to experimental package structure
2. ⏳ Update imports to use new package paths
3. ⏳ Generate tests for files without coverage
4. ⏳ Begin promoting files with existing tests to development 