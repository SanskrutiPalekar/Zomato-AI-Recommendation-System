"""
Configuration settings for Phase 1 - Zomato Data Ingestion & Preprocessing.
"""

from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

RAW_CSV_FILENAME = "zomato.csv"
CLEANED_CSV_FILENAME = "zomato_cleaned.csv"
METADATA_DB_FILENAME = "zomato_metadata.db"

# Hugging Face Dataset Details
HUGGINGFACE_DATASET_ID = "ManikaSaini/zomato-restaurant-recommendation"
HUGGINGFACE_RAW_CSV_URL = (
    "https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation/resolve/main/zomato.csv"
)

# Raw Column Mapping to Standardized Column Names
COLUMN_MAPPING = {
    # Standard Zomato / Bangalore HF Dataset columns
    "name": "restaurant_name",
    "rate": "rating",
    "votes": "votes",
    "approx_cost(for two people)": "cost_for_two",
    "location": "location",
    "listed_in(city)": "city",
    "cuisines": "cuisines",
    "rest_type": "rest_type",
    "dish_liked": "dish_liked",
    "online_order": "online_order",
    "book_table": "book_table",
    "address": "address",
    "url": "url",
    "listed_in(type)": "service_type",
    # Zomato Mumbai Dataset (pipe-delimited) columns
    "NAME": "restaurant_name",
    "PRICE": "cost_for_two",
    "CUSINE_CATEGORY": "cuisines",
    "CITY": "city",
    "REGION": "location",
    "URL": "url",
    "CUSINE TYPE": "rest_type",
    "RATING": "rating",
    "VOTES": "votes",
}

# Required columns for downstream recommendation tasks
REQUIRED_COLUMNS = [
    "restaurant_name",
    "rating",
    "votes",
    "cost_for_two",
    "location",
    "city",
    "cuisines",
]

