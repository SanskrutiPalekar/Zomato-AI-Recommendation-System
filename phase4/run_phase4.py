"""
CLI runner for Phase 4: Groq AI Recommendation Engine.
Demonstrates end-to-end flow from Step 1 to Step 4.
"""

import argparse
import sys
from pathlib import Path
import pandas as pd

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

from phase1.metadata_store import MetadataStore
from phase2.input_handler import InputHandler
from phase3.integrator import IntegrationPipeline
from phase4.config import DEFAULT_GROQ_MODEL
from phase4.groq_engine import GroqRecommendationEngine
from phase4.pipeline import Phase4Pipeline


def get_demo_store() -> MetadataStore:
    """Creates a sample store with verified Bangalore restaurants."""
    store = MetadataStore()
    demo_records = [
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
    ]
    store.index_dataframe(pd.DataFrame(demo_records))
    return store


def main():
    parser = argparse.ArgumentParser(description="Phase 4: Groq Recommendation Engine Runner.")
    parser.add_argument("--city", type=str, default="koramangla", help="City / locality input")
    parser.add_argument("--price", type=str, default="under 800", help="Budget input")
    parser.add_argument("--preferences", type=str, default="Biryani", help="Optional food preferences")
    parser.add_argument("--api-key", type=str, default=None, help="Groq API key (optional, can also use GROQ_API_KEY env var)")
    parser.add_argument("--force-mock", action="store_true", help="Force mock generation mode")
    args = parser.parse_args()

    print("\n" + "=" * 65)
    print(" Zomato AI Recommendation — Phase 4: Groq AI Recommendation Engine")
    print("=" * 65)

    # 1. Initialize Step 1 Store
    store = get_demo_store()

    # 2. Process Step 2 User Query
    handler = InputHandler()
    query = handler.process_inputs(args.city, args.price, args.preferences)
    print(f"[*] Validated Query: {query.summary()}")

    # 3. Integrate Step 3 Context
    integrator = IntegrationPipeline()
    payload = integrator.run(query=query, metadata_store=store, max_candidates=5)
    print(f"[*] Step 3 Integration: {payload.total_found} candidates retrieved.")

    # 4. Execute Step 4 Recommendation
    engine = GroqRecommendationEngine(api_key=args.api_key)
    pipeline = Phase4Pipeline(engine=engine)

    mode_label = "Live Groq API" if (engine.is_live_api_ready() and not args.force_mock) else "Mock Fallback (API Key not set)"
    print(f"[*] Execution Mode: {mode_label}")
    if not engine.is_live_api_ready() and not args.force_mock:
        print("    [TIP] To enable live LLM generation, set GROQ_API_KEY environment variable")
        print("          or pass --api-key <your-groq-key>")

    response = pipeline.run(payload, force_mock=args.force_mock)

    print("\n" + "-" * 65)
    print(" AI RECOMMENDATION RESULTS (Step 4 Output):")
    print("-" * 65)
    print(f"Overview: {response.overall_ai_summary}")
    print(f"Model: {response.model_name} | Latency: {response.latency_seconds}s\n")

    for idx, rec in enumerate(response.recommendations, 1):
        print(f"[{idx}] {rec.restaurant_name} ({rec.location})")
        print(f"    Rating: {rec.rating}* | Cost for Two: Rs. {rec.cost_for_two} ({rec.budget_verdict})")
        print(f"    Cuisines: {rec.cuisines}")
        print(f"    AI Rationale: {rec.ai_rationale}")
        print(f"    Must-Try Dishes: {', '.join(rec.must_try_dishes)}")
        print(f"    Services: Online Order: {rec.online_order} | Table Booking: {rec.book_table}")
        print()
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()

