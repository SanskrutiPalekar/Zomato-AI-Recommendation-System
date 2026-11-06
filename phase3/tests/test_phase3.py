"""
Unit and integration tests for Phase 3: Integrate (Step 3).
Tests metadata filtering, preference fusion, relaxation fallbacks, and LLM context payload generation.
"""

import pytest
import pandas as pd

from phase1.pipeline import Phase1Pipeline
from phase2.input_handler import InputHandler
from phase2.models import UserQuery
from phase3.context_fusion import ContextFusionEngine
from phase3.filter_engine import FilterEngine
from phase3.integrator import IntegrationPipeline
from phase3.models import CandidateRestaurant, IntegrationContextPayload


# ============================================================================
# 1. FilterEngine Unit Tests
# ============================================================================

class TestFilterEngine:
    def test_filter_strict_budget_and_city(self, filter_engine: FilterEngine):
        query = UserQuery(
            city="Koramangala",
            max_budget=800.0,
            min_budget=0.0,
            raw_city_input="Koramangala",
            raw_budget_input="800",
        )
        candidates, relaxed, notes = filter_engine.filter_candidates(query, enable_relaxation=False)

        # Expected: Meghana Foods (600) and Empire (750) fit.
        # Truffles (900) and Chianti (1800) should be excluded.
        assert len(candidates) == 2
        assert not relaxed
        assert notes is None

        names = [c.restaurant_name for c in candidates]
        assert "Meghana Foods" in names
        assert "Empire Restaurant" in names
        assert "Truffles" not in names

    def test_budget_savings_calculation(self, filter_engine: FilterEngine):
        query = UserQuery(
            city="Koramangala",
            max_budget=800.0,
            raw_city_input="Koramangala",
            raw_budget_input="800",
        )
        candidates, _, _ = filter_engine.filter_candidates(query)

        meghana = next(c for c in candidates if c.restaurant_name == "Meghana Foods")
        assert meghana.cost_for_two == 600
        # Savings = 800 - 600 = 200
        assert meghana.budget_savings == 200

    def test_relaxation_when_budget_is_slightly_exceeded(self, filter_engine: FilterEngine):
        # Query with Rs. 780 budget. Truffles is 900 (exceeds), but Truffles doesn't fit.
        # But if user enters budget 760, Empire is 750 (fits).
        # What if user enters budget 500? No restaurant in Koramangala fits (min is 600).
        # 500 * 1.20 = 600! Meghana Foods (600) should now fit under relaxation!
        query = UserQuery(
            city="Koramangala",
            max_budget=500.0,
            raw_city_input="Koramangala",
            raw_budget_input="500",
        )
        candidates, relaxed, notes = filter_engine.filter_candidates(query, enable_relaxation=True)

        assert len(candidates) == 1
        assert candidates[0].restaurant_name == "Meghana Foods"
        assert relaxed is True
        assert "Expanded budget" in notes

    def test_no_results_without_relaxation(self, filter_engine: FilterEngine):
        query = UserQuery(
            city="Koramangala",
            max_budget=500.0,
            raw_city_input="Koramangala",
            raw_budget_input="500",
        )
        candidates, relaxed, notes = filter_engine.filter_candidates(query, enable_relaxation=False)
        assert len(candidates) == 0
        assert relaxed is False


# ============================================================================
# 2. ContextFusionEngine Unit Tests
# ============================================================================

class TestContextFusionEngine:
    def test_preference_relevance_calculation(self, fusion_engine: ContextFusionEngine):
        c_biryani = CandidateRestaurant(
            restaurant_id=1,
            restaurant_name="Meghana Foods",
            city="Koramangala",
            location="Koramangala",
            cost_for_two=600,
            rating=4.4,
            votes=4000,
            cuisines="Biryani, Andhra",
            dish_liked="Chicken Biryani",
        )
        c_cafe = CandidateRestaurant(
            restaurant_id=2,
            restaurant_name="Truffles",
            city="Koramangala",
            location="Koramangala",
            cost_for_two=900,
            rating=4.5,
            votes=6000,
            cuisines="Cafe, Burger",
            dish_liked="Burger, Shake",
        )

        score_biryani = fusion_engine.calculate_preference_relevance(c_biryani, "Biryani")
        score_cafe = fusion_engine.calculate_preference_relevance(c_cafe, "Biryani")

        assert score_biryani == 1.0
        assert score_cafe == 0.0

    def test_neutral_relevance_when_no_preferences(self, fusion_engine: ContextFusionEngine):
        c = CandidateRestaurant(
            restaurant_id=1,
            restaurant_name="Any Diner",
            city="Koramangala",
            location="Koramangala",
            cost_for_two=500,
            rating=4.0,
            votes=100,
        )
        assert fusion_engine.calculate_preference_relevance(c, None) == 0.5
        assert fusion_engine.calculate_preference_relevance(c, "") == 0.5

    def test_rank_and_score_candidates(self, fusion_engine: ContextFusionEngine):
        candidates = [
            CandidateRestaurant(
                restaurant_id=1,
                restaurant_name="Cafe Spot",
                city="Koramangala",
                location="Koramangala",
                cost_for_two=700,
                rating=4.6,
                votes=1000,
                cuisines="Cafe, Italian",
            ),
            CandidateRestaurant(
                restaurant_id=2,
                restaurant_name="Biryani House",
                city="Koramangala",
                location="Koramangala",
                cost_for_two=700,
                rating=4.3,
                votes=1000,
                cuisines="Biryani, Mughlai",
            ),
        ]
        query = UserQuery(
            city="Koramangala",
            max_budget=800.0,
            preferences="Biryani",
            raw_city_input="Koramangala",
            raw_budget_input="800",
        )

        ranked = fusion_engine.rank_and_score_candidates(candidates, query, max_candidates=2)
        # Biryani House should rank 1st because user specifically requested Biryani
        assert ranked[0].restaurant_name == "Biryani House"
        assert ranked[0].relevance_score > ranked[1].relevance_score

    def test_build_llm_context(self, fusion_engine: ContextFusionEngine):
        candidates = [
            CandidateRestaurant(
                restaurant_id=1,
                restaurant_name="Meghana Foods",
                city="Koramangala",
                location="Koramangala 5th Block",
                cost_for_two=600,
                rating=4.4,
                votes=4100,
                cuisines="Biryani, Andhra",
                dish_liked="Chicken Biryani",
                online_order="Yes",
            )
        ]
        query = UserQuery(
            city="Koramangala",
            max_budget=800.0,
            preferences="Biryani",
            raw_city_input="Koramangala",
            raw_budget_input="800",
        )

        context_str = fusion_engine.build_llm_context(candidates, query)
        assert "Search Constraints" in context_str
        assert "Target Location: Koramangala" in context_str
        assert "Meghana Foods" in context_str
        assert "Cost for Two: Rs. 600" in context_str
        assert "Delivery Available" in context_str


