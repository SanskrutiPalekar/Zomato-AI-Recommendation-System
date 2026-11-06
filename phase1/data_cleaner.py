"""
Data cleaner and preprocessor for the Zomato Restaurant Recommendation dataset.
Standardizes fields, parses ratings and costs, and removes invalid/duplicate records.
"""

import re
from typing import Any, List, Optional
import numpy as np
import pandas as pd

from phase1.config import COLUMN_MAPPING, REQUIRED_COLUMNS


class ZomatoDataCleaner:
    """Cleans, parses, and standardizes raw Zomato restaurant data."""

    def __init__(self, default_rating_impute: bool = True):
        self.default_rating_impute = default_rating_impute

    @staticmethod
    def parse_rating(val: Any) -> Optional[float]:
        """
        Parses rating string (e.g., '4.1/5', '3.9 /5', 'NEW', '-') into float.
        Returns None for non-numeric or unrated entries.
        """
        if pd.isna(val) or val is None:
            return None

        val_str = str(val).strip()

        # Handle explicit unrated states
        if val_str in ("NEW", "-", "", "nan", "None"):
            return None

        # Extract numeric rating (e.g., '4.1' from '4.1/5')
        match = re.search(r"([0-9]+(?:\.[0-9]+)?)", val_str)
        if match:
            try:
                rating = float(match.group(1))
                if 0.0 <= rating <= 5.0:
                    return rating
            except ValueError:
                return None
        return None

    @staticmethod
    def parse_cost(val: Any) -> Optional[int]:
        """
        Parses cost for two string (e.g., '1,200', '800') into an integer.
        Returns None for invalid or missing values.
        """
        if pd.isna(val) or val is None:
            return None

        val_str = str(val).strip().replace(",", "")

        match = re.search(r"(\d+)", val_str)
        if match:
            try:
                cost = int(match.group(1))
                if cost > 0:
                    return cost
            except ValueError:
                return None
        return None

    @staticmethod
    def parse_votes(val: Any) -> int:
        """
        Parses votes count into an integer. Defaults to 0 if missing/invalid.
        """
        if pd.isna(val) or val is None:
            return 0
        try:
            return max(0, int(val))
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def clean_string(val: Any, default: str = "") -> str:
        """
        Strips whitespace and handles missing string fields.
        """
        if pd.isna(val) or val is None:
            return default
        cleaned = str(val).strip()
        return cleaned if cleaned else default

    @staticmethod
    def parse_cuisines(val: Any) -> List[str]:
        """
        Parses comma-separated or multi-space-separated cuisines into a clean list of strings.
        """
        if pd.isna(val) or val is None:
            return []
        val_str = str(val).strip()
        if "," in val_str:
            items = val_str.split(",")
        else:
            items = re.split(r"\s{2,}", val_str)
        return [item.strip() for item in items if item.strip()]

    def clean_dataframe(
        self,
        df: pd.DataFrame,
        drop_missing_essentials: bool = True,
    ) -> pd.DataFrame:
        """
        Performs end-to-end cleaning and standardization on the raw DataFrame.

        Args:
            df: Raw DataFrame loaded from CSV.
            drop_missing_essentials: Whether to drop rows missing restaurant name,
                                     location/city, or cost.

        Returns:
            Cleaned and normalized DataFrame.
        """
        data = df.copy()

        # 1. Rename columns if raw column names match mapping
        data = data.rename(columns=COLUMN_MAPPING)

        # Ensure all required target columns exist
        for col in REQUIRED_COLUMNS:
            if col not in data.columns:
                data[col] = np.nan

        # 2. Clean numeric attributes
        data["rating"] = data["rating"].apply(self.parse_rating)
        data["cost_for_two"] = data["cost_for_two"].apply(self.parse_cost)
        data["votes"] = data["votes"].apply(self.parse_votes)

        # 3. Clean textual attributes
        data["restaurant_name"] = data["restaurant_name"].apply(
            lambda v: self.clean_string(v, default="Unknown Restaurant")
        )
        data["location"] = data["location"].apply(
            lambda v: self.clean_string(v, default="Unknown Location")
        )
        # If 'listed_in(city)' was the source (Bangalore HF dataset), prefer granular 'location'
        # Otherwise if 'CITY' was explicitly provided (e.g. Mumbai dataset), preserve 'city'
        has_explicit_city = "CITY" in df.columns or (
            "city" in df.columns and "listed_in(city)" not in df.columns
        )
        if "location" in data.columns and not has_explicit_city:
            data["city"] = data["location"].apply(
                lambda v: self.clean_string(v, default=None)
            )
        else:
            data["city"] = data["city"].apply(
                lambda v: self.clean_string(v, default=None)
            )
        # Final fallback: use location if city is missing
        if "city" in data.columns:
            data["city"] = data["city"].fillna(data.get("location", pd.Series(dtype=str)))
        # Clean region prefixes like 'First International Financial Centre-- Bandra Kurla Complex'
        data["location"] = data["location"].apply(
            lambda v: str(v).split("--")[-1].strip() if "--" in str(v) else str(v).strip()
        )

        # Clean cuisines list and string representations
        data["cuisines_list"] = data["cuisines"].apply(self.parse_cuisines)
        data["cuisines"] = data["cuisines_list"].apply(
            lambda items: ", ".join(items) if items else "Various"
        )

        if "rest_type" in data.columns:
            data["rest_type"] = data["rest_type"].apply(
                lambda v: self.clean_string(v, default="Casual Dining")
            )

        if "dish_liked" in data.columns:
            data["dish_liked"] = data["dish_liked"].apply(
                lambda v: self.clean_string(v, default="")
            )

        if "online_order" in data.columns:
            data["online_order"] = data["online_order"].apply(
                lambda v: "Yes" if str(v).strip().lower() in ("yes", "true", "1") else "No"
            )

        if "book_table" in data.columns:
            data["book_table"] = data["book_table"].apply(
                lambda v: "Yes" if str(v).strip().lower() in ("yes", "true", "1") else "No"
            )

        # 4. Handle missing essentials
        if drop_missing_essentials:
            # Must have name, location, and cost_for_two
            valid_mask = (
                (data["restaurant_name"] != "Unknown Restaurant")
                & (data["location"] != "Unknown Location")
                & (data["cost_for_two"].notna())
            )
            data = data[valid_mask].copy()

        # 5. Optional rating imputation (fill missing rating with median rating)
        if self.default_rating_impute:
            median_rating = data["rating"].median()
            if pd.isna(median_rating):
                median_rating = 3.5
            data["rating"] = data["rating"].fillna(round(median_rating, 1))

        # 6. Deduplicate entries based on name, location, and address/cost
        subset_cols = ["restaurant_name", "location", "cost_for_two"]
        if "address" in data.columns:
            subset_cols.append("address")
        data = data.drop_duplicates(subset=subset_cols, keep="first").reset_index(drop=True)

        # 7. Add integer ID for referencing across pipeline steps
        data["restaurant_id"] = data.index

        return data

