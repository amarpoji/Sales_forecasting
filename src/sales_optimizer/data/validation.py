import logging
import pandas as pd
from sales_optimizer.exceptions import DataValidationError

logger = logging.getLogger(__name__)

def validate_sales_schema(df: pd.DataFrame):
    """Validates the canonical long-form sales schema."""
    required_cols = [
        "date", "day_id", "store_id", "product_id", 
        "department_id", "category_id", "state_id", 
        "units_sold", "week_id", "sell_price"
    ]
    
    # Check for missing columns
    for col in required_cols:
        if col not in df.columns:
            raise DataValidationError(f"Missing required column: {col}")

    # Validate non-negative sales
    if (df["units_sold"] < 0).any():
        raise DataValidationError("Negative units_sold found")

    # Validate unique records
    if df.duplicated(subset=["date", "store_id", "product_id"]).any():
        raise DataValidationError("Duplicate records found for date-store-product combination")

    logger.info("schema_validation_passed", extra={"rows": len(df)})
