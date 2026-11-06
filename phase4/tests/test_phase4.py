"""
Unit and integration tests for Phase 4: Recommendation Engine (Groq LLM).
Provides offline mock validation and live Groq API tests when GROQ_API_KEY is configured.
"""

import os
import pytest
import pandas as pd

from phase1.pipeline import Phase1Pipeline
from phase2.input_handler import InputHandler
from phase2.models import UserQuery
from phase3.integrator import IntegrationPipeline
from phase4.config import GROQ_API_KEY_ENV
from phase4.groq_engine import GroqRecommendationEngine
from phase4.models import RecommendationResponse, RecommendedRestaurant
from phase4.pipeline import Phase4Pipeline
from phase4.prompts import SYSTEM_PROMPT, build_recommendation_prompt
from phase4.reranker import CandidateReranker


# ============================================================================
# 1. CandidateReranker Unit Tests
# ============================================================================

class TestCandidateReranker:
    def test_compute_score_formula(self, reranker: CandidateReranker, sample_user_query, sample_candidates):
        meghana = sample_candidates[0]
        score = reranker.compute_score(meghana, sample_user_query)
        assert 0.0 <= score <= 1.5
        assert score > 0.5  # High rating, high votes, and biryani relevance

    def test_select_top_candidates(self, reranker: CandidateReranker, sample_user_query, sample_candidates):
        top_2 = reranker.select_top_candidates(sample_candidates, sample_user_query, target_count=2)
        assert len(top_2) == 2
        # Meghana Foods should rank top due to Biryani relevance and strong rating
        assert top_2[0].restaurant_name == "Meghana Foods"

    def test_empty_candidates_handling(self, reranker: CandidateReranker, sample_user_query):
        assert reranker.select_top_candidates([], sample_user_query) == []


# ============================================================================
# 2. Prompt Builder Unit Tests
# ============================================================================

class TestPromptBuilder:
    def test_system_prompt_rules(self):
        assert "Strict Budget Compliance" in SYSTEM_PROMPT
        assert "Personalized Justification" in SYSTEM_PROMPT
        assert "Must-Try Dishes" in SYSTEM_PROMPT
        assert "JSON" in SYSTEM_PROMPT

    def test_build_recommendation_prompt(self, sample_user_query, sample_candidates):
        prompt = build_recommendation_prompt(sample_user_query, sample_candidates)
        assert "Koramangala" in prompt
        assert "Rs. 800" in prompt
        assert "Biryani" in prompt
        assert "Meghana Foods" in prompt
        assert "Empire Restaurant" in prompt
        assert "overall_ai_summary" in prompt


# ============================================================================
# 3. GroqRecommendationEngine Unit Tests
# ============================================================================

