"""
Phase 4: Recommendation.
Groq LLM-powered restaurant recommendation engine with heuristic re-ranking
and structured JSON reasoning.
"""

from phase4.config import (
    DEFAULT_FINAL_RECS_COUNT,
    DEFAULT_GROQ_MODEL,
    FAST_GROQ_MODEL,
    GROQ_API_KEY_ENV,
)
from phase4.groq_engine import GroqRecommendationEngine
from phase4.models import RecommendationResponse, RecommendedRestaurant
from phase4.pipeline import Phase4Pipeline
from phase4.prompts import SYSTEM_PROMPT, build_recommendation_prompt
from phase4.reranker import CandidateReranker

__all__ = [
    "RecommendedRestaurant",
    "RecommendationResponse",
    "CandidateReranker",
    "GroqRecommendationEngine",
    "Phase4Pipeline",
    "SYSTEM_PROMPT",
    "build_recommendation_prompt",
    "DEFAULT_GROQ_MODEL",
    "FAST_GROQ_MODEL",
    "GROQ_API_KEY_ENV",
    "DEFAULT_FINAL_RECS_COUNT",
]

