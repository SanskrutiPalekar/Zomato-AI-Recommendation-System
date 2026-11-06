"""
Test fixtures and mock datasets for Phase 1 tests.
"""

import pandas as pd
import pytest


@pytest.fixture
def sample_raw_zomato_data() -> pd.DataFrame:
    """
    Returns a sample DataFrame mirroring the schema and quirks of the raw Hugging Face
    'ManikaSaini/zomato-restaurant-recommendation' dataset.
    """
    data = [
        {
            "url": "https://zomato.com/bangalore/jalsa-banashankari",
            "address": "942, 21st Main Road, Banashankari, Bangalore",
            "name": "Jalsa",
            "online_order": "Yes",
            "book_table": "Yes",
            "rate": "4.1/5",
            "votes": 775,
            "phone": "080 42297555",
            "location": "Banashankari",
            "rest_type": "Casual Dining",
            "dish_liked": "Pasta, Lunch Buffet, Masala Papad",
            "cuisines": "North Indian, Mughlai, Chinese",
            "approx_cost(for two people)": "800",
            "reviews_list": "[('Rated 4.0', 'RATED\\n  A beautiful place to dine in.')]",
            "menu_item": "[]",
            "listed_in(type)": "Buffet",
            "listed_in(city)": "Banashankari",
        },
        {
            "url": "https://zomato.com/bangalore/spice-elephant-banashankari",
            "address": "2nd Floor, 80 Feet Road, Banashankari, Bangalore",
            "name": "Spice Elephant",
            "online_order": "Yes",
            "book_table": "No",
            "rate": "4.1/5",
            "votes": 787,
            "phone": "080 41714161",
            "location": "Banashankari",
            "rest_type": "Casual Dining",
            "dish_liked": "Momos, Lunch Buffet, Chocolate Mousse",
            "cuisines": "Chinese, North Indian, Thai",
            "approx_cost(for two people)": "1,200",
            "reviews_list": "[('Rated 4.0', 'RATED\\n  Nice ambience.')]",
            "menu_item": "[]",
            "listed_in(type)": "Buffet",
            "listed_in(city)": "Banashankari",
        },
        {
            "url": "https://zomato.com/bangalore/empire-koramangala",
            "address": "80 Feet Road, 5th Block, Koramangala, Bangalore",
            "name": "Empire Restaurant",
            "online_order": "Yes",
            "book_table": "No",
            "rate": "4.3 /5",
            "votes": 2500,
            "phone": "080 40404040",
            "location": "Koramangala",
            "rest_type": "Casual Dining",
            "dish_liked": "Ghee Rice, Chicken Kebab, Coin Parotta",
            "cuisines": "North Indian, Biryani, Mughlai",
            "approx_cost(for two people)": "750",
            "reviews_list": "[('Rated 4.5', 'RATED\\n  Legendary midnight spot.')]",
            "menu_item": "[]",
            "listed_in(type)": "Dine-out",
            "listed_in(city)": "Koramangala",
        },
        {
            # New restaurant without rating yet
            "url": "https://zomato.com/bangalore/the-new-cafe",
            "address": "12th Main, Indiranagar, Bangalore",
            "name": "The New Cafe",
            "online_order": "No",
            "book_table": "No",
            "rate": "NEW",
            "votes": 0,
            "phone": "080 12345678",
            "location": "Indiranagar",
            "rest_type": "Cafe",
            "dish_liked": "",
            "cuisines": "Cafe, Beverages",
            "approx_cost(for two people)": "500",
            "reviews_list": "[]",
            "menu_item": "[]",
            "listed_in(type)": "Cafes",
            "listed_in(city)": "Indiranagar",
        },
        {
            # Invalid entry missing cost
            "url": "https://zomato.com/bangalore/missing-cost",
            "address": "Koramangala, Bangalore",
            "name": "Missing Cost Diner",
            "online_order": "No",
            "book_table": "No",
            "rate": "3.5/5",
            "votes": 10,
            "phone": "",
            "location": "Koramangala",
            "rest_type": "Quick Bites",
            "dish_liked": "",
            "cuisines": "Fast Food",
            "approx_cost(for two people)": None,
            "reviews_list": "[]",
            "menu_item": "[]",
            "listed_in(type)": "Dine-out",
            "listed_in(city)": "Koramangala",
        },
        {
            # Duplicate entry of Empire Restaurant
            "url": "https://zomato.com/bangalore/empire-koramangala-dup",
            "address": "80 Feet Road, 5th Block, Koramangala, Bangalore",
            "name": "Empire Restaurant",
            "online_order": "Yes",
            "book_table": "No",
            "rate": "4.3 /5",
            "votes": 2500,
            "phone": "080 40404040",
            "location": "Koramangala",
            "rest_type": "Casual Dining",
            "dish_liked": "Ghee Rice, Chicken Kebab, Coin Parotta",
            "cuisines": "North Indian, Biryani, Mughlai",
            "approx_cost(for two people)": "750",
            "reviews_list": "[('Rated 4.5', 'RATED\\n  Legendary midnight spot.')]",
            "menu_item": "[]",
            "listed_in(type)": "Delivery",
            "listed_in(city)": "Koramangala",
        },
    ]
    return pd.DataFrame(data)