class TestGroqRecommendationEngine:
    def test_api_ready_status(self, monkeypatch):
        # When no key is set in environment or parameter
        monkeypatch.delenv(GROQ_API_KEY_ENV, raising=False)
        engine_no_key = GroqRecommendationEngine(api_key=None)
        assert not engine_no_key.is_live_api_ready()

        # When key is explicitly provided
        engine_with_key = GroqRecommendationEngine(api_key="gsk_dummy_test_key_12345")
        assert engine_with_key.api_key == "gsk_dummy_test_key_12345"

    def test_mock_generation_schema_compliance(self, mock_engine, sample_user_query, sample_candidates):
        resp = mock_engine.generate_recommendations(
            query=sample_user_query,
            candidates=sample_candidates,
            force_mock=True,
        )

        assert isinstance(resp, RecommendationResponse)
        assert len(resp.recommendations) == len(sample_candidates)
        assert resp.is_mock is True
        assert len(resp.overall_ai_summary) > 10

        for r in resp.recommendations:
            assert isinstance(r, RecommendedRestaurant)
            assert r.cost_for_two <= sample_user_query.max_budget
            assert len(r.ai_rationale) > 15
            assert len(r.must_try_dishes) > 0
            assert "under your budget" in r.budget_verdict or "Fits" in r.budget_verdict

    def test_empty_candidates_response(self, mock_engine, sample_user_query):
        resp = mock_engine.generate_recommendations(
            query=sample_user_query,
            candidates=[],
            force_mock=True,
        )
        assert resp.recommendations == []
        assert "No matching restaurants found" in resp.overall_ai_summary

    @pytest.mark.skipif(
        not os.getenv(GROQ_API_KEY_ENV),
        reason="Requires GROQ_API_KEY environment variable. Will execute once user sets the key.",
    )
    def test_live_groq_api_call(self, sample_user_query, sample_candidates):
        """
        Live integration test against Groq Cloud API.
        Executes automatically as soon as GROQ_API_KEY is provided.
        """
        engine = GroqRecommendationEngine()
        assert engine.is_live_api_ready()

        resp = engine.generate_recommendations(
            query=sample_user_query,
            candidates=sample_candidates[:2],
            force_mock=False,
        )

        assert isinstance(resp, RecommendationResponse)
        assert len(resp.recommendations) >= 1
        assert resp.is_mock is False
        assert len(resp.model_name) > 0
        assert resp.latency_seconds > 0.0

    @pytest.mark.skipif(
        not os.getenv(GROQ_API_KEY_ENV),
        reason="Requires GROQ_API_KEY environment variable.",
    )
    def test_live_groq_budget_adherence(self, sample_candidates):
        """
        Live Groq Test 1: Verifies that the LLM strictly adheres to user budget ceiling
        and generates clear value-for-money budget verdicts.
        """
        strict_budget_query = UserQuery(
            city="Koramangala",
            max_budget=650.0,
            min_budget=0.0,
            preferences=None,
            raw_city_input="Koramangala",
            raw_budget_input="650",
        )
        # Meghana Foods costs 600 (fits <= 650); Empire costs 750 (exceeds 650)
        engine = GroqRecommendationEngine()
        resp = engine.generate_recommendations(
            query=strict_budget_query,
            candidates=sample_candidates,  # Candidates include costs: 600, 750, 350
            force_mock=False,
        )

        assert isinstance(resp, RecommendationResponse)
        assert len(resp.recommendations) >= 1
        assert resp.is_mock is False

        # Every recommended restaurant must be within the user's budget ceiling
        for rec in resp.recommendations:
            assert rec.cost_for_two <= strict_budget_query.max_budget, (
                f"LLM recommended {rec.restaurant_name} (Cost: Rs. {rec.cost_for_two}) "
                f"which exceeds the budget of Rs. {strict_budget_query.max_budget}"
            )
            assert len(rec.ai_rationale) > 20
            assert len(rec.budget_verdict) > 0

    @pytest.mark.skipif(
        not os.getenv(GROQ_API_KEY_ENV),
        reason="Requires GROQ_API_KEY environment variable.",
    )
    def test_live_groq_cuisine_and_must_try_dishes(self, sample_candidates):
        """
        Live Groq Test 2: Verifies that the LLM focuses on user preferences and extracts
        concrete must-try dishes for each recommendation.
        """
        query_with_pref = UserQuery(
            city="Koramangala",
            max_budget=800.0,
            preferences="Biryani, Andhra style",
            raw_city_input="Koramangala",
            raw_budget_input="800",
        )
        engine = GroqRecommendationEngine()
        resp = engine.generate_recommendations(
            query=query_with_pref,
            candidates=sample_candidates[:2],
            force_mock=False,
        )

        assert len(resp.recommendations) >= 1
        top_rec = resp.recommendations[0]

        # Must have at least 1 must-try dish suggested
        assert len(top_rec.must_try_dishes) >= 1
        # AI rationale should provide a personalized justification
        assert len(top_rec.ai_rationale.split()) >= 8

    @pytest.mark.skipif(
        not os.getenv(GROQ_API_KEY_ENV),
        reason="Requires GROQ_API_KEY environment variable.",
    )
    def test_live_groq_pipeline_end_to_end(self, sample_context_payload):
        """
        Live Groq Test 3: Verifies that the entire Phase4Pipeline executes live
        using Groq LLM with valid latency and structured overview summary.
        """
        live_engine = GroqRecommendationEngine()
        pipeline = Phase4Pipeline(engine=live_engine, target_recs_count=2)

        resp = pipeline.run(sample_context_payload, force_mock=False)

        assert isinstance(resp, RecommendationResponse)
        assert resp.is_mock is False
        assert len(resp.recommendations) == 2
        assert len(resp.overall_ai_summary) > 15
        assert resp.latency_seconds > 0.0
        assert resp.latency_seconds < 15.0  # Groq should respond within a few seconds


