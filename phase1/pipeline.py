"""
Phase 1 Pipeline Orchestrator.
Coordinates dataset loading, cleaning, document building, and metadata indexing.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from phase1.config import (
    CLEANED_CSV_FILENAME,
    PROCESSED_DATA_DIR,
)
from phase1.data_cleaner import ZomatoDataCleaner
from phase1.data_loader import ZomatoDataLoader
from phase1.document_builder import RestaurantDocument, RestaurantDocumentBuilder
from phase1.metadata_store import MetadataStore


@dataclass
class Phase1Result:
    """Encapsulates the output artifacts of Phase 1."""

    cleaned_df: pd.DataFrame
    documents: List[RestaurantDocument]
    metadata_store: MetadataStore
    stats: Dict[str, Any]


class Phase1Pipeline:
    """Executes the complete Phase 1 / Step 1 pipeline."""

    def __init__(
        self,
        loader: Optional[ZomatoDataLoader] = None,
        cleaner: Optional[ZomatoDataCleaner] = None,
        doc_builder: Optional[RestaurantDocumentBuilder] = None,
        metadata_store: Optional[MetadataStore] = None,
    ):
        self.loader = loader or ZomatoDataLoader()
        self.cleaner = cleaner or ZomatoDataCleaner()
        self.doc_builder = doc_builder or RestaurantDocumentBuilder()
        self.metadata_store = metadata_store or MetadataStore()

    def run(
        self,
        raw_csv_path: Optional[Path] = None,
        raw_df: Optional[pd.DataFrame] = None,
        nrows: Optional[int] = None,
        save_processed: bool = False,
        processed_dir: Optional[Path] = None,
    ) -> Phase1Result:
        """
        Executes the Phase 1 ingestion, cleaning, document generation, and indexing.

        Args:
            raw_csv_path: Path to raw zomato.csv (if loading from file).
            raw_df: In-memory raw DataFrame (if already loaded).
            nrows: Optional row limit for fast processing or testing.
            save_processed: Whether to persist the cleaned DataFrame to CSV.
            processed_dir: Directory where processed CSV should be written.

        Returns:
            Phase1Result containing cleaned data, semantic documents, and indexed store.
        """
        # 1. Load Data
        if raw_df is not None:
            df_raw = raw_df.head(nrows) if nrows else raw_df.copy()
        else:
            df_raw = self.loader.load_from_csv(file_path=raw_csv_path, nrows=nrows)

        raw_count = len(df_raw)

        # 2. Clean Data
        cleaned_df = self.cleaner.clean_dataframe(df_raw)
        cleaned_count = len(cleaned_df)

        # 3. Build Semantic Documents
        documents = self.doc_builder.build_documents(cleaned_df)

        # 4. Populate Metadata Store
        indexed_count = self.metadata_store.index_dataframe(cleaned_df)

        # 5. Optional Save Processed CSV
        if save_processed:
            out_dir = Path(processed_dir) if processed_dir else PROCESSED_DATA_DIR
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / CLEANED_CSV_FILENAME
            cleaned_df.to_csv(out_path, index=False)

        # 6. Gather Statistics
        stats = {
            "raw_records_count": raw_count,
            "cleaned_records_count": cleaned_count,
            "documents_generated": len(documents),
            "indexed_records_count": indexed_count,
            "distinct_cities": len(self.metadata_store.get_distinct_cities()),
            "distinct_locations": len(self.metadata_store.get_distinct_locations()),
            "min_cost": int(cleaned_df["cost_for_two"].min()) if not cleaned_df.empty else 0,
            "max_cost": int(cleaned_df["cost_for_two"].max()) if not cleaned_df.empty else 0,
            "avg_rating": round(float(cleaned_df["rating"].mean()), 2) if not cleaned_df.empty else 0.0,
        }

        return Phase1Result(
            cleaned_df=cleaned_df,
            documents=documents,
            metadata_store=self.metadata_store,
            stats=stats,
        )

