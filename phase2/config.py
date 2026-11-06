"""
Configuration settings for Phase 2: User Input & Query Processing.
"""

from typing import Dict, List

# Known dataset localities / areas in Bangalore
DEFAULT_KNOWN_LOCALITIES: List[str] = [
    "Banashankari",
    "Basavanagudi",
    "Bellandur",
    "Brigade Road",
    "BTM",
    "Church Street",
    "Commercial Street",
    "Cunningham Road",
    "Domlur",
    "Electronic City",
    "Frazer Town",
    "HSR Layout",
    "Indiranagar",
    "Jayanagar",
    "JP Nagar",
    "Kalyan Nagar",
    "Kammanahalli",
    "Koramangala",
    "Lavelle Road",
    "Malleshwaram",
    "Marathahalli",
    "MG Road",
    "New BEL Road",
    "Old Airport Road",
    "Rajajinagar",
    "Residency Road",
    "Richmond Road",
    "Sarjapur Road",
    "Shanti Nagar",
    "Shivajinagar",
    "Ulsoor",
    "Whitefield",
    "Bangalore",
]

# Common abbreviations and aliases mapped to standard locality names
LOCATION_ALIASES: Dict[str, str] = {
    "blr": "Bangalore",
    "bengaluru": "Bangalore",
    "banglore": "Bangalore",
    "hsr": "HSR Layout",
    "btm": "BTM",
    "jp nagar": "JP Nagar",
    "jpnagar": "JP Nagar",
    "mg road": "MG Road",
    "mgroad": "MG Road",
    "ecity": "Electronic City",
    "electronic city": "Electronic City",
    "koramangala": "Koramangala",
    "kora": "Koramangala",
    "indiranagar": "Indiranagar",
    "indira nagar": "Indiranagar",
}

# Budget Tier presets (INR for two people)
BUDGET_TIERS: Dict[str, Dict[str, float]] = {
    "budget": {"min_price": 0.0, "max_price": 500.0},
    "cheap": {"min_price": 0.0, "max_price": 400.0},
    "pocket friendly": {"min_price": 0.0, "max_price": 600.0},
    "moderate": {"min_price": 500.0, "max_price": 1200.0},
    "mid-range": {"min_price": 500.0, "max_price": 1200.0},
    "expensive": {"min_price": 1200.0, "max_price": 3000.0},
    "fine dining": {"min_price": 1500.0, "max_price": 5000.0},
    "luxury": {"min_price": 2500.0, "max_price": 10000.0},
}

# Fuzzy matching thresholds
MIN_CITY_CONFIDENCE_THRESHOLD = 0.60
EXACT_MATCH_CONFIDENCE = 1.0

# Default tolerance expansion for budget (e.g. 10% tolerance)
DEFAULT_BUDGET_TOLERANCE_PCT = 0.10

