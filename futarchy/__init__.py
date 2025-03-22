"""
Futarchy Trading Bot Package

This package is organized into three validation levels:
- stable: Production-ready code with human-reviewed tests
- development: Code with complete AI-generated tests
- experimental: New or unvalidated code

Imports should follow these rules:
1. stable can import from stable only
2. development can import from development and stable
3. experimental can import from any level
"""

__version__ = "0.1.0"

# Validation level constants
VALIDATION_LEVEL_STABLE = "stable"
VALIDATION_LEVEL_DEVELOPMENT = "development"
VALIDATION_LEVEL_EXPERIMENTAL = "experimental"

def get_validation_level(module_name: str) -> str:
    """
    Returns the validation level of a module based on its import path.
    """
    if module_name.startswith("futarchy.stable."):
        return VALIDATION_LEVEL_STABLE
    elif module_name.startswith("futarchy.development."):
        return VALIDATION_LEVEL_DEVELOPMENT
    else:
        return VALIDATION_LEVEL_EXPERIMENTAL

def validate_import(importer_module: str, imported_module: str) -> bool:
    """
    Validates whether an import is allowed based on validation levels.
    Returns True if the import is allowed, False otherwise.
    """
    importer_level = get_validation_level(importer_module)
    imported_level = get_validation_level(imported_module)
    
    if importer_level == VALIDATION_LEVEL_STABLE:
        return imported_level == VALIDATION_LEVEL_STABLE
    elif importer_level == VALIDATION_LEVEL_DEVELOPMENT:
        return imported_level in (VALIDATION_LEVEL_STABLE, VALIDATION_LEVEL_DEVELOPMENT)
    return True  # experimental can import from anywhere
