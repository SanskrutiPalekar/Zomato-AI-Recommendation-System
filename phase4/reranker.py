"""
Candidate re-ranking and scoring engine for Phase 4.
Calculates composite heuristic scores to prioritize the top candidate pool for Groq LLM inference.
"""

import math
from typing import List

from phase2.models import UserQuery
from phase3.models import CandidateRestaurant
from phase4.config import (
    DEFAULT_FINAL_RECS_COUNT,
    MAX_FINAL_RECS_COUNT,
    WEIGHT_BUDGET,
    WEIGHT_RATING,
    WEIGHT_VOTES,
)


class CandidateReranker:
    """Computes composite heuristic scores to select top candidate restaurants."""

    def __init__(
        self,
        weight_rating: float = WEIGHT_RATING,
        weight_votes: float = WEIGHT_VOTES,
        weight_budget: float = WEIGHT_BUDGET,
    ):
        self.w_rating = weight_rating
        self.w_votes = weight_votes
        self.w_budget = weight_budget

    def compute_score(self, candidate: CandidateRestaurant, query: UserQuery) -> float:
        """
        Computes the composite rank score for a candidate:
        Score = w1 * NormRating + w2 * LogVotes + w3 * BudgetEfficiency + w4 * Relevance
        """
        # 1. Rating component: normalized between 0 and 1 (ratings are 0.0 to 5.0)
        norm_rating = candidate.rating / 5.0

        # 2. Votes component: log10 scale, normalized against 10,000 votes (log10(10001) ~ 4.0)
        log_votes = math.log10(candidate.votes + 1) / 4.0
        norm_votes = min(1.0, max(0.0, log_votes))

        # 3. Budget proximity / efficiency component: higher score for staying comfortably below budget
        if query.max_budget > 0:
            cost_ratio = candidate.cost_for_two / query.max_budget
            budget_efficiency = max(0.0, min(1.0, 1.0 - (cost_ratio * 0.5)))
        else:
            budget_efficiency = 0.5

        # 4. Preference relevance (from Phase 3)
        relevance = candidate.relevance_score

        # Combine: if user specified preferences, heavily weight relevance so
        # unrelated cheap/popular spots do not outrank matching dishes/vibes
        if query.preferences:
            total_score = (
                (0.55 * relevance)
                + (0.25 * norm_rating)
                + (0.10 * norm_votes)
                + (0.10 * budget_efficiency)
            )
        else:
            total_score = (
                (self.w_rating * norm_rating)
                + (self.w_votes * norm_votes)
                + (self.w_budget * budget_efficiency)
                + (0.20 * relevance)
            )
        return round(total_score, 4)

    def select_top_candidates(
        self,
        candidates: List[CandidateRestaurant],
        query: UserQuery,
        target_count: int = DEFAULT_FINAL_RECS_COUNT,
    ) -> List[CandidateRestaurant]:
        """
        Scores all candidates and returns top candidates sorted by composite score.
        """
        if not candidates:
            return []

        # When user specified dish/vibe preferences, filter to candidates that actually match
        # (relevance_score > 0) whenever at least 1 matching restaurant exists
        pool = candidates
        if query.preferences:
            matching = [c for c in candidates if c.relevance_score > 0]
            if matching:
                pool = matching

        scored = [(c, self.compute_score(c, query)) for c in pool]
        # Sort descending by score
        scored.sort(key=lambda pair: pair[1], reverse=True)

        k = min(len(scored), max(1, min(target_count, MAX_FINAL_RECS_COUNT)))
        return [pair[0] for pair in scored[:k]]

