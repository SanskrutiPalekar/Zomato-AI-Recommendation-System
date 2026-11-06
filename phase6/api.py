"""
FastAPI application for Phase 6.
Exposes REST endpoints that integrate with the ZomatoAIService (Steps 1–5)
to serve restaurant recommendations over HTTP.
"""

import sys
from pathlib import Path

# Ensure workspace root is on sys.path for imports
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from phase6.schemas import (
    CityListResponse,
    ErrorResponse,
    HealthResponse,
    RecommendedRestaurantOut,
    RecommendRequest,
    RecommendResponse,
    QuerySummary,
)
from phase6.dependencies import get_service, get_store


def create_app() -> FastAPI:
    """Factory function that creates and configures the FastAPI application."""

    app = FastAPI(
        title="Zomato AI Recommendation API",
        description="AI-powered restaurant recommendations using Groq LLM. "
        "Integrates data ingestion, input validation, candidate filtering, "
        "AI ranking, and structured responses.",
        version="1.0.0",
    )

    # CORS — allow React dev server and common origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ─── Routes ──────────────────────────────────────────────

    @app.get("/health", response_model=HealthResponse, tags=["System"])
    async def health_check():
        """Health check endpoint. Returns service status and data stats."""
        store = get_store()
        return HealthResponse(
            status="ok",
            restaurant_count=store.count(),
            cities_available=len(store.get_distinct_cities()),
        )

    @app.get("/api/cities", response_model=CityListResponse, tags=["Data"])
    async def list_cities():
        """Returns all available city/locality names from the indexed dataset."""
        store = get_store()
        cities = store.get_distinct_cities()
        locations = store.get_distinct_locations()
        combined = list(dict.fromkeys(cities + locations))
        return CityListResponse(cities=combined, total=len(combined))

    @app.post(
        "/api/recommend",
        response_model=RecommendResponse,
        responses={
            422: {"model": ErrorResponse, "description": "Invalid input"},
            404: {"model": ErrorResponse, "description": "No restaurants found"},
            503: {"model": ErrorResponse, "description": "AI service unavailable"},
        },
        tags=["Recommendations"],
    )
    async def recommend(req: RecommendRequest):
        """
        Main recommendation endpoint.
        Accepts city, price, and optional preferences.
        Runs the full 5-step pipeline and returns ranked AI recommendations.
        """
        service = get_service()

        try:
            response = service.search(
                city=req.city,
                price=req.price,
                preferences=req.preferences,
                force_mock=False,
                render_output=False,
                top_k=req.top_k,
            )
        except ValueError as e:
            # Step 2 validation errors (city not found, budget parse failure)
            raise HTTPException(status_code=422, detail=str(e))
        except ConnectionError as e:
            # Groq API connectivity issues
            raise HTTPException(status_code=503, detail=f"AI service unavailable: {e}")
        except Exception as e:
            # Unexpected errors — log and return 503
            raise HTTPException(status_code=503, detail=f"Service error: {e}")

        # Map internal RecommendationResponse → API RecommendResponse
        if not response.recommendations:
            raise HTTPException(
                status_code=404,
                detail=f"No restaurants found in '{req.city}' within budget '{req.price}'.",
            )

        query_summary = QuerySummary(
            city=response.query_summary.get("city", req.city),
            budget=response.query_summary.get("max_budget", 0)
            or response.query_summary.get("budget_for_two", 0)
            or response.query_summary.get("budget", 0),
            preferences=response.query_summary.get("preferences", req.preferences),
        )

        recs_out = []
        for idx, rec in enumerate(response.recommendations, 1):
            budget = query_summary.budget
            saving = int(budget - rec.cost_for_two) if budget > 0 else None
            recs_out.append(
                RecommendedRestaurantOut(
                    rank=idx,
                    restaurant_name=rec.restaurant_name,
                    location=rec.location,
                    rating=rec.rating,
                    cost_for_two=rec.cost_for_two,
                    cuisines=rec.cuisines,
                    online_order=rec.online_order,
                    book_table=rec.book_table,
                    ai_rationale=rec.ai_rationale,
                    must_try_dishes=rec.must_try_dishes,
                    budget_saving=saving,
                    budget_verdict=rec.budget_verdict,
                )
            )

        candidate_count = response.query_summary.get("candidate_count", len(recs_out))
        latency_ms = int(response.latency_seconds * 1000)

        return RecommendResponse(
            query=query_summary,
            recommendations=recs_out,
            overall_ai_summary=response.overall_ai_summary,
            model_name=response.model_name,
            latency_ms=latency_ms,
            candidate_count=candidate_count,
            is_mock=response.is_mock,
        )

    return app


# Module-level app instance (used by `uvicorn phase6.api:app`)
app = create_app()

