import pytest
import pandas as pd
from sales_optimizer.data.transformation import transform_to_long
from sales_optimizer.data.validation import validate_sales_schema
from tests.fixtures.m5_data import sample_sales_df, sample_calendar_df

def test_data_pipeline_integration(sample_sales_df, sample_calendar_df):
    # Prepare fixtures for transformation
    # Note: transformation expects specific columns like 'id', 'item_id', etc.
    # Adjusting fixture to fit the transformation expected input
    sales = sample_sales_df.rename(columns={"product_id": "item_id"})
    sales["id"] = "HOBBIES_1_001_CA_1_evaluation"
    sales["dept_id"] = "HOBBIES_1"
    sales["cat_id"] = "HOBBIES"
    sales["store_id"] = "CA_1"
    sales["state_id"] = "CA"
    
    # Wide to long
    # We need to reshape the fixture a bit for the melt to work as expected by the function
    wide_sales = sales.pivot(index=["id", "item_id", "dept_id", "cat_id", "store_id", "state_id"], 
                            columns="day_id", values="units_sold").reset_index()
    
    calendar = sample_calendar_df.rename(columns={"date": "date", "wm_yr_wk": "wm_yr_wk"})
    calendar["d"] = ["d_1", "d_2", "d_3"]
    
    # Run transformation
    long_df = transform_to_long(wide_sales, calendar)
    
    # Add dummy price for validation
    long_df["sell_price"] = 1.99
    
    # Validate result
    validate_sales_schema(long_df)
    
    assert "units_sold" in long_df.columns
    assert len(long_df) == 3
