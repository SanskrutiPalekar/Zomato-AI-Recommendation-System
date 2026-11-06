"""
Pytest fixtures for Phase 6 API tests.
Sets up an in-memory MetadataStore, a mock ZomatoAIService,
and a FastAPI TestClient — all fully offline (no Groq API calls).
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from phase1.metadata_store import MetadataStore
from phase4.pipeline import Phase4Pipeline
from phase4.groq_engine import GroqRecommendationEngine
from phase5.display_adapter import JSONDisplayAdapter
from phase5.service import ZomatoAIService
from phase6 import dependencies as deps


@pytest.fixture(autouse=True)
def _reset_singletons():
    """Ensure clean singletons for every test."""
    deps.reset_singletons()
    yield
    deps.reset_singletons()


@pytest.fixture
def sample_store() -> MetadataStore:
    """Pre-indexed MetadataStore with 5 restaurants across 2 cities."""
    store = MetadataStore()
    records = [
        {
            "restaurant_id": 1,
            "restaurant_name": "Meghana Foods",
            "city": "koramangala",
            "location": "koramangala 1st block",
            "cost_for_two": 600,
            "rating": 4.4,
            "votes": 4100,
            "cuisines": "Biryani, Andhra, South Indian",
            "rest_type": "Casual Dining",
            "dish_liked": "Chicken Boneless Biryani, Chilli Chicken",
            "online_order": "Yes",
            "book_table": "No",
        },
        {
            "restaurant_id": 2,
            "restaurant_name": "Empire Restaurant",
            "city": "koramangala",
            "location": "koramangala 5th block",
            "cost_for_two": 750,
            "rating": 4.3,
            "votes": 2500,
            "cuisines": "North Indian, Biryani, Mughlai",
            "rest_type": "Casual Dining",
            "dish_liked": "Ghee Rice, Coin Parotta",
            "online_order": "Yes",
            "book_table": "No",
        },
        {
            "restaurant_id": 3,
            "restaurant_name": "Corner House Ice Cream",
            "city": "koramangala",
            "location": "koramangala 7th block",
            "cost_for_two": 350,
            "rating": 4.5,
            "votes": 3100,
            "cuisines": "Desserts, Ice Cream",
            "rest_type": "Dessert Parlor",
            "dish_liked": "Death By Chocolate",
            "online_order": "Yes",
            "book_table": "No",
        },
        {
            "restaurant_id": 4,
            "restaurant_name": "Toit Brewpub",
            "city": "indiranagar",
            "location": "indiranagar 100 feet road",
            "cost_for_two": 1500,
            "rating": 4.7,
            "votes": 12500,
            "cuisines": "Italian, Pizza, Brewery",
            "rest_type": "Microbrewery, Pub",
            "dish_liked": "Wood Fired Pizza, Craft Beer",
            "online_order": "No",
            "book_table": "Yes",
        },
        {
            "restaurant_id": 5,
            "restaurant_name": "Glen's Bakehouse",
            "city": "indiranagar",
            "location": "indiranagar 100 feet road",
            "cost_for_two": 600,
            "rating": 4.5,
            "votes": 4200,
            "cuisines": "Bakery, Desserts, Cafe",
            "rest_type": "Bakery, Cafe",
            "dish_liked": "Red Velvet Cupcake, Cheesecake",
            "online_order": "Yes",
            "book_table": "No",
        },
    ]
    store.index_dataframe(pd.DataFrame(records))
    return store


@pytest.fixture
def mock_service(sample_store) -> ZomatoAIService:
    """ZomatoAIService configured with mock Groq engine (no API calls)."""
    engine = GroqRecommendationEngine()
    pipeline = Phase4Pipeline(engine=engine)
    service = ZomatoAIService(
        metadata_store=sample_store,
        recommendation_pipeline=pipeline,
        display_adapter=JSONDisplayAdapter(),
    )
    return service


@pytest.fixture
def api_client(sample_store, mock_service):
    """FastAPI TestClient wired to the mock store and service."""
    from httpx import ASGITransport, AsyncClient
    from phase6.api import create_app

    # Inject test dependencies
    deps.set_store(sample_store)
    deps.set_service(mock_service)

    app = create_app()

    # Synchronous test client via httpx
    from starlette.testclient import TestClient
    client = TestClient(app)
    return client

