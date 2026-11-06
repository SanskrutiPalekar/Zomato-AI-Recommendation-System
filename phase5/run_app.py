"""
Master Application Entrypoint for Zomato AI Restaurant Recommendation Service.
Integrates all 5 phases into a unified Command Line Interface (CLI).
"""

import argparse
import os
import sys
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# Ensure workspace root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from phase1.config import RAW_DATA_DIR
from phase1.metadata_store import MetadataStore
from phase1.pipeline import Phase1Pipeline
from phase4.groq_engine import GroqRecommendationEngine
from phase4.pipeline import Phase4Pipeline
from phase5.display_adapter import CLIDisplayAdapter
from phase5.service import ZomatoAIService


def initialize_step1_store() -> MetadataStore:
    """Initializes the Step 1 Metadata Store from .env DATASET_FILE, local zomato.csv, or seed dataset."""
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

    for csv_path in candidates:
        if csv_path.exists():
            try:
                print(f"[*] Ingesting restaurant dataset from: {csv_path}...")
                store = MetadataStore()
                pipeline = Phase1Pipeline(metadata_store=store)
                pipeline.run(raw_csv_path=csv_path, nrows=1000)
                if store.count() > 0:
                    return store
                print(f"[!] Dataset {csv_path} had 0 valid rows. Falling back...")
            except Exception as err:
                print(f"[!] Error loading {csv_path} ({err}). Falling back to working dataset...")

    store = MetadataStore()
    if False:
        pass
    else:
        # High quality sample records covering key Bangalore dining hubs
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


def main():
    parser = argparse.ArgumentParser(description="Zomato AI Restaurant Recommendation Service")
    parser.add_argument("--interactive", action="store_true", help="Launch interactive CLI prompt session")
    parser.add_argument("--city", type=str, default=None, help="City / locality (e.g. Koramangala, Indiranagar)")
    parser.add_argument("--price", type=str, default=None, help="Budget for two (e.g. 800, 'under 1000')")
    parser.add_argument("--preferences", type=str, default=None, help="Optional food or vibe preferences")
    parser.add_argument("--mock", action="store_true", help="Use offline mock mode (no Groq API calls)")
    args = parser.parse_args()

    # Step 1: Initialize Knowledge Base Store
    store = initialize_step1_store()

    # Initialize Service
    display_adapter = CLIDisplayAdapter()
    engine = GroqRecommendationEngine()
    recs_pipeline = Phase4Pipeline(engine=engine)

    service = ZomatoAIService(
        metadata_store=store,
        recommendation_pipeline=recs_pipeline,
        display_adapter=display_adapter,
    )

    if args.interactive or (not args.city and not args.price):
        # Interactive session mode
        service.run_interactive_session()
    else:
        # Direct CLI execution mode
        display_adapter.render_welcome()
        service.search(
            city=args.city,
            price=args.price,
            preferences=args.preferences,
            force_mock=args.mock,
        )


if __name__ == "__main__":
    main()

