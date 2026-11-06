"""
Phase 6: Web API Layer (FastAPI).
Exposes the Zomato AI Recommendation Service as REST endpoints,
integrating all business logic from Steps 1–5.
"""

from phase6.schemas import RecommendRequest, RecommendResponse, CityListResponse, HealthResponse

__all__ = [
    "RecommendRequest",
    "RecommendResponse",
    "CityListResponse",
    "HealthResponse",
]

