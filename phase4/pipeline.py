"""
Pipeline orchestrator for Phase 4: Recommendation.
Coordinates candidate re-ranking, Groq prompt execution, and response synthesis.
"""

from typing import Optional

from phase3.models import IntegrationContextPayload
from phase4.config import DEFAULT_FINAL_RECS_COUNT, DEFAULT_GROQ_MODEL
from phase4.groq_engine import GroqRecommendationEngine
from phase4.models import RecommendationResponse
from phase4.reranker import CandidateReranker


class Phase4Pipeline:
    """Executes Step 4 of the Zomato AI Recommendation Service."""

    def __init__(
        self,
        reranker: Optional[CandidateReranker] = None,
        engine: Optional[GroqRecommendationEngine] = None,
        target_recs_count: int = DEFAULT_FINAL_RECS_COUNT,
    ):
        self.reranker = reranker or CandidateReranker()
        self.engine = engine or GroqRecommendationEngine()
        self.target_recs_count = target_recs_count

    def run(
        self,
        payload: IntegrationContextPayload,
        force_mock: bool = False,
        target_count: Optional[int] = None,
    ) -> RecommendationResponse:
        """
        Executes the Phase 4 recommendation pipeline:
        1. Takes candidate restaurants from Phase 3 IntegrationContextPayload.
        2. Applies composite scoring to select the top 3-5 finalist restaurants.
        3. Calls Groq LLM to synthesize reasoned recommendations with must-try dishes.

        Returns:
            Structured RecommendationResponse.
        """
        k = target_count or self.target_recs_count

        # 1. Select top candidate finalists
        top_candidates = self.reranker.select_top_candidates(
            candidates=payload.candidates,
            query=payload.query,
            target_count=k,
        )

        # 2. Invoke Groq AI Recommendation Engine
        response = self.engine.generate_recommendations(
            query=payload.query,
            candidates=top_candidates,
            force_mock=force_mock,
        )

        return response

