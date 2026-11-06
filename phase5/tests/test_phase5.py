"""
Integration tests for Phase 5 & Full End-to-End System.
Exercises all 5 layers:
  Step 1: Input Zomato user data (MetadataStore)
  Step 2: User Input (InputHandler)
  Step 3: Integrate (IntegrationPipeline)
  Step 4: Recommendation (Phase4Pipeline / Groq LLM)
  Step 5: Display to the User (DisplayAdapter)

Includes exactly 3 integration tests to respect Groq API rate limits.
"""

import os
import pytest

from phase4.config import GROQ_API_KEY_ENV
from phase5.display_adapter import CLIDisplayAdapter, JSONDisplayAdapter
from phase5.service import ZomatoAIService


# ============================================================================
# Integration Test 1: Full 5-Layer End-to-End Flow (Offline / Mock Mode)
# ============================================================================

def test_full_system_mock_mode_integration(mock_service: ZomatoAIService, json_display_adapter: JSONDisplayAdapter):
    """
    Test 1: Tests the complete 5-layer pipeline from raw user string inputs to
    display adapter output in mock mode without consuming external API rate limits.
    """
    response = mock_service.search(
        city="koramangla",          # Typo in city (Step 2 resolves to 'Koramangala')
        price="under 800",          # Natural language budget (Step 2 parses to Rs. 880)
        preferences="Biryani",       # Preference (Step 3 boosts Biryani spots)
        force_mock=True,
        render_output=True,
    )

    # 1. Verify Step 2 Input Resolution captured in Step 5 adapter
    assert json_display_adapter.last_query is not None
    assert json_display_adapter.last_query["city"] == "Koramangala"

    # 2. Verify Step 3 + Step 4 Recommendations
    assert len(response.recommendations) >= 1
    top_pick = response.recommendations[0]
    assert top_pick.restaurant_name == "Meghana Foods"
    assert top_pick.cost_for_two <= 880

    # 3. Verify Step 5 Display Serialization
    assert json_display_adapter.last_response is not None
    assert "recommendations" in json_display_adapter.last_response
    assert len(json_display_adapter.last_response["recommendations"]) >= 1


# ============================================================================
# Integration Test 2: Live Groq API End-to-End System Integration
# ============================================================================

@pytest.mark.skipif(
    not os.getenv(GROQ_API_KEY_ENV),
    reason="Requires GROQ_API_KEY environment variable.",
)
def test_full_system_live_groq_integration(integrated_store):
    """
    Test 2: Single live end-to-end integration test calling Groq LLM through
    all 5 layers and rendering via CLIDisplayAdapter.
    """
    cli_adapter = CLIDisplayAdapter()
    service = ZomatoAIService(
        metadata_store=integrated_store,
        display_adapter=cli_adapter,
    )

    response = service.search(
        city="indiranagar",
        price="under 1600",
        preferences="Pizza, Craft Beer",
        force_mock=False,
        render_output=True,
    )

    # Verify live Groq execution
    assert response.is_mock is False
    assert len(response.recommendations) >= 1
    assert response.latency_seconds > 0.0

    # Verify budget compliance of live recommendation
    top_rec = response.recommendations[0]
    assert top_rec.restaurant_name == "Toit Brewpub"
    assert top_rec.cost_for_two <= 1760  # 1600 + 10% tolerance
    assert len(top_rec.ai_rationale) > 15
    assert len(top_rec.must_try_dishes) >= 1


# ============================================================================
# Integration Test 3: Constraint Handling & Edge-Case Search
# ============================================================================

def test_full_system_budget_edge_case_integration(mock_service: ZomatoAIService, json_display_adapter: JSONDisplayAdapter):
    """
    Test 3: Tests end-to-end handling of an ultra-tight budget query,
    verifying fallback filtering and display output.
    """
    # Corner House costs 350; Meghana costs 600; Empire costs 750
    # User asks for budget 400. Corner House (350) should be the exclusive match.
    response = mock_service.search(
        city="Koramangala",
        price="400",
        preferences="Dessert",
        force_mock=True,
        render_output=True,
    )

    assert len(response.recommendations) == 1
    rec = response.recommendations[0]
    assert rec.restaurant_name == "Corner House Ice Cream"
    assert rec.cost_for_two == 350
    assert rec.cost_for_two <= 440  # 400 + 10% tolerance
    assert json_display_adapter.last_response is not None

