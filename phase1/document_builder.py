"""
Document builder for restaurant profiles.
Transforms tabular restaurant records into rich semantic documents with metadata.
"""

from typing import Any, Dict, List
import pandas as pd


class RestaurantDocument:
    """Represents a restaurant profile document with text content and metadata."""

    def __init__(self, restaurant_id: int, text: str, metadata: Dict[str, Any]):
        self.restaurant_id = restaurant_id
        self.text = text
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        return {
            "restaurant_id": self.restaurant_id,
            "text": self.text,
            "metadata": self.metadata,
        }

    def __repr__(self) -> str:
        return f"<RestaurantDocument id={self.restaurant_id} name='{self.metadata.get('restaurant_name')}'>"


class RestaurantDocumentBuilder:
    """Builds semantic documents from cleaned Zomato restaurant data."""

    @staticmethod
    def build_text_profile(row: pd.Series) -> str:
        """
        Synthesizes a cohesive, natural language profile for a restaurant record.
        """
        name = row.get("restaurant_name", "Unknown Restaurant")
        loc = row.get("location", "Unknown Location")
        city = row.get("city", loc)
        cuisines = row.get("cuisines", "Multi-Cuisine")
        rest_type = row.get("rest_type", "Casual Dining")
        cost = row.get("cost_for_two", "N/A")
        rating = row.get("rating", "N/A")
        votes = row.get("votes", 0)
        dishes = row.get("dish_liked", "")
        online = row.get("online_order", "No")
        booking = row.get("book_table", "No")

        profile_lines = [
            f"Restaurant: {name}",
            f"Location: {loc}, {city}",
            f"Type: {rest_type}",
            f"Cuisines: {cuisines}",
            f"Cost for Two: Rs. {cost}",
            f"Rating: {rating}/5 (based on {votes} customer reviews)",
        ]

        if dishes:
            profile_lines.append(f"Popular Dishes / Liked By Customers: {dishes}")

        services = []
        if online == "Yes":
            services.append("Online Ordering Available")
        if booking == "Yes":
            services.append("Table Booking Available")
        if services:
            profile_lines.append(f"Services: {', '.join(services)}")

        return "\n".join(profile_lines)

    @staticmethod
    def extract_metadata(row: pd.Series) -> Dict[str, Any]:
        """
        Extracts key metadata fields for filtering and scoring.
        """
        return {
            "restaurant_id": int(row.get("restaurant_id", 0)),
            "restaurant_name": str(row.get("restaurant_name", "")),
            "city": str(row.get("city", "")).strip().lower(),
            "location": str(row.get("location", "")).strip().lower(),
            "cost_for_two": int(row.get("cost_for_two", 0)),
            "rating": float(row.get("rating", 0.0)),
            "votes": int(row.get("votes", 0)),
            "cuisines": str(row.get("cuisines", "")),
            "rest_type": str(row.get("rest_type", "")),
            "online_order": str(row.get("online_order", "No")),
            "book_table": str(row.get("book_table", "No")),
        }

    def build_documents(self, df: pd.DataFrame) -> List[RestaurantDocument]:
        """
        Generates a list of RestaurantDocument instances from a cleaned DataFrame.
        """
        documents: List[RestaurantDocument] = []
        for _, row in df.iterrows():
            text = self.build_text_profile(row)
            metadata = self.extract_metadata(row)
            restaurant_id = metadata["restaurant_id"]
            documents.append(RestaurantDocument(restaurant_id, text, metadata))

        return documents
