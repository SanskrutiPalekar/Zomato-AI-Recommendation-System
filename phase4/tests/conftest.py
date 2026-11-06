"""
Pytest fixtures for Phase 4 tests.
"""

import pytest

from phase2.models import UserQuery
from phase3.models import CandidateRestaurant, IntegrationContextPayload
from phase4.groq_engine import GroqRecommendationEngine
from phase4.pipeline import Phase4Pipeline
from phase4.reranker import CandidateReranker


@pytest.fixture
def sample_user_query() -> UserQuery:
    return UserQuery(
        city="Koramangala",
        max_budget=800.0,
        min_budget=0.0,
        preferences="Biryani",
        raw_city_input="Koramangala",
        raw_budget_input="800",
    )


@pytest.fixture
def sample_candidates() -> list[CandidateRestaurant]:
    return [
        CandidateRestaurant(
            restaurant_id=1,
            restaurant_name="Meghana Foods",
            city="Koramangala",
            location="Koramangala 1st Block",
            cost_for_two=600,
            rating=4.4,
            votes=4100,
            cuisines="Biryani, Andhra",
            rest_type="Casual Dining",
            dish_liked="Chicken Biryani, Chilli Chicken",
            online_order="Yes",
            book_table="No",
            relevance_score=1.0,
            budget_savings=200,
        ),
        CandidateRestaurant(
            restaurant_id=2,
            restaurant_name="Empire Restaurant",
            city="Koramangala",
            location="Koramangala 5th Block",
            cost_for_two=750,
            rating=4.2,
            votes=2500,
            cuisines="North Indian, Biryani",
            rest_type="Casual Dining",
            dish_liked="Ghee Rice, Coin Parotta",
            online_order="Yes",
            book_table="No",
            relevance_score=1.0,
            budget_savings=50,
        ),
        CandidateRestaurant(
            restaurant_id=3,
            restaurant_name="Corner House",
            city="Koramangala",
            location="Koramangala 7th Block",
            cost_for_two=350,
            rating=4.5,
            votes=3100,
            cuisines="Desserts, Ice Cream",
            rest_type="Dessert Parlor",
            dish_liked="Death By Chocolate",
            online_order="Yes",
            book_table="No",
            relevance_score=0.0,
            budget_savings=450,
        ),
    ]


@pytest.fixture
def sample_context_payload(sample_user_query, sample_candidates) -> IntegrationContextPayload:
    return IntegrationContextPayload(
        query=sample_user_query,
        candidates=sample_candidates,
        total_found=len(sample_candidates),
        applied_relaxation=False,
        context_text="Sample formatted context text",
    )


@pytest.fixture
def reranker() -> CandidateReranker:
    return CandidateReranker()


@pytest.fixture
def mock_engine() -> GroqRecommendationEngine:
    return GroqRecommendationEngine(api_key=None)


@pytest.fixture
def phase4_pipeline(reranker, mock_engine) -> Phase4Pipeline:
    return Phase4Pipeline(reranker=reranker, engine=mock_engine)

