"""
Phase 2: User Input.
Provides modules for capturing, parsing, validating, and standardizing user search queries (City & Price).
"""

from phase2.budget_parser import BudgetParser
from phase2.city_matcher import CityMatcher
from phase2.cli_prompt import CLIPrompt
from phase2.config import (
    BUDGET_TIERS,
    DEFAULT_BUDGET_TOLERANCE_PCT,
    DEFAULT_KNOWN_LOCALITIES,
    LOCATION_ALIASES,
    MIN_CITY_CONFIDENCE_THRESHOLD,
)
from phase2.input_handler import InputHandler
from phase2.models import CityPreference, PricePreference, UserQuery

__all__ = [
    "BudgetParser",
    "CityMatcher",
    "InputHandler",
    "CLIPrompt",
    "UserQuery",
    "PricePreference",
    "CityPreference",
    "DEFAULT_KNOWN_LOCALITIES",
    "LOCATION_ALIASES",
    "BUDGET_TIERS",
    "MIN_CITY_CONFIDENCE_THRESHOLD",
    "DEFAULT_BUDGET_TOLERANCE_PCT",
]

