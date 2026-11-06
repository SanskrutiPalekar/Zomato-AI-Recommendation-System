"""
Input Handler for Phase 2: User Input.
Orchestrates city matching, budget parsing, and creates normalized UserQuery objects.
Acts as the decoupled business logic between UI interfaces (CLI / WebUI) and Step 3 integration.
"""

from typing import Any, Dict, Optional, Tuple, Union

from phase2.budget_parser import BudgetParser
from phase2.city_matcher import CityMatcher
from phase2.models import CityPreference, PricePreference, UserQuery


class InputHandler:
    """Validates, parses, and normalizes user query parameters."""

    def __init__(
        self,
        city_matcher: Optional[CityMatcher] = None,
        budget_parser: Optional[BudgetParser] = None,
    ):
        self.city_matcher = city_matcher or CityMatcher()
        self.budget_parser = budget_parser or BudgetParser()

    def process_inputs(
        self,
        city_input: str,
        budget_input: Union[str, int, float],
        preferences_input: Optional[str] = None,
        apply_budget_tolerance: bool = True,
    ) -> UserQuery:
        """
        Validates raw user inputs and constructs a validated UserQuery.

        Args:
            city_input: User city or neighborhood string.
            budget_input: User budget for two (e.g., 800, 'under 1000').
            preferences_input: Optional dining preferences (cuisines, vibe).
            apply_budget_tolerance: Whether to add flex tolerance to max_budget.

        Returns:
            UserQuery instance ready for Step 3 integration.

        Raises:
            ValueError: If either city or budget validation fails.
        """
        # 1. Resolve City / Locality
        city_pref: CityPreference = self.city_matcher.resolve(city_input)

        # 2. Parse Budget
        price_pref: PricePreference = self.budget_parser.parse(budget_input)

        effective_max = (
            price_pref.effective_max_price
            if apply_budget_tolerance
            else price_pref.max_price
        )

        # 3. Clean optional preferences
        clean_pref = None
        if preferences_input:
            stripped = str(preferences_input).strip()
            if stripped:
                clean_pref = stripped

        # 4. Construct UserQuery
        return UserQuery(
            city=city_pref.resolved_city,
            max_budget=effective_max,
            min_budget=price_pref.min_price,
            preferences=clean_pref,
            raw_city_input=str(city_input),
            raw_budget_input=str(budget_input),
            city_confidence=city_pref.confidence_score,
            metadata={
                "is_exact_city_match": city_pref.is_exact_match,
                "base_max_budget": price_pref.max_price,
                "tolerance_applied": apply_budget_tolerance,
                "city_suggestions": city_pref.suggestions,
            },
        )

    def validate_inputs_safe(
        self,
        city_input: str,
        budget_input: Union[str, int, float],
        preferences_input: Optional[str] = None,
    ) -> Tuple[Optional[UserQuery], Optional[str]]:
        """
        Safe validation wrapper that catches ValueErrors and returns (query, error_message).
        Ideal for interactive CLI prompts and web forms.
        """
        try:
            query = self.process_inputs(city_input, budget_input, preferences_input)
            return query, None
        except ValueError as err:
            return None, str(err)

