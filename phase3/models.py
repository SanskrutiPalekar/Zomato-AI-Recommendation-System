"""
Data models for Phase 3: Integration & Candidate Context Fusion.
Prepares validated candidates and formatted context payloads for Step 4 (Groq LLM).
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from phase2.models import UserQuery


class CandidateRestaurant(BaseModel):
    """Represents a restaurant candidate that passed Step 3 filters."""

    restaurant_id: int
    restaurant_name: str
    city: str
    location: str
    cost_for_two: int
    rating: float
    votes: int
    cuisines: str = ""
    rest_type: str = ""
    dish_liked: str = ""
    online_order: str = "No"
    book_table: str = "No"
    relevance_score: float = Field(default=0.0, description="Preference match score between 0.0 and 1.0")
    budget_savings: int = Field(default=0, description="Amount in INR below the user's maximum budget")

    def to_context_summary(self) -> str:
        """Compact text summary formatted for LLM context injection."""
        lines = [
            f"- Restaurant: {self.restaurant_name} ({self.location})",
            f"  Cost for Two: Rs. {self.cost_for_two} | Rating: {self.rating}/5.0 ({self.votes} votes)",
            f"  Cuisines: {self.cuisines} | Type: {self.rest_type}",
        ]
        if self.dish_liked:
            lines.append(f"  Popular Dishes: {self.dish_liked}")
        services = []
        if self.online_order == "Yes":
            services.append("Delivery Available")
        if self.book_table == "Yes":
            services.append("Table Booking")
        if services:
            lines.append(f"  Services: {', '.join(services)}")
        return "\n".join(lines)


class IntegrationContextPayload(BaseModel):
    """The structured payload bridging Step 1 & Step 2 into Step 4 (Recommendation)."""

    query: UserQuery
    candidates: List[CandidateRestaurant]
    total_found: int
    applied_relaxation: bool = False
    relaxation_notes: Optional[str] = None
    context_text: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)

