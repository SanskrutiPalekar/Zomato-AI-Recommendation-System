"""
Budget parser for user price input.
Converts diverse natural language, currency, and range expressions into structured PricePreference models.
"""

import re
from typing import Optional, Tuple, Union

from phase2.config import BUDGET_TIERS, DEFAULT_BUDGET_TOLERANCE_PCT
from phase2.models import PricePreference


class BudgetParser:
    """Parses and standardizes user budget/price inputs for dining recommendations."""

    def __init__(self, tolerance_pct: float = DEFAULT_BUDGET_TOLERANCE_PCT):
        self.tolerance_pct = tolerance_pct

    def parse(self, budget_input: Union[str, int, float]) -> PricePreference:
        """
        Parses raw budget input into a validated PricePreference.

        Args:
            budget_input: User input (e.g., 800, 'under 1000', '500-1200', 'fine dining').

        Returns:
            PricePreference object with min_price, max_price, and metadata.

        Raises:
            ValueError: If the input cannot be resolved to a positive budget.
        """
        if budget_input is None:
            raise ValueError("Budget input cannot be None or empty.")

        raw_str = str(budget_input).strip()
        if not raw_str:
            raise ValueError("Budget input cannot be empty.")

        cleaned = raw_str.lower()

        # Reject negative numbers explicitly
        if re.search(r"-\s*\d+", cleaned) and not re.search(r"\d+\s*-\s*\d+", cleaned):
            raise ValueError(f"Budget cannot be negative: '{raw_str}'.")

        # 1. Check keyword / budget tier presets with word boundary (e.g., 'budget', 'fine dining')
        for tier_name, tier_values in BUDGET_TIERS.items():
            pattern = rf"\b{re.escape(tier_name)}\b"
            if re.search(pattern, cleaned):
                # Ensure it is not negated (e.g. 'not a budget', 'not-a-budget')
                if re.search(rf"\b(?:not|no|non|never)\b.*?\b{re.escape(tier_name)}\b", cleaned.replace("-", " ")):
                    continue
                return PricePreference(
                    raw_input=raw_str,
                    min_price=tier_values["min_price"],
                    max_price=tier_values["max_price"],
                    flex_tolerance_pct=self.tolerance_pct,
                )

        # Remove currency symbols, commas, and suffixes
        normalized = cleaned.replace("₹", " ").replace("rs.", " ").replace("rs", " ")
        normalized = normalized.replace("inr", " ").replace("/-", " ").replace(",", "")
        normalized = re.sub(r"\s+", " ", normalized).strip()

        # 2. Check for range expressions (e.g., '500-1000', '500 to 1000', 'between 500 and 1000')
        range_match = re.search(
            r"(?:between\s+)?(\d+(?:\.\d+)?)\s*(?:-|to|and)\s*(\d+(?:\.\d+)?)",
            normalized,
        )
        if range_match:
            val1 = float(range_match.group(1))
            val2 = float(range_match.group(2))
            min_val, max_val = min(val1, val2), max(val1, val2)
            if max_val <= 0:
                raise ValueError("Budget must be greater than zero.")
            return PricePreference(
                raw_input=raw_str,
                min_price=min_val,
                max_price=max_val,
                flex_tolerance_pct=self.tolerance_pct,
            )

        # 3. Check for approximate phrases (e.g., 'around 1000', 'approx 800', 'about 1200')
        approx_match = re.search(
            r"(?:around|approx|approximately|about|~)\s*(\d+(?:\.\d+)?)",
            normalized,
        )
        if approx_match:
            center_val = float(approx_match.group(1))
            if center_val <= 0:
                raise ValueError("Budget must be greater than zero.")
            min_val = max(0.0, round(center_val * 0.85, 2))
            max_val = round(center_val * 1.15, 2)
            return PricePreference(
                raw_input=raw_str,
                min_price=min_val,
                max_price=max_val,
                flex_tolerance_pct=self.tolerance_pct,
            )

        # 4. Check for upper-bound phrases (e.g., 'under 800', 'below 1000', 'max 600', 'upto 750')
        upper_match = re.search(
            r"(?:under|below|less than|max|maximum|upto|up to|within)\s*(\d+(?:\.\d+)?)",
            normalized,
        )
        if upper_match:
            max_val = float(upper_match.group(1))
            if max_val <= 0:
                raise ValueError("Budget must be greater than zero.")
            return PricePreference(
                raw_input=raw_str,
                min_price=0.0,
                max_price=max_val,
                flex_tolerance_pct=self.tolerance_pct,
            )

        # 5. Check for lower-bound phrases (e.g., 'above 500', 'more than 1000', 'min 800')
        lower_match = re.search(
            r"(?:above|more than|over|min|minimum|at least)\s*(\d+(?:\.\d+)?)",
            normalized,
        )
        if lower_match:
            min_val = float(lower_match.group(1))
            if min_val <= 0:
                raise ValueError("Budget must be greater than zero.")
            # Set a generous upper bound for open-ended queries
            return PricePreference(
                raw_input=raw_str,
                min_price=min_val,
                max_price=min_val * 2.5,
                flex_tolerance_pct=self.tolerance_pct,
            )

        # 6. Extract standalone single numeric value (e.g., '800', '1200.00')
        single_num_match = re.search(r"(\d+(?:\.\d+)?)", normalized)
        if single_num_match:
            val = float(single_num_match.group(1))
            if val <= 0:
                raise ValueError("Budget must be greater than zero.")
            return PricePreference(
                raw_input=raw_str,
                min_price=0.0,
                max_price=val,
                flex_tolerance_pct=self.tolerance_pct,
            )

        raise ValueError(
            f"Unable to understand budget '{raw_str}'. "
            "Please provide an amount like 800, 'under 1000', '500-1200', or a tier like 'budget' or 'fine dining'."
        )
