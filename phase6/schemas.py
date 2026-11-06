"""
Pydantic request/response schemas for the Phase 6 REST API.
Decouples API contract from internal domain models.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    """Incoming recommendation search request from the frontend."""

    city: str = Field(
        ...,
        min_length=1,
        description="City or locality name (e.g. Koramangala, BTM, Indiranagar)",
        examples=["koramangala"],
    )
    price: str = Field(
        ...,
        min_length=1,
        description="Budget for two people (e.g. '800', 'under 1000', 'budget')",
        examples=["under 800"],
    )
    preferences: Optional[str] = Field(
        default=None,
        description="Optional food or vibe preferences (e.g. 'Biryani', 'vegetarian')",
        examples=["Biryani"],
    )
    top_k: int = Field(
        default=6,
        ge=1,
        le=20,
        description="Number of AI recommendations to return (default 6, max 20)",
    )


class RecommendedRestaurantOut(BaseModel):
    """Single restaurant recommendation in the API response."""

    rank: int = Field(..., description="Rank position (1-based)")
    restaurant_name: str
    location: str
    rating: float
    votes: Optional[int] = None
    cost_for_two: int
    cuisines: str = ""
    rest_type: Optional[str] = None
    online_order: str = "No"
    book_table: str = "No"
    ai_rationale: str = ""
    must_try_dishes: List[str] = Field(default_factory=list)
    budget_saving: Optional[int] = Field(
        default=None,
        description="Amount below budget (positive = savings, negative = over budget)",
    )
    budget_verdict: str = ""


class QuerySummary(BaseModel):
    """Echo of the resolved query parameters."""

    city: str
    budget: float
    preferences: Optional[str] = None


class RecommendResponse(BaseModel):
    """Full recommendation API response."""

    query: QuerySummary
    recommendations: List[RecommendedRestaurantOut] = Field(default_factory=list)
    overall_ai_summary: str = ""
    model_name: str = ""
    latency_ms: int = 0
    candidate_count: int = 0
    is_mock: bool = False


class CityListResponse(BaseModel):
    """Available cities/localities response."""

    cities: List[str] = Field(default_factory=list)
    total: int = 0


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    restaurant_count: int = 0
    cities_available: int = 0


class ErrorResponse(BaseModel):
    """Error detail body."""

    detail: str

