"""
Unit and integration tests for Phase 1 / Step 1: Input the Zomato User Data.
"""

from pathlib import Path
import pandas as pd
import pytest

from phase1.data_cleaner import ZomatoDataCleaner
from phase1.data_loader import ZomatoDataLoader
from phase1.document_builder import RestaurantDocumentBuilder
from phase1.metadata_store import MetadataStore
from phase1.pipeline import Phase1Pipeline


# ============================================================================
# 1. ZomatoDataCleaner Unit Tests
# ============================================================================

class TestZomatoDataCleaner:
    def test_parse_rating_standard(self):
        cleaner = ZomatoDataCleaner()
        assert cleaner.parse_rating("4.1/5") == 4.1
        assert cleaner.parse_rating("3.9 /5") == 3.9
        assert cleaner.parse_rating("5.0/5") == 5.0
        assert cleaner.parse_rating("2.8") == 2.8

    def test_parse_rating_edge_cases(self):
        cleaner = ZomatoDataCleaner()
        assert cleaner.parse_rating("NEW") is None
        assert cleaner.parse_rating("-") is None
        assert cleaner.parse_rating("") is None
        assert cleaner.parse_rating(None) is None
        assert cleaner.parse_rating("invalid") is None
        assert cleaner.parse_rating("6.5/5") is None  # Out of range

    def test_parse_cost_standard(self):
        cleaner = ZomatoDataCleaner()
        assert cleaner.parse_cost("800") == 800
        assert cleaner.parse_cost("1,200") == 1200
        assert cleaner.parse_cost("2,500") == 2500
        assert cleaner.parse_cost(450) == 450

    def test_parse_cost_edge_cases(self):
        cleaner = ZomatoDataCleaner()
        assert cleaner.parse_cost(None) is None
        assert cleaner.parse_cost("") is None
        assert cleaner.parse_cost("FREE") is None
        assert cleaner.parse_cost(0) is None

    def test_parse_votes(self):
        cleaner = ZomatoDataCleaner()
        assert cleaner.parse_votes(775) == 775
        assert cleaner.parse_votes("120") == 120
        assert cleaner.parse_votes(None) == 0
        assert cleaner.parse_votes("invalid") == 0
        assert cleaner.parse_votes(-10) == 0

    def test_parse_cuisines(self):
        cleaner = ZomatoDataCleaner()
        assert cleaner.parse_cuisines("North Indian, Mughlai, Chinese") == [
            "North Indian",
            "Mughlai",
            "Chinese",
        ]
        assert cleaner.parse_cuisines("Cafe") == ["Cafe"]
        assert cleaner.parse_cuisines(None) == []
        assert cleaner.parse_cuisines("") == []

    def test_clean_dataframe_pipeline(self, sample_raw_zomato_data):
        cleaner = ZomatoDataCleaner(default_rating_impute=True)
        cleaned = cleaner.clean_dataframe(sample_raw_zomato_data)

        # 1. Row missing cost should have been dropped
        assert not any(cleaned["restaurant_name"] == "Missing Cost Diner")

        # 2. Duplicate Empire Restaurant should be deduplicated
        empire_rows = cleaned[cleaned["restaurant_name"] == "Empire Restaurant"]
        assert len(empire_rows) == 1

        # 3. New Cafe's missing rating should be imputed
        new_cafe = cleaned[cleaned["restaurant_name"] == "The New Cafe"].iloc[0]
        assert new_cafe["rating"] > 0
        assert new_cafe["cost_for_two"] == 500

        # 4. Standardized columns check
        for col in ["restaurant_id", "restaurant_name", "rating", "cost_for_two", "city", "location"]:
            assert col in cleaned.columns

        # 5. Restaurant IDs should be sequential integers
        assert list(cleaned["restaurant_id"]) == list(range(len(cleaned)))


# ============================================================================
# 2. ZomatoDataLoader Unit Tests
# ============================================================================

class TestZomatoDataLoader:
    def test_load_from_csv_success(self, tmp_path, sample_raw_zomato_data):
        csv_file = tmp_path / "test_zomato.csv"
        sample_raw_zomato_data.to_csv(csv_file, index=False)

        loader = ZomatoDataLoader(raw_data_dir=tmp_path)
        df = loader.load_from_csv(file_path=csv_file)

        assert len(df) == len(sample_raw_zomato_data)
        assert "name" in df.columns

    def test_load_from_csv_with_nrows(self, tmp_path, sample_raw_zomato_data):
        csv_file = tmp_path / "test_zomato.csv"
        sample_raw_zomato_data.to_csv(csv_file, index=False)

        loader = ZomatoDataLoader(raw_data_dir=tmp_path)
        df = loader.load_from_csv(file_path=csv_file, nrows=2)

        assert len(df) == 2

    def test_load_from_csv_not_found(self, tmp_path):
        loader = ZomatoDataLoader(raw_data_dir=tmp_path)
        non_existent = tmp_path / "missing.csv"
        with pytest.raises(FileNotFoundError):
            loader.load_from_csv(file_path=non_existent)


