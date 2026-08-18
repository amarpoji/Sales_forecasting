import pandas as pd
import logging
from sales_optimizer.exceptions import DataValidationError

logger = logging.getLogger(__name__)

def transform_to_long(sales_df: pd.DataFrame, calendar_df: pd.DataFrame) -> pd.DataFrame:
    """Transforms wide M5 sales_train_evaluation to canonical long form."""
    # Identify d_ columns
    d_cols = [c for c in sales_df.columns if c.startswith("d_")]
    
    # Melt
    long_df = sales_df.melt(
        id_vars=["id", "item_id", "dept_id", "cat_id", "store_id", "state_id"],
        value_vars=d_cols,
        var_name="day_id",
        value_name="units_sold"
    )
    
    # Merge calendar
    if "date" not in calendar_df.columns or "d" not in calendar_df.columns:
         raise DataValidationError("Calendar file missing required d or date mapping.")
         
    long_df = long_df.merge(calendar_df[["d", "date", "wm_yr_wk"]], left_on="day_id", right_on="d")
    
    # Rename for canonical schema
    long_df = long_df.rename(columns={
        "item_id": "product_id",
        "dept_id": "department_id",
        "cat_id": "category_id",
        "wm_yr_wk": "week_id"
    })
    
    # Drop temp cols
    long_df = long_df.drop(columns=["id", "d"])
    
    logger.info("transformation_completed", extra={"rows": len(long_df)})
    return long_df
