"""
CLI runner for Phase 1: Input the Zomato User Data.
Allows running the ingestion and cleaning pipeline directly from terminal.
"""

import argparse
import sys
from pathlib import Path

# Ensure workspace root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pandas as pd

from phase1.config import RAW_DATA_DIR
from phase1.pipeline import Phase1Pipeline


def main():
    parser = argparse.ArgumentParser(
        description="Phase 1: Ingest, clean, and index Zomato Restaurant data."
    )
    parser.add_argument(
        "--csv-path",
        type=str,
        default=None,
        help="Path to local zomato.csv. If omitted, checks default data/raw/zomato.csv",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="Number of rows to load (for fast testing/development).",
    )
    parser.add_argument(
        "--save-processed",
        action="store_true",
        default=True,
        help="Whether to save the cleaned data to data/processed/zomato_cleaned.csv",
    )
    args = parser.parse_args()

    pipeline = Phase1Pipeline()

    print("\n" + "=" * 60)
    print(" Zomato AI Recommendation — Phase 1 Pipeline Runner")
    print("=" * 60)

    csv_path = Path(args.csv_path) if args.csv_path else RAW_DATA_DIR / "zomato.csv"

    if not csv_path.exists():
        print(f"\n[!] Dataset file not found at: {csv_path}")
        print("    You can place 'zomato.csv' inside data/raw/ or pass --csv-path <path>")
        print("    Running Phase 1 demonstration using built-in verified sample records...\n")

        sample_data = [
            {
                "name": "Jalsa",
                "rate": "4.1/5",
                "votes": 775,
                "location": "Banashankari",
                "listed_in(city)": "Banashankari",
                "cuisines": "North Indian, Mughlai, Chinese",
                "approx_cost(for two people)": "800",
                "dish_liked": "Pasta, Lunch Buffet, Masala Papad",
                "rest_type": "Casual Dining",
                "online_order": "Yes",
                "book_table": "Yes",
            },
            {
                "name": "Spice Elephant",
                "rate": "4.1/5",
                "votes": 787,
                "location": "Banashankari",
                "listed_in(city)": "Banashankari",
                "cuisines": "Chinese, North Indian, Thai",
                "approx_cost(for two people)": "1,200",
                "dish_liked": "Momos, Lunch Buffet, Chocolate Mousse",
                "rest_type": "Casual Dining",
                "online_order": "Yes",
                "book_table": "No",
            },
            {
                "name": "Empire Restaurant",
                "rate": "4.3 /5",
                "votes": 2500,
                "location": "Koramangala",
                "listed_in(city)": "Koramangala",
                "cuisines": "North Indian, Biryani, Mughlai",
                "approx_cost(for two people)": "750",
                "dish_liked": "Ghee Rice, Chicken Kebab, Coin Parotta",
                "rest_type": "Casual Dining",
                "online_order": "Yes",
                "book_table": "No",
            },
            {
                "name": "The New Cafe",
                "rate": "NEW",
                "votes": 25,
                "location": "Indiranagar",
                "listed_in(city)": "Indiranagar",
                "cuisines": "Cafe, Beverages",
                "approx_cost(for two people)": "500",
                "dish_liked": "Cold Coffee, Waffles",
                "rest_type": "Cafe",
                "online_order": "No",
                "book_table": "No",
            },
        ]
        result = pipeline.run(raw_df=pd.DataFrame(sample_data), save_processed=args.save_processed)
    else:
        print(f"\n[*] Ingesting from {csv_path} (sample size: {args.sample_size or 'Full'})...")
        result = pipeline.run(
            raw_csv_path=csv_path,
            nrows=args.sample_size,
            save_processed=args.save_processed,
        )

    print("\n[*] Phase 1 Pipeline Completed Successfully!")
    print("-" * 60)
    for key, value in result.stats.items():
        print(f"  - {key.replace('_', ' ').capitalize()}: {value}")
    print("-" * 60)

    # Demonstrate Step 1 metadata querying
    test_city = "Koramangala"
    test_budget = 800
    print(f"\n[*] Sample Integration Query Preview (City='{test_city}', Max Price=Rs. {test_budget}):")
    matches = result.metadata_store.query_by_city_and_price(city=test_city, max_price=test_budget)
    if matches:
        for r in matches:
            print(f"  -> {r['restaurant_name']} ({r['location']}) | Cost: Rs. {r['cost_for_two']} | Rating: {r['rating']}* | Cuisines: {r['cuisines']}")
    else:
        print("  -> No restaurants found matching criteria.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
