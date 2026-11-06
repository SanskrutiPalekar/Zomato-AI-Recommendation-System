"""
Unit tests for Phase 2: User Input (City & Price Parsing, Validation, and Normalization).
"""

import pytest

from phase2.budget_parser import BudgetParser
from phase2.city_matcher import CityMatcher
from phase2.input_handler import InputHandler
from phase2.models import UserQuery
from phase1.data_cleaner import ZomatoDataCleaner
from phase1.metadata_store import MetadataStore


# ============================================================================
# 1. BudgetParser Unit Tests
# ============================================================================

class TestBudgetParser:
    def test_parse_numeric_and_float(self, budget_parser: BudgetParser):
        p1 = budget_parser.parse(800)
        assert p1.max_price == 800.0
        assert p1.min_price == 0.0

        p2 = budget_parser.parse("1200")
        assert p2.max_price == 1200.0

        p3 = budget_parser.parse(750.50)
        assert p3.max_price == 750.50

    def test_parse_currency_formats(self, budget_parser: BudgetParser):
        p1 = budget_parser.parse("Rs. 800")
        assert p1.max_price == 800.0

        p2 = budget_parser.parse("Rs 1,200/-")
        assert p2.max_price == 1200.0

        p3 = budget_parser.parse("₹1500 INR")
        assert p3.max_price == 1500.0

    def test_parse_upper_bound_phrases(self, budget_parser: BudgetParser):
        assert budget_parser.parse("under 800").max_price == 800.0
        assert budget_parser.parse("below 1000").max_price == 1000.0
        assert budget_parser.parse("less than 600").max_price == 600.0
        assert budget_parser.parse("max 900").max_price == 900.0
        assert budget_parser.parse("upto 750").max_price == 750.0

    def test_parse_ranges(self, budget_parser: BudgetParser):
        p1 = budget_parser.parse("500-1000")
        assert p1.min_price == 500.0
        assert p1.max_price == 1000.0

        p2 = budget_parser.parse("between 400 and 800")
        assert p2.min_price == 400.0
        assert p2.max_price == 800.0

        p3 = budget_parser.parse("600 to 1200")
        assert p3.min_price == 600.0
        assert p3.max_price == 1200.0

    def test_parse_approximate(self, budget_parser: BudgetParser):
        p = budget_parser.parse("around 1000")
        assert p.min_price == 850.0  # 1000 * 0.85
        assert p.max_price == 1150.0  # 1000 * 1.15

    def test_parse_preset_tiers(self, budget_parser: BudgetParser):
        p_budget = budget_parser.parse("budget friendly")
        assert p_budget.max_price == 500.0

        p_fine = budget_parser.parse("fine dining")
        assert p_fine.max_price == 5000.0
        assert p_fine.min_price == 1500.0

    def test_effective_max_price_tolerance(self, budget_parser: BudgetParser):
        p = budget_parser.parse(1000)
        # 10% tolerance configured on fixture
        assert p.effective_max_price == 1100.0

    def test_invalid_budget_inputs(self, budget_parser: BudgetParser):
        with pytest.raises(ValueError):
            budget_parser.parse("")

        with pytest.raises(ValueError):
            budget_parser.parse("free")

        with pytest.raises(ValueError):
            budget_parser.parse("-500")

        with pytest.raises(ValueError):
            budget_parser.parse("xyz abc")


# ============================================================================
# 2. CityMatcher Unit Tests
# ============================================================================

class TestCityMatcher:
    def test_exact_match(self, city_matcher: CityMatcher):
        res = city_matcher.resolve("Koramangala")
        assert res.resolved_city == "Koramangala"
        assert res.confidence_score == 1.0
        assert res.is_exact_match is True

    def test_case_insensitive_and_whitespace(self, city_matcher: CityMatcher):
        res1 = city_matcher.resolve("  koramangala  ")
        assert res1.resolved_city == "Koramangala"

        res2 = city_matcher.resolve("INDIRANAGAR")
        assert res2.resolved_city == "Indiranagar"

    def test_aliases(self, city_matcher: CityMatcher):
        assert city_matcher.resolve("blr").resolved_city == "Bangalore"
        assert city_matcher.resolve("bengaluru").resolved_city == "Bangalore"
        assert city_matcher.resolve("hsr").resolved_city == "HSR Layout"
        assert city_matcher.resolve("btm").resolved_city == "BTM"

    def test_typo_fuzzy_matching(self, city_matcher: CityMatcher):
        # Common typos should resolve with high confidence
        res1 = city_matcher.resolve("koramangla")
        assert res1.resolved_city == "Koramangala"
        assert res1.confidence_score >= 0.85

        res2 = city_matcher.resolve("whitefeild")
        assert res2.resolved_city == "Whitefield"

        res3 = city_matcher.resolve("banashankri")
        assert res3.resolved_city == "Banashankari"

    def test_unrecognized_city_raises(self, city_matcher: CityMatcher):
        with pytest.raises(ValueError) as excinfo:
            city_matcher.resolve("RandomFakeCity123")
        assert "Could not recognize locality" in str(excinfo.value)

    def test_empty_city_raises(self, city_matcher: CityMatcher):
        with pytest.raises(ValueError):
            city_matcher.resolve("")


