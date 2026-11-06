"""
Metadata Store for Phase 1.
Provides fast structured filtering by City and Price (approx cost for two),
backed by SQLite or Pandas for low-latency candidate retrieval in Step 3.
"""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd


class MetadataStore:
    """Manages structured restaurant metadata and provides fast filtering by City and Price."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = str(db_path) if db_path else ":memory:"
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        """Initializes the database schema with appropriate indexes."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS restaurants (
                restaurant_id INTEGER PRIMARY KEY,
                restaurant_name TEXT NOT NULL,
                city TEXT NOT NULL,
                location TEXT NOT NULL,
                cost_for_two INTEGER NOT NULL,
                rating REAL NOT NULL,
                votes INTEGER NOT NULL,
                cuisines TEXT,
                rest_type TEXT,
                dish_liked TEXT,
                online_order TEXT,
                book_table TEXT
            )
            """
        )
        # Create indexes for fast lookup on Step 2 criteria: City and Price
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_city ON restaurants(city)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_location ON restaurants(location)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cost ON restaurants(cost_for_two)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_city_cost ON restaurants(city, cost_for_two)")
        self.conn.commit()

    def index_dataframe(self, df: pd.DataFrame) -> int:
        """
        Populates the metadata database from a cleaned DataFrame.
        Returns the number of indexed records.
        """
        cols_to_insert = [
            "restaurant_id",
            "restaurant_name",
            "city",
            "location",
            "cost_for_two",
            "rating",
            "votes",
            "cuisines",
            "rest_type",
            "dish_liked",
            "online_order",
            "book_table",
        ]

        # Ensure all columns exist
        insert_df = df.copy()
        for col in cols_to_insert:
            if col not in insert_df.columns:
                insert_df[col] = None

        insert_df = insert_df[cols_to_insert]

        # Insert into SQLite
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM restaurants")  # Clear prior data
        insert_df.to_sql("restaurants", self.conn, if_exists="append", index=False)
        self.conn.commit()

        cursor.execute("SELECT COUNT(*) FROM restaurants")
        count = cursor.fetchone()[0]
        return count

    def query_by_city_and_price(
        self,
        city: str,
        max_price: float,
        min_price: float = 0.0,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Filters restaurants matching city/location and within budget range.
        Case-insensitive and matches either city or local area name.
        """
        city_clean = city.strip().lower()
        query = """
            SELECT * FROM restaurants
            WHERE (LOWER(city) LIKE ? OR LOWER(location) LIKE ?)
              AND cost_for_two <= ?
              AND cost_for_two >= ?
            ORDER BY rating DESC, votes DESC
            LIMIT ?
        """
        cursor = self.conn.cursor()
        pattern = f"%{city_clean}%"
        cursor.execute(query, (pattern, pattern, max_price, min_price, limit))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_restaurant_by_id(self, restaurant_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves single restaurant record by its ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM restaurants WHERE restaurant_id = ?", (restaurant_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_distinct_cities(self) -> List[str]:
        """Returns sorted list of distinct cities."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT city FROM restaurants WHERE city IS NOT NULL ORDER BY city")
        return [row[0] for row in cursor.fetchall()]

    def get_distinct_locations(self) -> List[str]:
        """Returns sorted list of distinct neighborhood locations."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT DISTINCT location FROM restaurants WHERE location IS NOT NULL ORDER BY location"
        )
        return [row[0] for row in cursor.fetchall()]

    def count(self) -> int:
        """Returns total number of stored records."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM restaurants")
        return cursor.fetchone()[0]

    def close(self):
        """Closes the underlying database connection."""
        self.conn.close()

