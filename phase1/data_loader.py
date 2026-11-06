"""
Data loader for the Zomato Restaurant Recommendation dataset.
Supports loading from local CSV files and fetching from Hugging Face.
"""

import os
import urllib.request
from pathlib import Path
from typing import Optional
import pandas as pd

from phase1.config import (
    HUGGINGFACE_RAW_CSV_URL,
    RAW_DATA_DIR,
    RAW_CSV_FILENAME,
)


class ZomatoDataLoader:
    """Handles downloading and loading the Zomato restaurant dataset."""

    def __init__(self, raw_data_dir: Optional[Path] = None):
        self.raw_data_dir = Path(raw_data_dir) if raw_data_dir else RAW_DATA_DIR
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.default_csv_path = self.raw_data_dir / RAW_CSV_FILENAME

    def download_dataset(
        self,
        target_path: Optional[Path] = None,
        url: str = HUGGINGFACE_RAW_CSV_URL,
        chunk_size: int = 1024 * 1024,
    ) -> Path:
        """
        Download raw dataset from Hugging Face.
        """
        dest_path = Path(target_path) if target_path else self.default_csv_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        with urllib.request.urlopen(req) as response, open(dest_path, "wb") as out_file:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)

        return dest_path

    def load_from_csv(
        self,
        file_path: Optional[Path] = None,
        nrows: Optional[int] = None,
        usecols: Optional[list] = None,
    ) -> pd.DataFrame:
        """
        Load dataset into a pandas DataFrame from CSV.
        """
        path = Path(file_path) if file_path else self.default_csv_path

        if not path.exists():
            raise FileNotFoundError(
                f"Zomato dataset file not found at: {path}. "
                f"Please download it first or pass a valid file_path."
            )

        # Auto-detect pipe ('|') vs comma (',') delimiter from header line
        sep = ","
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                first_line = f.readline()
                if "|" in first_line and first_line.count("|") > first_line.count(","):
                    sep = "|"
        except Exception:
            pass

        df = pd.read_csv(
            path,
            sep=sep,
            nrows=nrows,
            usecols=usecols,
            encoding="utf-8",
            on_bad_lines="skip",
        )
        return df

    def get_data(
        self,
        file_path: Optional[Path] = None,
        auto_download: bool = False,
        nrows: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Convenience method to retrieve dataset, downloading if needed and specified.
        """
        path = Path(file_path) if file_path else self.default_csv_path

        if not path.exists():
            if auto_download:
                self.download_dataset(target_path=path)
            else:
                raise FileNotFoundError(
                    f"Dataset not found at {path}. Set auto_download=True or provide a local path."
                )

        return self.load_from_csv(file_path=path, nrows=nrows)

