"""
Pytest fixtures for Phase 2 tests.
"""

import pytest

from phase2.budget_parser import BudgetParser
from phase2.city_matcher import CityMatcher
from phase2.input_handler import InputHandler


@pytest.fixture
def budget_parser() -> BudgetParser:
    return BudgetParser(tolerance_pct=0.10)


@pytest.fixture
def city_matcher() -> CityMatcher:
    return CityMatcher()


@pytest.fixture
def input_handler(city_matcher, budget_parser) -> InputHandler:
    return InputHandler(city_matcher=city_matcher, budget_parser=budget_parser)

