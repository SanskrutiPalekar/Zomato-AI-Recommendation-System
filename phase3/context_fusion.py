"""
Context fusion and relevance scoring for Phase 3.
Enriches candidate restaurants with preference relevance and builds the LLM prompt context.
"""

import re
from typing import List, Optional
from phase2.models import UserQuery
from phase3.models import CandidateRestaurant


class ContextFusionEngine:
    """Computes preference relevance scores and generates LLM-ready context blocks."""

    VIBE_SYNONYMS = {
        "coffee": ["cafe", "coffee", "bakery", "bistro"],
        "cafe": ["cafe", "coffee", "bistro", "bakery"],
        "romantic": ["fine dining", "lounge", "casual dining", "continental", "italian"],
        "date": ["fine dining", "lounge", "cafe", "italian", "continental"],
        "party": ["pub", "bar", "club", "lounge", "microbrewery", "nightlife"],
        "drinks": ["pub", "bar", "microbrewery", "lounge", "beverages"],
        "chill": ["cafe", "lounge", "pub", "bistro"],
        "sweet": ["desserts", "ice cream", "bakery", "mithai"],
        "dessert": ["desserts", "ice cream", "bakery", "waffle"],
        "quick": ["quick bites", "fast food", "street food", "food truck"],
        "street": ["street food", "quick bites", "chaat", "fast food"],
        "family": ["casual dining", "fine dining", "north indian", "south indian"],
        "healthy": ["healthy food", "salad", "juices", "sandwich"],
        "veg": ["vegetarian", "pure veg", "south indian", "north indian", "street food"],
        "vegetarian": ["vegetarian", "pure veg", "south indian", "north indian"],
    }

    @classmethod
    def calculate_preference_relevance(
        cls,
        candidate: CandidateRestaurant,
        preferences: Optional[str],
    ) -> float:
        """
        Calculates a relevance score (0.0 to 1.0) based on how well the candidate's
        name, cuisines, dishes, and dining type match the user's taste/ambience preferences.
        """
        if not preferences:
            return 0.5  # Neutral default when no preferences are specified

        stop_words = {"and", "the", "for", "with", "food", "place", "good", "best", "spot", "spots", "vibe"}
        pref_tokens = [
            t.strip().lower()
            for t in re.split(r"[,;|\s]+", preferences)
            if len(t.strip()) >= 2 and t.strip().lower() not in stop_words
        ]
        if not pref_tokens:
            return 0.5

        searchable_text = (
            f"{candidate.restaurant_name} {candidate.cuisines} "
            f"{candidate.dish_liked} {candidate.rest_type}"
        ).lower()

        matched_tokens = 0
        for token in pref_tokens:
            expanded_terms = [token] + cls.VIBE_SYNONYMS.get(token, [])
            if any(term in searchable_text for term in expanded_terms):
                matched_tokens += 1

        relevance = matched_tokens / len(pref_tokens)
        return round(min(1.0, relevance), 2)

    def rank_and_score_candidates(
        self,
        candidates: List[CandidateRestaurant],
        query: UserQuery,
        max_candidates: int = 10,
    ) -> List[CandidateRestaurant]:
        """
        Scores and ranks candidates balancing preference relevance, rating, and review count.
        When preferences are specified and matching restaurants exist, filters out non-matches.
        """
        scored_candidates: List[CandidateRestaurant] = []

        for c in candidates:
            c.relevance_score = self.calculate_preference_relevance(c, query.preferences)
            scored_candidates.append(c)

        has_pref = bool(query.preferences)

        def sort_key(item: CandidateRestaurant):
            rating_norm = item.rating / 5.0
            votes_norm = min(1.0, (item.votes / 1000.0))
            if has_pref:
                return (
                    1 if item.relevance_score > 0 else 0,
                    (0.65 * item.relevance_score) + (0.25 * rating_norm) + (0.10 * votes_norm),
                )
            else:
                return (0, (0.60 * rating_norm) + (0.40 * votes_norm))

        scored_candidates.sort(key=sort_key, reverse=True)
        return scored_candidates[:max_candidates]

    def build_llm_context(
        self,
        candidates: List[CandidateRestaurant],
        query: UserQuery,
    ) -> str:
        """
        Generates a token-efficient, structured context block ready to be passed
        to Step 4 (Groq LLM).
        """
        if not candidates:
            return "No matching restaurants found within the specified criteria."

        header = [
            f"=== Search Constraints ===",
            f"Target Location: {query.city}",
            f"Budget Range   : Rs. {int(query.min_budget)} to Rs. {int(query.max_budget)} for two",
        ]
        if query.preferences:
            header.append(f"User Preferences: {query.preferences}")
        header.append(f"\n=== Filtered Candidate Pool ({len(candidates)} restaurants) ===")

        body = [c.to_context_summary() for c in candidates]
        return "\n".join(header) + "\n\n" + "\n\n".join(body)

