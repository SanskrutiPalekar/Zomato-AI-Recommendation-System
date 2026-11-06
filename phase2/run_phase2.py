"""
Runner script for Phase 2: User Input.
Demonstrates query parsing, fuzzy city matching, budget normalization, and CLI input.
"""

import argparse
import sys
from pathlib import Path

# Ensure workspace root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from phase2.cli_prompt import CLIPrompt
from phase2.input_handler import InputHandler


def main():
    parser = argparse.ArgumentParser(description="Phase 2: User Input Validation & Parsing Runner.")
    parser.add_argument("--city", type=str, default=None, help="City / locality input")
    parser.add_argument("--price", type=str, default=None, help="Budget / price input (e.g., 800, 'under 1000')")
    parser.add_argument("--preferences", type=str, default=None, help="Optional taste / vibe preferences")
    parser.add_argument("--interactive", action="store_true", help="Launch interactive CLI prompt")
    args = parser.parse_args()

    handler = InputHandler()

    if args.interactive or (args.city is None and args.price is None):
        if args.interactive:
            prompt = CLIPrompt(handler)
            query = prompt.prompt_user()
            print("[+] Query successfully validated and ready for Phase 3:")
            print(f"    {query.summary()}")
            return
        else:
            print("\n" + "=" * 60)
            print(" Phase 2: User Input Parsing — Automated Demonstration")
            print("=" * 60)
            test_queries = [
                ("koramangla", "800", "Biryani"),
                ("hsr", "under 1000", "Rooftop, Italian"),
                ("BLR", "500-1200", None),
                ("whitefeild", "fine dining", "Continental"),
            ]
            for city_in, price_in, pref_in in test_queries:
                print(f"\n[*] Raw Input -> City: '{city_in}', Price: '{price_in}', Preferences: '{pref_in}'")
                query = handler.process_inputs(city_in, price_in, pref_in)
                print(f"    [OK] Standardized: {query.summary()}")
                print(f"         Confidence : {int(query.city_confidence * 100)}% | Exact: {query.metadata['is_exact_city_match']}")
            print("\n" + "=" * 60)
            print(" To run interactively: python phase2/run_phase2.py --interactive")
            print("=" * 60 + "\n")
            return

    # Direct CLI arguments mode
    try:
        query = handler.process_inputs(
            city_input=args.city,
            budget_input=args.price,
            preferences_input=args.preferences,
        )
        print("\n[+] User Query Processed Successfully:")
        print(f"    Standardized Summary: {query.summary()}")
        print(f"    Target City         : {query.city} (Confidence: {int(query.city_confidence * 100)}%)")
        print(f"    Budget Range        : Rs. {query.min_budget} - Rs. {query.max_budget}")
        if query.preferences:
            print(f"    Preferences         : {query.preferences}")
        print()
    except ValueError as err:
        print(f"\n[!] Input Error: {err}\n", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