# ============================================================================
# 3. RestaurantDocumentBuilder Unit Tests
# ============================================================================

class TestRestaurantDocumentBuilder:
    def test_build_documents(self, sample_raw_zomato_data):
        cleaner = ZomatoDataCleaner()
        cleaned = cleaner.clean_dataframe(sample_raw_zomato_data)

        builder = RestaurantDocumentBuilder()
        docs = builder.build_documents(cleaned)

        assert len(docs) == len(cleaned)

        first_doc = docs[0]
        assert first_doc.restaurant_id == 0
        # Text contains restaurant profile attributes
        assert "Restaurant: Jalsa" in first_doc.text
        assert "Cost for Two: Rs. 800" in first_doc.text
        assert "Banashankari" in first_doc.text

        # Metadata contains structured fields
        assert first_doc.metadata["restaurant_name"] == "Jalsa"
        assert first_doc.metadata["cost_for_two"] == 800
        assert first_doc.metadata["rating"] == 4.1
        assert first_doc.metadata["city"] == "banashankari"


# ============================================================================
# 4. MetadataStore Unit Tests
# ============================================================================

class TestMetadataStore:
    def test_indexing_and_filtering(self, sample_raw_zomato_data):
        cleaner = ZomatoDataCleaner()
        cleaned = cleaner.clean_dataframe(sample_raw_zomato_data)

        store = MetadataStore()
        count = store.index_dataframe(cleaned)
        assert count == len(cleaned)
        assert store.count() == len(cleaned)

        # Filter: City 'Banashankari' with max price 1000
        # Expected: Jalsa (800) fits; Spice Elephant (1200) exceeds budget
        results = store.query_by_city_and_price(city="Banashankari", max_price=1000)
        assert len(results) == 1
        assert results[0]["restaurant_name"] == "Jalsa"
        assert results[0]["cost_for_two"] == 800

        # Filter: City 'Banashankari' with max price 1500
        # Expected: Both Jalsa (800) and Spice Elephant (1200) fit
        results_higher = store.query_by_city_and_price(city="Banashankari", max_price=1500)
        assert len(results_higher) == 2

    def test_case_insensitive_matching(self, sample_raw_zomato_data):
        cleaner = ZomatoDataCleaner()
        cleaned = cleaner.clean_dataframe(sample_raw_zomato_data)

        store = MetadataStore()
        store.index_dataframe(cleaned)

        # Lowercase search
        results_lower = store.query_by_city_and_price(city="koramangala", max_price=1000)
        assert len(results_lower) >= 1
        assert results_lower[0]["restaurant_name"] == "Empire Restaurant"

    def test_distinct_cities_and_locations(self, sample_raw_zomato_data):
        cleaner = ZomatoDataCleaner()
        cleaned = cleaner.clean_dataframe(sample_raw_zomato_data)

        store = MetadataStore()
        store.index_dataframe(cleaned)

        cities = store.get_distinct_cities()
        locations = store.get_distinct_locations()

        assert "Banashankari" in cities
        assert "Koramangala" in cities
        assert "Banashankari" in locations

    def test_get_by_id(self, sample_raw_zomato_data):
        cleaner = ZomatoDataCleaner()
        cleaned = cleaner.clean_dataframe(sample_raw_zomato_data)

        store = MetadataStore()
        store.index_dataframe(cleaned)

        record = store.get_restaurant_by_id(0)
        assert record is not None
        assert record["restaurant_name"] == cleaned.iloc[0]["restaurant_name"]

        non_existent = store.get_restaurant_by_id(9999)
        assert non_existent is None


# ============================================================================
# 5. End-to-End Phase 1 Pipeline Integration Tests
# ============================================================================

class TestPhase1Pipeline:
    def test_pipeline_run_with_raw_df(self, sample_raw_zomato_data, tmp_path):
        pipeline = Phase1Pipeline()
        result = pipeline.run(
            raw_df=sample_raw_zomato_data,
            save_processed=True,
            processed_dir=tmp_path,
        )

        # Check Result Objects
        assert not result.cleaned_df.empty
        assert len(result.documents) == len(result.cleaned_df)
        assert result.metadata_store.count() == len(result.cleaned_df)

        # Check Processed CSV file was saved
        saved_csv = tmp_path / "zomato_cleaned.csv"
        assert saved_csv.exists()
        saved_df = pd.read_csv(saved_csv)
        assert len(saved_df) == len(result.cleaned_df)

        # Check Stats
        stats = result.stats
        assert stats["raw_records_count"] == len(sample_raw_zomato_data)
        assert stats["cleaned_records_count"] == len(result.cleaned_df)
        assert stats["documents_generated"] == len(result.documents)
        assert stats["distinct_cities"] >= 2
        assert stats["min_cost"] > 0
        assert stats["max_cost"] >= stats["min_cost"]

        # Validate that the resulting metadata store is queryable for Step 2/3
        recs = result.metadata_store.query_by_city_and_price(city="Koramangala", max_price=900)
        assert len(recs) == 1
        assert recs[0]["restaurant_name"] == "Empire Restaurant"
