import pandas as pd
import logging
from pathlib import Path
from typing import Dict
from sales_optimizer.exceptions import DataValidationError

logger = logging.getLogger(__name__)

def ingest_m5_file(path: str, expected_cols: list) -> pd.DataFrame:
    """Ingests and performs basic schema validation on raw M5 files."""
    path_obj = Path(path)
    if not path_obj.exists():
        raise DataValidationError(f"File not found: {path}")

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        raise DataValidationError(f"Could not read CSV: {path}") from exc

    # Validate columns
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        raise DataValidationError(f"Missing columns in {path}: {missing}")

    logger.info("data_ingested", extra={"file": path, "rows": len(df)})
    return df