# ============================================================================
# 3. IntegrationPipeline Unit Tests
# ============================================================================

class TestIntegrationPipeline:
    def test_pipeline_run(self, integration_pipeline: IntegrationPipeline, sample_indexed_store):
        query = UserQuery(
            city="Koramangala",
            max_budget=1000.0,
            preferences="Burger",
            raw_city_input="Koramangala",
            raw_budget_input="1000",
        )
        payload = integration_pipeline.run(query=query, metadata_store=sample_indexed_store, max_candidates=3)

        assert isinstance(payload, IntegrationContextPayload)
        assert payload.query.city == "Koramangala"
        assert len(payload.candidates) <= 3
        assert payload.total_found >= 3
        # Truffles (known for burgers) should rank top
        assert payload.candidates[0].restaurant_name == "Truffles"
        assert "Truffles" in payload.context_text


# ============================================================================
# 4. End-to-End Test: Phase 1 + Phase 2 + Phase 3 Integration
# ============================================================================

class TestEndToEndPhase123:
    def test_full_flow_phase1_to_phase3(self):
        # 1. Phase 1: Ingest & Index sample raw records
        raw_data = pd.DataFrame([
            {
                "name": "Nagarjuna",
                "rate": "4.4/5",
                "votes": 3500,
                "location": "Indiranagar",
                "listed_in(city)": "Indiranagar",
                "cuisines": "Andhra, Biryani, South Indian",
                "approx_cost(for two people)": "800",
                "dish_liked": "Chicken Roast, Meals, Biryani",
                "rest_type": "Casual Dining",
                "online_order": "Yes",
                "book_table": "No",
            },
            {
                "name": "Glen's Bakehouse",
                "rate": "4.5/5",
                "votes": 4200,
                "location": "Indiranagar",
                "listed_in(city)": "Indiranagar",
                "cuisines": "Bakery, Desserts, Cafe",
                "approx_cost(for two people)": "600",
                "dish_liked": "Red Velvet Cupcake, Cheesecake",
                "rest_type": "Bakery, Cafe",
                "online_order": "Yes",
                "book_table": "No",
            },
            {
                "name": "High End Indiranagar Bar",
                "rate": "4.6/5",
                "votes": 1200,
                "location": "Indiranagar",
                "listed_in(city)": "Indiranagar",
                "cuisines": "Continental",
                "approx_cost(for two people)": "2500",
                "dish_liked": "Cocktails",
                "rest_type": "Lounge",
                "online_order": "No",
                "book_table": "Yes",
            },
        ])

        phase1_result = Phase1Pipeline().run(raw_df=raw_data)
        assert phase1_result.metadata_store.count() == 3

        # 2. Phase 2: User Input Parsing with typo & natural language budget
        input_handler = InputHandler()
        user_query = input_handler.process_inputs(
            city_input="indira nagar",  # Spacing variance
            budget_input="under 1000",   # Phrase
            preferences_input="Biryani",
        )
        assert user_query.city == "Indiranagar"
        assert user_query.max_budget >= 1000.0

        # 3. Phase 3: Integration & Context Fusion
        integrator = IntegrationPipeline()
        payload = integrator.run(
            query=user_query,
            metadata_store=phase1_result.metadata_store,
            max_candidates=5,
        )

        assert payload.total_found == 2  # Nagarjuna (800) and Glen's (600) fit; 2500 excluded
        assert payload.candidates[0].restaurant_name == "Nagarjuna"  # Ranked 1st due to 'Biryani' preference
        assert "Nagarjuna" in payload.context_text
        assert "Glen's Bakehouse" in payload.context_text
        assert "High End Indiranagar Bar" not in payload.context_text

