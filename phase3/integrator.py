"""
Pipeline orchestrator for Phase 3: Integrate.
Glues Step 1 (Metadata Knowledge Base) with Step 2 (UserQuery) to generate
the candidate context payload for Step 4 (Recommendation Engine).
"""

from typing import Optional
from phase1.metadata_store import MetadataStore
from phase2.models import UserQuery
from phase3.context_fusion import ContextFusionEngine
from phase3.filter_engine import FilterEngine
from phase3.models import IntegrationContextPayload


class IntegrationPipeline:
    """Coordinates metadata filtering, preference scoring, and context assembly."""

    def __init__(
        self,
        filter_engine: Optional[FilterEngine] = None,
        fusion_engine: Optional[ContextFusionEngine] = None,
    ):
        self._filter_engine = filter_engine
        self.fusion_engine = fusion_engine or ContextFusionEngine()

    def run(
        self,
        query: UserQuery,
        metadata_store: MetadataStore,
        max_candidates: int = 10,
        enable_relaxation: bool = True,
    ) -> IntegrationContextPayload:
        """
        Executes the integration flow:
        1. Hard filter candidate restaurants from MetadataStore based on query city & budget.
        2. Score and rank candidates using preference fusion and review metrics.
        3. Build structured LLM context string for Step 4.

        Returns:
            IntegrationContextPayload ready for Groq LLM consumption.
        """
        filter_engine = self._filter_engine or FilterEngine(metadata_store)

        # 1. Filter candidates
        raw_candidates, applied_relaxation, relaxation_notes = filter_engine.filter_candidates(
            query=query,
            limit=50,
            enable_relaxation=enable_relaxation,
        )

        # 2. Score and re-rank candidates based on user preferences and quality metrics
        ranked_candidates = self.fusion_engine.rank_and_score_candidates(
            candidates=raw_candidates,
            query=query,
            max_candidates=max_candidates,
        )

        # 3. Build token-efficient context text for Groq LLM
        context_text = self.fusion_engine.build_llm_context(ranked_candidates, query)

        return IntegrationContextPayload(
            query=query,
            candidates=ranked_candidates,
            total_found=len(raw_candidates),
            applied_relaxation=applied_relaxation,
            relaxation_notes=relaxation_notes,
            context_text=context_text,
            metadata={
                "returned_candidates_count": len(ranked_candidates),
                "has_preferences": bool(query.preferences),
            },
        )

