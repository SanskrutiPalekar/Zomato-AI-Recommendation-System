"""
Runner script for Phase 3: Integrate.
Demonstrates filtering, context fusion, and candidate payload generation for Step 4.
"""

import argparse
import sys
from pathlib import Path
import pandas as pd

# Ensure workspace root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from phase1.metadata_store import MetadataStore
from phase2.input_handler import InputHandler
from phase3.integrator import IntegrationPipeline


def get_demo_store() -> MetadataStore:
    """Creates a pre-populated metadata store with realistic Bangalore restaurants."""
    store = MetadataStore()
    demo_records = [
        {
            "restaurant_id": 1,
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
            "restaurant_id": 2,
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
            "restaurant_id": 3,
            "restaurant_name": "Truffles",
            "city": "koramangala",
            "location": "koramangala 5th block",
            "cost_for_two": 850,
            "rating": 4.5,
            "votes": 5800,
            "cuisines": "Cafe, American, Burger",
            "rest_type": "Cafe, Quick Bites",
            "dish_liked": "All American Burger, Ferrero Rocher Shake",
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
            "dish_liked": "Wood Fired Pizza, Tiramisu",
            "online_order": "No",
            "book_table": "Yes",
        },
        {
            "restaurant_id": 5,
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
    ]
    store.index_dataframe(pd.DataFrame(demo_records))
    return store


def main():
    parser = argparse.ArgumentParser(description="Phase 3: Integration & Context Fusion Runner.")
    parser.add_argument("--city", type=str, default="koramangla", help="City or locality")
    parser.add_argument("--price", type=str, default="under 800", help="Budget ceiling")
    parser.add_argument("--preferences", type=str, default="Biryani", help="Optional food preferences")
    args = parser.parse_args()

    print("\n" + "=" * 65)
    print(" Phase 3: Integration Pipeline (Step 1 + Step 2 -> Candidate Pool)")
    print("=" * 65)

    # 1. Step 1: Initialize Metadata Store
    store = get_demo_store()
    print(f"[*] Step 1 Store Initialized: {store.count()} indexed restaurants.")

    # 2. Step 2: Validate User Input
    handler = InputHandler()
    query = handler.process_inputs(args.city, args.price, args.preferences)
    print(f"[*] Step 2 Query Validated   : {query.summary()}")

    # 3. Step 3: Run Integration Pipeline
    integrator = IntegrationPipeline()
    payload = integrator.run(query=query, metadata_store=store, max_candidates=5)

    print(f"\n[*] Step 3 Integration Completed:")
    print(f"    - Total Matching Found : {payload.total_found}")
    print(f"    - Candidates Retained  : {len(payload.candidates)}")
    print(f"    - Relaxation Applied   : {payload.applied_relaxation}")
    if payload.relaxation_notes:
        print(f"    - Relaxation Notes     : {payload.relaxation_notes}")

    print("\n[*] Candidate Pool Ranked for Step 4:")
    for idx, c in enumerate(payload.candidates, 1):
        print(f"  {idx}. {c.restaurant_name} | Cost: Rs. {c.cost_for_two} | Rating: {c.rating}* | Score: {c.relevance_score}")
        print(f"     Savings: Rs. {c.budget_savings} below max budget | Cuisines: {c.cuisines}")

    print("\n" + "-" * 65)
    print(" Generated Prompt Context for Step 4 (Groq LLM):")
    print("-" * 65)
    print(payload.context_text)
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()

