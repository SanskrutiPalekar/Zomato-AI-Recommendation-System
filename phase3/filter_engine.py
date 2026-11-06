"""
Metadata and constraint filter engine for Phase 3.
Filters candidate restaurants based on validated UserQuery constraints with graceful relaxation fallback.
"""

from typing import List, Optional, Tuple
from phase1.metadata_store import MetadataStore
from phase2.models import UserQuery
from phase3.models import CandidateRestaurant


class FilterEngine:
    """Filters restaurant records from MetadataStore using UserQuery constraints."""

    def __init__(self, metadata_store: MetadataStore):
        self.store = metadata_store

    def filter_candidates(
        self,
        query: UserQuery,
        limit: int = 200,
        enable_relaxation: bool = True,
    ) -> Tuple[List[CandidateRestaurant], bool, Optional[str]]:
        """
        Retrieves matching restaurants based on city/locality and budget constraints.
        If strict matching yields zero results and relaxation is enabled,
        gracefully broadens budget and/or locality.

        Returns:
            Tuple of (candidates_list, applied_relaxation_flag, relaxation_notes)
        """
        # 1. Primary Filter: Exact / Substring locality & budget window
        raw_results = self.store.query_by_city_and_price(
            city=query.city,
            max_price=query.max_budget,
            min_price=query.min_budget,
            limit=limit,
        )

        applied_relaxation = False
        relaxation_notes = None

        # 2. Relaxation Fallback if no records found
        if not raw_results and enable_relaxation:
            # Step A: Try relaxing budget ceiling by +20%
            relaxed_budget = round(query.max_budget * 1.20, 2)
            raw_results = self.store.query_by_city_and_price(
                city=query.city,
                max_price=relaxed_budget,
                min_price=query.min_budget,
                limit=limit,
            )
            if raw_results:
                applied_relaxation = True
                relaxation_notes = (
                    f"No restaurants found under Rs. {int(query.max_budget)} in {query.city}. "
                    f"Expanded budget to Rs. {int(relaxed_budget)} to find matching options."
                )
            else:
                # Step B: Try relaxing to broader Bangalore region
                if query.city.lower() != "bangalore":
                    raw_results = self.store.query_by_city_and_price(
                        city="Bangalore",
                        max_price=query.max_budget,
                        min_price=query.min_budget,
                        limit=limit,
                    )
                    if raw_results:
                        applied_relaxation = True
                        relaxation_notes = (
                            f"No restaurants found in {query.city} within budget. "
                            f"Expanded search to wider Bangalore region."
                        )

        # 3. Transform database rows to CandidateRestaurant models
        candidates: List[CandidateRestaurant] = []
        for row in raw_results:
            cost = int(row.get("cost_for_two", 0))
            savings = max(0, int(query.max_budget - cost))
            candidate = CandidateRestaurant(
                restaurant_id=int(row["restaurant_id"]),
                restaurant_name=str(row["restaurant_name"]),
                city=str(row.get("city", "")),
                location=str(row.get("location", "")),
                cost_for_two=cost,
                rating=float(row.get("rating", 0.0)),
                votes=int(row.get("votes", 0)),
                cuisines=str(row.get("cuisines", "")),
                rest_type=str(row.get("rest_type", "")),
                dish_liked=str(row.get("dish_liked", "")),
                online_order=str(row.get("online_order", "No")),
                book_table=str(row.get("book_table", "No")),
                budget_savings=savings,
            )
            candidates.append(candidate)

        return candidates, applied_relaxation, relaxation_notes