# ============================================================================
# 4. Phase4Pipeline Unit Tests
# ============================================================================

class TestPhase4Pipeline:
    def test_pipeline_run_mock(self, phase4_pipeline: Phase4Pipeline, sample_context_payload):
        resp = phase4_pipeline.run(sample_context_payload, force_mock=True, target_count=2)

        assert isinstance(resp, RecommendationResponse)
        assert len(resp.recommendations) == 2
        # Check ranking order: Meghana Foods should be top recommendation
        assert resp.recommendations[0].restaurant_name == "Meghana Foods"


# ============================================================================
# 5. Full End-to-End Test: Step 1 -> Step 2 -> Step 3 -> Step 4
# ============================================================================

class TestEndToEndSteps1To4:
    def test_full_chain_step1_to_step4(self):
        # 1. Step 1: Ingest sample raw restaurant data
        raw_data = pd.DataFrame([
            {
                "name": "Meghana Foods",
                "rate": "4.4/5",
                "votes": 4200,
                "location": "Koramangala",
                "listed_in(city)": "Koramangala",
                "cuisines": "Biryani, Andhra",
                "approx_cost(for two people)": "600",
                "dish_liked": "Chicken Biryani, Boneless Biryani",
                "rest_type": "Casual Dining",
                "online_order": "Yes",
                "book_table": "No",
            },
            {
                "name": "Empire Restaurant",
                "rate": "4.3/5",
                "votes": 2500,
                "location": "Koramangala",
                "listed_in(city)": "Koramangala",
                "cuisines": "North Indian, Biryani",
                "approx_cost(for two people)": "750",
                "dish_liked": "Ghee Rice, Kebab",
                "rest_type": "Casual Dining",
                "online_order": "Yes",
                "book_table": "No",
            },
            {
                "name": "Luxury Steakhouse",
                "rate": "4.6/5",
                "votes": 1100,
                "location": "Koramangala",
                "listed_in(city)": "Koramangala",
                "cuisines": "Steak, Continental",
                "approx_cost(for two people)": "2200",
                "dish_liked": "Wagyu, Wine",
                "rest_type": "Fine Dining",
                "online_order": "No",
                "book_table": "Yes",
            },
        ])
        phase1_res = Phase1Pipeline().run(raw_df=raw_data)

        # 2. Step 2: Validate user query
        handler = InputHandler()
        user_query = handler.process_inputs("koramangla", "under 800", "Biryani")

        # 3. Step 3: Integrate & Context Fusion
        integrator = IntegrationPipeline()
        payload = integrator.run(query=user_query, metadata_store=phase1_res.metadata_store)

        # 4. Step 4: Groq AI Recommendation
        pipeline = Phase4Pipeline()
        final_recs = pipeline.run(payload, force_mock=True)

        assert len(final_recs.recommendations) == 2
        top_pick = final_recs.recommendations[0]
        assert top_pick.restaurant_name == "Meghana Foods"
        assert top_pick.cost_for_two == 600
        assert top_pick.cost_for_two <= user_query.max_budget
        assert "Luxury Steakhouse" not in [r.restaurant_name for r in final_recs.recommendations]

