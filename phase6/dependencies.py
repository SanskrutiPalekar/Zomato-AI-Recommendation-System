"""
Dependency management for Phase 6 API.
Provides singleton access to the MetadataStore and ZomatoAIService
so that all API routes share a single initialized service instance.
"""

import os
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# Ensure workspace root on path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from phase1.config import RAW_DATA_DIR
from phase1.metadata_store import MetadataStore
from phase1.pipeline import Phase1Pipeline
from phase4.pipeline import Phase4Pipeline
from phase5.display_adapter import JSONDisplayAdapter
from phase5.service import ZomatoAIService


# Module-level singletons
_store: Optional[MetadataStore] = None
_service: Optional[ZomatoAIService] = None


def _build_sample_store() -> MetadataStore:
    """Creates a MetadataStore with embedded sample records (no CSV required)."""
    store = MetadataStore()
    sample_records = [
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
            "dish_liked": "Chicken Boneless Biryani, Chilli Chicken, Paneer Biryani",
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
            "dish_liked": "Ghee Rice, Coin Parotta, Chicken Kebab",
            "online_order": "Yes",
            "book_table": "No",
        },
        {
            "restaurant_id": 3,
            "restaurant_name": "Truffles",
            "city": "koramangala",
            "location": "koramangala 5th block",
            "cost_for_two": 850,
            "rating": 4.5,
            "votes": 5800,
            "cuisines": "Cafe, American, Burger",
            "rest_type": "Cafe, Quick Bites",
            "dish_liked": "All American Burger, Ferrero Shake",
            "online_order": "Yes",
            "book_table": "No",
        },
        {
            "restaurant_id": 4,
            "restaurant_name": "Corner House Ice Cream",
            "city": "koramangala",
            "location": "koramangala 7th block",
            "cost_for_two": 350,
            "rating": 4.5,
            "votes": 3100,
            "cuisines": "Desserts, Ice Cream",
            "rest_type": "Dessert Parlor",
            "dish_liked": "Death By Chocolate, Hot Caramello",
            "online_order": "Yes",
            "book_table": "No",
        },
        {
            "restaurant_id": 5,
            "restaurant_name": "Toit Brewpub",
            "city": "indiranagar",
            "location": "indiranagar 100 feet road",
            "cost_for_two": 1500,
            "rating": 4.7,
            "votes": 12500,
            "cuisines": "Italian, Pizza, Brewery",
            "rest_type": "Microbrewery, Pub",
            "dish_liked": "Wood Fired Pizza, Tintin Craft Beer",
            "online_order": "No",
            "book_table": "Yes",
        },
        {
            "restaurant_id": 6,
            "restaurant_name": "Glen's Bakehouse",
            "city": "indiranagar",
            "location": "indiranagar 100 feet road",
            "cost_for_two": 600,
            "rating": 4.5,
            "votes": 4200,
            "cuisines": "Bakery, Desserts, Cafe",
            "rest_type": "Bakery, Cafe",
            "dish_liked": "Red Velvet Cupcake, Cheesecake, Lasagna",
            "online_order": "Yes",
            "book_table": "No",
        },
    ]
    store.index_dataframe(pd.DataFrame(sample_records))
    return store


def initialize_store(force_reinit: bool = False) -> MetadataStore:
    """
    Initializes or returns the singleton MetadataStore.
    Checks DATASET_FILE in .env first; if anything goes wrong, automatically
    falls back to zomato.csv or embedded sample data.
    """
    global _store
    if _store is not None and not force_reinit:
        return _store

    custom_file = os.getenv("DATASET_FILE", "").strip()
    candidates = []
    if custom_file:
        custom_path = Path(custom_file)
        if not custom_path.is_absolute():
            custom_path = RAW_DATA_DIR / custom_file
        candidates.append(custom_path)

    default_csv = RAW_DATA_DIR / "zomato.csv"
    if default_csv not in candidates:
        candidates.append(default_csv)

    processed_csv = BASE_DIR / "data" / "processed" / "zomato_cleaned.csv"
    if processed_csv not in candidates:
        candidates.append(processed_csv)

    for csv_path in candidates:
        if csv_path.exists():
            try:
                temp_store = MetadataStore()
                pipeline = Phase1Pipeline(metadata_store=temp_store)
                pipeline.run(raw_csv_path=csv_path, nrows=10000)
                if temp_store.count() > 0:
                    print(f"[*] Loaded dataset from: {csv_path} ({temp_store.count()} records)")
                    _store = temp_store
                    return _store
                else:
                    print(f"[!] Dataset {csv_path} yielded 0 valid records. Falling back...")
            except Exception as err:
                print(f"[!] Failed to load {csv_path} ({err}). Falling back to working dataset...")

    _store = _build_sample_store()
    return _store


def get_store() -> MetadataStore:
    """Returns the singleton MetadataStore, initializing if needed."""
    global _store
    if _store is None:
        initialize_store()
    return _store


def set_store(store: MetadataStore) -> None:
    """Override the store singleton (used in tests)."""
    global _store
    _store = store


def get_service() -> ZomatoAIService:
    """Returns the singleton ZomatoAIService, initializing if needed."""
    global _service
    if _service is None:
        store = get_store()
        _service = ZomatoAIService(
            metadata_store=store,
            recommendation_pipeline=Phase4Pipeline(),
            display_adapter=JSONDisplayAdapter(),
        )
    return _service


def set_service(service: ZomatoAIService) -> None:
    """Override the service singleton (used in tests)."""
    global _service
    _service = service


def reset_singletons() -> None:
    """Resets all singletons to None (used between tests)."""
    global _store, _service
    _store = None
    _service = None

