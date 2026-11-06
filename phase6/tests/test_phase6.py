"""
Unit and integration tests for Phase 6: FastAPI REST API.
All tests run offline using the mock Groq engine — no API keys required.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


# ─── Health Check ─────────────────────────────────────────────


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_returns_200(self, api_client):
        resp = api_client.get("/health")
        assert resp.status_code == 200

    def test_health_response_structure(self, api_client):
        data = api_client.get("/health").json()
        assert data["status"] == "ok"
        assert data["restaurant_count"] == 5
        assert data["cities_available"] == 2


# ─── Cities Endpoint ─────────────────────────────────────────


class TestCitiesEndpoint:
    """Tests for GET /api/cities."""

    def test_cities_returns_200(self, api_client):
        resp = api_client.get("/api/cities")
        assert resp.status_code == 200

    def test_cities_response_has_known_localities(self, api_client):
        data = api_client.get("/api/cities").json()
        cities_lower = [c.lower() for c in data["cities"]]
        assert "koramangala" in cities_lower
        assert "indiranagar" in cities_lower

    def test_cities_total_matches_list_length(self, api_client):
        data = api_client.get("/api/cities").json()
        assert data["total"] == len(data["cities"])


# ─── Recommend Endpoint — Happy Path ─────────────────────────


class TestRecommendEndpoint:
    """Tests for POST /api/recommend (success cases)."""

    def test_recommend_returns_200_with_valid_input(self, api_client):
        resp = api_client.post(
            "/api/recommend",
            json={"city": "koramangala", "price": "under 800"},
        )
        assert resp.status_code == 200

    def test_recommend_response_has_recommendations(self, api_client):
        data = api_client.post(
            "/api/recommend",
            json={"city": "koramangala", "price": "under 800"},
        ).json()
        assert len(data["recommendations"]) > 0

    def test_recommend_response_structure(self, api_client):
        data = api_client.post(
            "/api/recommend",
            json={"city": "koramangala", "price": "800"},
        ).json()
        # Top-level fields
        assert "query" in data
        assert "recommendations" in data
        assert "overall_ai_summary" in data
        assert "model_name" in data
        assert "latency_ms" in data
        assert "is_mock" in data

    def test_recommend_query_echo(self, api_client):
        data = api_client.post(
            "/api/recommend",
            json={"city": "koramangala", "price": "under 800", "preferences": "Biryani"},
        ).json()
        query = data["query"]
        assert "koramangala" in query["city"].lower()
        assert query["budget"] > 0

    def test_recommend_restaurant_fields(self, api_client):
        data = api_client.post(
            "/api/recommend",
            json={"city": "koramangala", "price": "under 800"},
        ).json()
        rec = data["recommendations"][0]
        assert "rank" in rec
        assert "restaurant_name" in rec
        assert "location" in rec
        assert "rating" in rec
        assert "cost_for_two" in rec
        assert "cuisines" in rec
        assert "ai_rationale" in rec

    def test_recommend_restaurants_within_budget(self, api_client):
        data = api_client.post(
            "/api/recommend",
            json={"city": "koramangala", "price": "800"},
        ).json()
        for rec in data["recommendations"]:
            # Allow up to 10% budget flex
            assert rec["cost_for_two"] <= 880, (
                f"{rec['restaurant_name']} cost {rec['cost_for_two']} exceeds budget 800"
            )

    def test_recommend_ranks_are_sequential(self, api_client):
        data = api_client.post(
            "/api/recommend",
            json={"city": "koramangala", "price": "under 900"},
        ).json()
        ranks = [r["rank"] for r in data["recommendations"]]
        assert ranks == list(range(1, len(ranks) + 1))

    def test_recommend_with_preferences(self, api_client):
        data = api_client.post(
            "/api/recommend",
            json={"city": "koramangala", "price": "under 800", "preferences": "Biryani"},
        ).json()
        assert len(data["recommendations"]) > 0

    def test_recommend_mock_mode_flag(self, api_client):
        """is_mock field is present in the response (value depends on API key availability)."""
        data = api_client.post(
            "/api/recommend",
            json={"city": "koramangala", "price": "under 800"},
        ).json()
        assert "is_mock" in data
        assert isinstance(data["is_mock"], bool)


# ─── Recommend Endpoint — Error Cases ────────────────────────


class TestRecommendErrors:
    """Tests for POST /api/recommend (error handling)."""

    def test_missing_city_returns_422(self, api_client):
        resp = api_client.post(
            "/api/recommend",
            json={"price": "under 800"},
        )
        assert resp.status_code == 422

    def test_missing_price_returns_422(self, api_client):
        resp = api_client.post(
            "/api/recommend",
            json={"city": "koramangala"},
        )
        assert resp.status_code == 422

    def test_empty_body_returns_422(self, api_client):
        resp = api_client.post("/api/recommend", json={})
        assert resp.status_code == 422

    def test_empty_city_string_returns_422(self, api_client):
        resp = api_client.post(
            "/api/recommend",
            json={"city": "", "price": "500"},
        )
        assert resp.status_code == 422

    def test_empty_price_string_returns_422(self, api_client):
        resp = api_client.post(
            "/api/recommend",
            json={"city": "koramangala", "price": ""},
        )
        assert resp.status_code == 422


# ─── CORS Headers ────────────────────────────────────────────


class TestCORS:
    """Tests that CORS headers are set correctly for allowed origins."""

    def test_cors_allows_localhost_3000(self, api_client):
        resp = api_client.options(
            "/api/recommend",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"

