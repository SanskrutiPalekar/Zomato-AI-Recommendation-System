"""
Pytest fixtures for Phase 3 tests.
"""

import pandas as pd
import pytest

from phase1.metadata_store import MetadataStore
from phase2.models import UserQuery
from phase3.context_fusion import ContextFusionEngine
from phase3.filter_engine import FilterEngine
from phase3.integrator import IntegrationPipeline


@pytest.fixture
def sample_indexed_store() -> MetadataStore:
    """Pre-populated MetadataStore fixture with diverse restaurants in Koramangala and Indiranagar."""
    store = MetadataStore()
    records = [
        {
            "restaurant_id": 1,
            "restaurant_name": "Meghana Foods",
            "city": "koramangala",
            "location": "koramangala 5th block",
            "cost_for_two": 600,
            "rating": 4.4,
            "votes": 4100,
            "cuisines": "Biryani, Andhra, South Indian",
            "rest_type": "Casual Dining",
            "dish_liked": "Chicken Biryani, Paneer Biryani",
            "online_order": "Yes",
            "book_table": "No",
        },
        {
            "restaurant_id": 2,
            "restaurant_name": "Empire Restaurant",
            "city": "koramangala",
            "location": "koramangala 5th block",
            "cost_for_two": 750,
            "rating": 4.2,
            "votes": 2500,
            "cuisines": "North Indian, Biryani, Mughlai",
            "rest_type": "Casual Dining",
            "dish_liked": "Ghee Rice, Chicken Kebab",
            "online_order": "Yes",
            "book_table": "No",
        },
        {
            "restaurant_id": 3,
            "restaurant_name": "Truffles",
            "city": "koramangala",
            "location": "koramangala 5th block",
            "cost_for_two": 900,
            "rating": 4.5,
            "votes": 6000,
            "cuisines": "Cafe, American, Burger",
            "rest_type": "Cafe, Quick Bites",
            "dish_liked": "All American Burger",
            "online_order": "Yes",
            "book_table": "No",
        },
        {
            "restaurant_id": 4,
            "restaurant_name": "Chianti Italian Ristorante",
            "city": "koramangala",
            "location": "koramangala 5th block",
            "cost_for_two": 1800,
            "rating": 4.6,
            "votes": 1200,
            "cuisines": "Italian, Pizza, Pasta",
            "rest_type": "Fine Dining",
            "dish_liked": "Wood Fired Pizza, Pasta Carbonara",
            "online_order": "No",
            "book_table": "Yes",
        },
        {
            "restaurant_id": 5,
            "restaurant_name": "Toit Brewpub",
            "city": "indiranagar",
            "location": "indiranagar 100 feet road",
            "cost_for_two": 1500,
            "rating": 4.7,
            "votes": 12000,
            "cuisines": "Finger Food, Pizza, Brewery",
            "rest_type": "Microbrewery, Pub",
            "dish_liked": "Craft Beer, Wood Fired Pizza",
            "online_order": "No",
            "book_table": "Yes",
        },
    ]
    store.index_dataframe(pd.DataFrame(records))
    return store


@pytest.fixture
def filter_engine(sample_indexed_store) -> FilterEngine:
    return FilterEngine(metadata_store=sample_indexed_store)


@pytest.fixture
def fusion_engine() -> ContextFusionEngine:
    return ContextFusionEngine()


@pytest.fixture
def integration_pipeline(filter_engine, fusion_engine) -> IntegrationPipeline:
    return IntegrationPipeline(filter_engine=filter_engine, fusion_engine=fusion_engine)

