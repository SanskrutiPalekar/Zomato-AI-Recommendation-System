"""
Prompt engineering templates and builders for Groq LLM restaurant recommendation.
"""

from typing import List
from phase2.models import UserQuery
from phase3.models import CandidateRestaurant


SYSTEM_PROMPT = """You are Zomato's AI Food Concierge, an expert restaurant recommender.
Your task is to analyze candidate restaurants retrieved from the Zomato database and generate personalized, highly relevant recommendations.

Rules:
1. Strict Budget Compliance: Every recommended restaurant MUST have cost_for_two <= the user's maximum budget.
2. Strict Preference & Vibe Matching: When the user specifies food, dish, cuisine, or vibe preferences, ONLY recommend candidates that genuinely match those preferences and explicitly highlight how they match in the rationale.
3. Personalized Justification: For each restaurant, provide a crisp 2-sentence rationale explaining why it is an ideal match for the user's budget, location, and dish/vibe preference.
4. Must-Try Dishes: Name 2-3 specific dishes served by that restaurant that align with the user's dish/cuisine preferences and the restaurant's cuisine profile.
5. Budget Verdict: State clearly how it fits the budget (e.g. 'Rs. 200 under your budget' or 'Fits your Rs. 800 budget').
6. Output Format: You MUST return strictly valid JSON matching the specified schema. Do not include markdown code fences or conversational preamble."""


def build_recommendation_prompt(
    query: UserQuery,
    candidates: List[CandidateRestaurant],
) -> str:
    """Constructs the user prompt injecting candidate restaurant context and user constraints."""
    candidate_lines = []
    for idx, c in enumerate(candidates, 1):
        line = [
            f"Candidate #{idx}:",
            f"  - Name: {c.restaurant_name}",
            f"  - Locality: {c.location}, {c.city}",
            f"  - Cost for Two: Rs. {c.cost_for_two} (Budget Savings: Rs. {c.budget_savings})",
            f"  - Rating: {c.rating}/5.0 (from {c.votes} customer reviews)",
            f"  - Cuisines: {c.cuisines}",
            f"  - Dining Type: {c.rest_type}",
            f"  - Popular Dishes: {c.dish_liked or 'House specials'}",
            f"  - Online Delivery: {c.online_order} | Table Booking: {c.book_table}",
        ]
        candidate_lines.append("\n".join(line))

    candidates_block = "\n\n".join(candidate_lines)

    pref_line = f"User Specific Preferences: {query.preferences}" if query.preferences else "No specific food preferences stated."

    prompt = f"""User Request:
- Target Locality: {query.city}
- Maximum Budget for Two: Rs. {int(query.max_budget)}
- {pref_line}

Verified Candidates from Zomato Database:
{candidates_block}

Task:
Select the best {len(candidates)} recommendations from the candidates above and return a valid JSON object matching this schema:
{{
  "overall_ai_summary": "A 1-2 sentence overall summary of the dining options found for the user in this city and budget.",
  "recommendations": [
    {{
      "restaurant_name": "Exact Name",
      "location": "Locality",
      "cost_for_two": 600,
      "rating": 4.4,
      "cuisines": "Cuisines",
      "ai_rationale": "2-sentence justification for the recommendation.",
      "must_try_dishes": ["Dish 1", "Dish 2"],
      "budget_verdict": "Rs. X under your budget",
      "online_order": "Yes/No",
      "book_table": "Yes/No"
    }}
  ]
}}"""
    return prompt

