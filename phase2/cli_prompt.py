"""
Interactive CLI Prompt for Phase 2: User Input.
Handles user interaction, prompts for City & Budget, and displays validation feedback.
"""

import sys
from typing import Optional

from phase2.input_handler import InputHandler
from phase2.models import UserQuery


class CLIPrompt:
    """Handles terminal-based user input capture with interactive re-prompting on errors."""

    def __init__(self, handler: Optional[InputHandler] = None):
        self.handler = handler or InputHandler()

    def prompt_user(self) -> UserQuery:
        """
        Prompts user in CLI for City and Budget until valid inputs are provided.
        Returns the finalized UserQuery.
        """
        print("\n" + "=" * 60)
        print(" Zomato AI Concierge — Restaurant Search Input")
        print("=" * 60)

        # 1. Prompt City / Locality
        city_query = ""
        while True:
            try:
                city_raw = input("\n[?] Enter City or Locality (e.g. Koramangala, Indiranagar, Bangalore): ").strip()
                if not city_raw:
                    print("    [!] City cannot be empty. Please try again.")
                    continue
                # Validate locality immediately
                city_pref = self.handler.city_matcher.resolve(city_raw)
                if not city_pref.is_exact_match:
                    print(f"    [*] Matched to: '{city_pref.resolved_city}' (Confidence: {int(city_pref.confidence_score * 100)}%)")
                city_query = city_raw
                break
            except ValueError as err:
                print(f"    [!] Error: {err}")

        # 2. Prompt Budget / Price
        budget_query = ""
        while True:
            try:
                budget_raw = input("[?] Enter Budget for Two in Rs. (e.g. 800, 'under 1000', '500-1200'): ").strip()
                if not budget_raw:
                    print("    [!] Budget cannot be empty. Please try again.")
                    continue
                # Validate budget immediately
                self.handler.budget_parser.parse(budget_raw)
                budget_query = budget_raw
                break
            except ValueError as err:
                print(f"    [!] Error: {err}")

        # 3. Optional Preferences
        pref_raw = input("[?] (Optional) Any specific food or vibe preferences? (press Enter to skip): ").strip()

        # 4. Finalize Query
        query = self.handler.process_inputs(
            city_input=city_query,
            budget_input=budget_query,
            preferences_input=pref_raw if pref_raw else None,
        )

        print("\n" + "-" * 60)
        print(" [*] Search Query Confirmed:")
        print(f"     - Target Locality : {query.city}")
        print(f"     - Maximum Budget  : Rs. {int(query.max_budget)} (Base: Rs. {int(query.metadata.get('base_max_budget', query.max_budget))})")
        if query.min_budget > 0:
            print(f"     - Minimum Budget  : Rs. {int(query.min_budget)}")
        if query.preferences:
            print(f"     - Preferences     : {query.preferences}")
        print("-" * 60 + "\n")

        return query

