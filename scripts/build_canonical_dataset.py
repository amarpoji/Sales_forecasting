import logging
import pandas as pd
from pathlib import Path
from sales_optimizer.config import settings
from sales_optimizer.data.ingestion import ingest_m5_file
from sales_optimizer.data.transformation import transform_to_long
from sales_optimizer.data.validation import validate_sales_schema

# Configure logging
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

def build_canonical_dataset():
    logger.info("Starting canonical data pipeline...")
    
    raw_dir = Path(settings.data_raw_dir)
    
    # 1. Ingest
    sales_df = ingest_m5_file(str(raw_dir / "sales_train_evaluation.csv"), ["id", "item_id", "dept_id", "cat_id", "store_id", "state_id"])
    calendar_df = ingest_m5_file(str(raw_dir / "calendar.csv"), ["d", "date", "wm_yr_wk"])
    prices_df = ingest_m5_file(str(raw_dir / "sell_prices.csv"), ["store_id", "item_id", "wm_yr_wk", "sell_price"])
    
    # 2. Transform (Wide to Long)
    canonical_df = transform_to_long(sales_df, calendar_df)
    
    # 3. Join Prices
    # Ensure prices_df has the canonical column name for the merge
    prices_df = prices_df.rename(columns={
        "item_id": "product_id",
        "wm_yr_wk": "week_id"
    })
    
    # Join on store_id, product_id, and week_id
    canonical_df = canonical_df.merge(
        prices_df, 
        on=["store_id", "product_id", "week_id"], 
        how="left"
    )
    
    # 4. Validate
    validate_sales_schema(canonical_df)
    
    # 5. Persist
    output_path = Path(settings.data_processed_dir) / "canonical_sales.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canonical_df.to_parquet(output_path, index=False)
    
    logger.info(f"Pipeline complete. Data saved to {output_path}")

if __name__ == "__main__":
    build_canonical_dataset()
