"""
Groq AI Recommendation Engine for Phase 4.
Calls Groq Cloud API using Llama 3 models with JSON mode, and provides mock generation
when API key is not yet configured.
"""

import json
import os
import time
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from phase2.models import UserQuery
from phase3.models import CandidateRestaurant
from phase4.config import (
    DEFAULT_GROQ_MODEL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    GROQ_API_KEY_ENV,
)
from phase4.models import RecommendationResponse, RecommendedRestaurant
from phase4.prompts import SYSTEM_PROMPT, build_recommendation_prompt

# Load environment variables from .env if present
load_dotenv()


class GroqRecommendationEngine:
    """Handles prompt construction and execution against Groq's high-speed LLM inference API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_GROQ_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ):
        self.api_key = api_key or os.getenv(GROQ_API_KEY_ENV)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = None

        if self.api_key:
            try:
                from groq import Groq
                self._client = Groq(api_key=self.api_key)
            except Exception:
                self._client = None

    def is_live_api_ready(self) -> bool:
        """Checks if a valid Groq API key is configured."""
        return bool(self.api_key and self._client is not None)

    def generate_recommendations(
        self,
        query: UserQuery,
        candidates: List[CandidateRestaurant],
        force_mock: bool = False,
    ) -> RecommendationResponse:
        """
        Generates structured restaurant recommendations.
        Uses live Groq API if api_key is available; falls back to deterministic mock if not.
        """
        if not candidates:
            return RecommendationResponse(
                query_summary={"city": query.city, "budget": query.max_budget},
                recommendations=[],
                overall_ai_summary=f"No matching restaurants found in {query.city} within Rs. {int(query.max_budget)}.",
                model_name=self.model,
                latency_seconds=0.0,
            )

        if not force_mock and self.is_live_api_ready():
            return self._generate_via_groq_api(query, candidates)
        else:
            return self._generate_mock_recommendations(query, candidates)

    def _generate_via_groq_api(
        self,
        query: UserQuery,
        candidates: List[CandidateRestaurant],
    ) -> RecommendationResponse:
        """Executes live chat completion against Groq API."""
        prompt = build_recommendation_prompt(query, candidates)

        start_time = time.time()
        try:
            chat_completion = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"},
            )
            latency = round(time.time() - start_time, 2)
            content = chat_completion.choices[0].message.content
            parsed_json = json.loads(content)

            return self._parse_json_to_response(parsed_json, query, latency, is_mock=False)

        except Exception as err:
            # If live API encounters an error, fallback gracefully to mock with error logged in summary
            latency = round(time.time() - start_time, 2)
            mock_resp = self._generate_mock_recommendations(query, candidates)
            mock_resp.overall_ai_summary += f" (Note: Live Groq call failed: {err}; fallback applied.)"
            mock_resp.latency_seconds = latency
            return mock_resp

    def _generate_mock_recommendations(
        self,
        query: UserQuery,
        candidates: List[CandidateRestaurant],
    ) -> RecommendationResponse:
        """
        Deterministic mock generator for offline development and test suites
        when GROQ_API_KEY is not yet entered.
        """
        start_time = time.time()
        recs: List[RecommendedRestaurant] = []

        for c in candidates:
            # Generate grounded dish highlights
            dishes = [d.strip() for d in c.dish_liked.split(",") if d.strip()][:3]
            if not dishes:
                dishes = [c.cuisines.split(",")[0].strip() + " Special"] if c.cuisines else ["Chef's Special"]

            savings_text = (
                f"Rs. {c.budget_savings} under your budget"
                if c.budget_savings > 0
                else f"Fits your budget of Rs. {int(query.max_budget)}"
            )

            rationale = (
                f"{c.restaurant_name} is a top-rated choice in {c.location} with a {c.rating} rating from {c.votes} diners. "
                f"It serves acclaimed {c.cuisines} and fits comfortably at Rs. {c.cost_for_two} for two."
            )

            recs.append(
                RecommendedRestaurant(
                    restaurant_name=c.restaurant_name,
                    location=c.location,
                    cost_for_two=c.cost_for_two,
                    rating=c.rating,
                    cuisines=c.cuisines,
                    ai_rationale=rationale,
                    must_try_dishes=dishes,
                    budget_verdict=savings_text,
                    online_order=c.online_order,
                    book_table=c.book_table,
                )
            )

        budget_summary = f"Rs. {int(query.min_budget)} to Rs. {int(query.max_budget)}" if query.min_budget > 0 else f"Rs. {int(query.max_budget)}"
        pref_note = f" focusing on '{query.preferences}'" if query.preferences else ""
        summary = (
            f"Found {len(recs)} premier dining options in {query.city} within your budget of {budget_summary}{pref_note}."
        )

        latency = round(time.time() - start_time, 4)
        return RecommendationResponse(
            query_summary={
                "city": query.city,
                "budget_for_two": int(query.max_budget),
                "preferences": query.preferences,
            },
            recommendations=recs,
            overall_ai_summary=summary,
            model_name=f"{self.model} (mock-ready)",
            latency_seconds=latency,
            is_mock=True,
        )

    def _parse_json_to_response(
        self,
        data: Dict[str, Any],
        query: UserQuery,
        latency: float,
        is_mock: bool,
    ) -> RecommendationResponse:
        """Parses and validates LLM JSON output into a RecommendationResponse."""
        recs_data = data.get("recommendations", [])
        recs: List[RecommendedRestaurant] = []

        for item in recs_data:
            rec = RecommendedRestaurant(
                restaurant_name=item.get("restaurant_name", "Unknown Restaurant"),
                location=item.get("location", query.city),
                cost_for_two=int(item.get("cost_for_two", query.max_budget)),
                rating=float(item.get("rating", 4.0)),
                cuisines=str(item.get("cuisines", "")),
                ai_rationale=str(item.get("ai_rationale", "Recommended based on your preferences.")),
                must_try_dishes=item.get("must_try_dishes", []),
                budget_verdict=str(item.get("budget_verdict", f"Under Rs. {int(query.max_budget)}")),
                online_order=str(item.get("online_order", "No")),
                book_table=str(item.get("book_table", "No")),
            )
            recs.append(rec)

        summary = data.get(
            "overall_ai_summary",
            f"Here are the top {len(recs)} dining recommendations in {query.city}.",
        )

        return RecommendationResponse(
            query_summary={
                "city": query.city,
                "budget_for_two": int(query.max_budget),
                "preferences": query.preferences,
            },
            recommendations=recs,
            overall_ai_summary=summary,
            model_name=self.model,
            latency_seconds=latency,
            is_mock=is_mock,
        )

