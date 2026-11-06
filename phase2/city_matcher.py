"""
City and locality matcher for user input.
Resolves typos, abbreviations, and informal area names using fuzzy matching.
"""

import difflib
from typing import List, Optional

from phase2.config import (
    DEFAULT_KNOWN_LOCALITIES,
    EXACT_MATCH_CONFIDENCE,
    LOCATION_ALIASES,
    MIN_CITY_CONFIDENCE_THRESHOLD,
)
from phase2.models import CityPreference


class CityMatcher:
    """Resolves and standardizes user city/locality inputs against known dataset areas."""

    def __init__(
        self,
        known_localities: Optional[List[str]] = None,
        confidence_threshold: float = MIN_CITY_CONFIDENCE_THRESHOLD,
    ):
        self.known_localities = known_localities or DEFAULT_KNOWN_LOCALITIES
        self.confidence_threshold = confidence_threshold
        # Lowercase mapping for quick lookup
        self._lower_to_canonical = {loc.lower(): loc for loc in self.known_localities}

    def resolve(self, city_input: str) -> CityPreference:
        """
        Resolves raw city input to a standardized locality name.

        Args:
            city_input: Raw user input (e.g., 'koramangla', 'hsr', 'BLR', 'Indiranagar').

        Returns:
            CityPreference object containing the resolved locality name and confidence.

        Raises:
            ValueError: If input is empty or completely unrecognized.
        """
        if city_input is None:
            raise ValueError("City input cannot be None or empty.")

        raw_str = str(city_input).strip()
        if not raw_str:
            raise ValueError("City input cannot be empty.")

        query_lower = raw_str.lower()

        # 1. Exact match (case-insensitive)
        if query_lower in self._lower_to_canonical:
            return CityPreference(
                raw_input=raw_str,
                resolved_city=self._lower_to_canonical[query_lower],
                confidence_score=EXACT_MATCH_CONFIDENCE,
                is_exact_match=True,
            )

        # 2. Check alias map (e.g., 'hsr' -> 'HSR Layout', 'blr' -> 'Bangalore')
        if query_lower in LOCATION_ALIASES:
            canonical = LOCATION_ALIASES[query_lower]
            return CityPreference(
                raw_input=raw_str,
                resolved_city=canonical,
                confidence_score=EXACT_MATCH_CONFIDENCE,
                is_exact_match=True,
            )

        # 3. Substring match (e.g., 'koramangala 5th block' contains 'koramangala')
        for loc_lower, canonical in self._lower_to_canonical.items():
            if loc_lower in query_lower or query_lower in loc_lower:
                return CityPreference(
                    raw_input=raw_str,
                    resolved_city=canonical,
                    confidence_score=0.90,
                    is_exact_match=False,
                )

        # 4. Fuzzy sequence matching (handles typos like 'koramangla', 'whitefeild')
        best_match: Optional[str] = None
        best_ratio = 0.0

        for loc in self.known_localities:
            ratio = difflib.SequenceMatcher(None, query_lower, loc.lower()).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = loc

        # Fetch closest suggestions
        suggestions = difflib.get_close_matches(
            query_lower,
            [loc.lower() for loc in self.known_localities],
            n=3,
            cutoff=0.40,
        )
        canonical_suggestions = [
            self._lower_to_canonical[s] for s in suggestions if s in self._lower_to_canonical
        ]

        if best_match and best_ratio >= self.confidence_threshold:
            return CityPreference(
                raw_input=raw_str,
                resolved_city=best_match,
                confidence_score=round(best_ratio, 2),
                is_exact_match=False,
                suggestions=canonical_suggestions,
            )

        # Failed to find adequate match
        suggestions_hint = (
            f" Did you mean: {', '.join(canonical_suggestions)}?"
            if canonical_suggestions
            else ""
        )
        raise ValueError(
            f"Could not recognize locality '{raw_str}'.{suggestions_hint} "
            f"Please enter a valid Bangalore neighborhood or city."
        )

