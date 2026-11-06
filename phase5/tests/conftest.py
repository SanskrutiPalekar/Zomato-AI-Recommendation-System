"""
Pytest fixtures for Phase 5 integration tests.
"""

import pandas as pd
import pytest

from phase1.metadata_store import MetadataStore
from phase5.display_adapter import JSONDisplayAdapter
from phase5.service import ZomatoAIService


@pytest.fixture
def integrated_store() -> MetadataStore:
    """Pre-indexed store fixture for integration tests."""
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
    ]
    store.index_dataframe(pd.DataFrame(records))
    return store


@pytest.fixture
def json_display_adapter() -> JSONDisplayAdapter:
    return JSONDisplayAdapter()


@pytest.fixture
def mock_service(integrated_store, json_display_adapter) -> ZomatoAIService:
    return ZomatoAIService(
        metadata_store=integrated_store,
        display_adapter=json_display_adapter,
    )