# ============================================================================
# 3. InputHandler Unit Tests
# ============================================================================

class TestInputHandler:
    def test_process_inputs_valid(self, input_handler: InputHandler):
        query = input_handler.process_inputs(
            city_input="koramangla",
            budget_input="800",
            preferences_input="Biryani, North Indian",
            apply_budget_tolerance=True,
        )

        assert isinstance(query, UserQuery)
        assert query.city == "Koramangala"
        assert query.max_budget == 880.0  # 800 + 10% tolerance
        assert query.preferences == "Biryani, North Indian"
        assert query.raw_city_input == "koramangla"
        assert query.city_confidence >= 0.85
        assert "City: Koramangala" in query.summary()

    def test_process_inputs_no_tolerance(self, input_handler: InputHandler):
        query = input_handler.process_inputs(
            city_input="Indiranagar",
            budget_input="1000",
            apply_budget_tolerance=False,
        )
        assert query.max_budget == 1000.0

    def test_validate_inputs_safe(self, input_handler: InputHandler):
        # Valid inputs
        q, err = input_handler.validate_inputs_safe("HSR", "500-1000")
        assert q is not None
        assert err is None
        assert q.city == "HSR Layout"

        # Invalid city
        q_bad_city, err_city = input_handler.validate_inputs_safe("UnknownLandia", "800")
        assert q_bad_city is None
        assert "Could not recognize locality" in err_city

        # Invalid budget
        q_bad_budget, err_budget = input_handler.validate_inputs_safe("Koramangala", "not-a-budget")
        assert q_bad_budget is None
        assert "Unable to understand budget" in err_budget


# ============================================================================
# 4. Step 1 + Step 2 Integration Verification Test
# ============================================================================

class TestStep1Step2Integration:
    def test_user_query_filters_metadata_store(self, input_handler: InputHandler):
        """
        Verifies that a UserQuery generated in Step 2 can directly query the
        MetadataStore built in Step 1.
        """
        import pandas as pd

        sample_data = pd.DataFrame([
            {
                "restaurant_id": 1,
                "restaurant_name": "Empire Restaurant",
                "city": "koramangala",
                "location": "koramangala",
                "cost_for_two": 750,
                "rating": 4.3,
                "votes": 2500,
                "cuisines": "North Indian, Biryani",
                "rest_type": "Casual Dining",
                "dish_liked": "Ghee Rice, Kebab",
                "online_order": "Yes",
                "book_table": "No",
            },
            {
                "restaurant_id": 2,
                "restaurant_name": "High End Bistro",
                "city": "koramangala",
                "location": "koramangala",
                "cost_for_two": 2400,
                "rating": 4.6,
                "votes": 800,
                "cuisines": "Continental",
                "rest_type": "Fine Dining",
                "dish_liked": "Steak",
                "online_order": "No",
                "book_table": "Yes",
            },
        ])

        # Step 1: Store indexing
        store = MetadataStore()
        store.index_dataframe(sample_data)

        # Step 2: User input processing
        user_query = input_handler.process_inputs(
            city_input="koramangla",  # Has typo
            budget_input="under 800",  # Phrase with tolerance -> 880
            apply_budget_tolerance=True,
        )

        # Step 3 Bridge: Query metadata store with Step 2 results
        results = store.query_by_city_and_price(
            city=user_query.city,
            max_price=user_query.max_budget,
            min_price=user_query.min_budget,
        )

        # Verification: Only Empire Restaurant (750) fits within budget; High End Bistro (2400) is excluded
        assert len(results) == 1
        assert results[0]["restaurant_name"] == "Empire Restaurant"
        assert results[0]["cost_for_two"] <= user_query.max_budget

