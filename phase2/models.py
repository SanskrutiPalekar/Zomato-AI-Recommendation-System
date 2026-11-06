"""
Pydantic data models for Phase 2: User Input.
Provides strict schema validation and normalization for City and Price queries.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class PricePreference(BaseModel):
    """Normalized price/budget preference extracted from user input."""

    raw_input: str
    max_price: float = Field(..., gt=0, description="Upper bound budget for two people in INR")
    min_price: float = Field(default=0.0, ge=0, description="Lower bound budget for two people in INR")
    flex_tolerance_pct: float = Field(default=0.0, ge=0, description="Tolerance percentage applied to budget")

    @property
    def effective_max_price(self) -> float:
        """Returns max price with tolerance applied (e.g., max_price * 1.10)."""
        return round(self.max_price * (1.0 + self.flex_tolerance_pct), 2)


class CityPreference(BaseModel):
    """Normalized city/locality preference resolved from user input."""

    raw_input: str
    resolved_city: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    is_exact_match: bool
    suggestions: List[str] = Field(default_factory=list)


class UserQuery(BaseModel):
    """Complete, validated user search request ready for Step 3 integration."""

    city: str = Field(..., min_length=1, description="Standardized city/locality name")
    max_budget: float = Field(..., gt=0, description="Maximum budget for two people in INR")
    min_budget: float = Field(default=0.0, ge=0, description="Minimum budget for two people in INR")
    preferences: Optional[str] = Field(default=None, description="Optional taste/dietary/ambience notes")
    raw_city_input: str
    raw_budget_input: str
    city_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("city")
    @classmethod
    def clean_city_string(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("City name cannot be empty.")
        return cleaned

    def summary(self) -> str:
        budget_str = f"Rs. {int(self.min_budget)} - Rs. {int(self.max_budget)}" if self.min_budget > 0 else f"Up to Rs. {int(self.max_budget)}"
        pref_str = f" | Preferences: '{self.preferences}'" if self.preferences else ""
        return f"City: {self.city} | Budget: {budget_str}{pref_str}"

