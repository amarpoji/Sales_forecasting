import pandas as pd
import pytest

@pytest.fixture
def sample_sales_df():
    return pd.DataFrame({
        "day_id": ["d_1", "d_2", "d_3"],
        "store_id": ["CA_1", "CA_1", "CA_1"],
        "product_id": ["HOBBIES_1_001", "HOBBIES_1_001", "HOBBIES_1_001"],
        "units_sold": [1, 0, 2],
    })

@pytest.fixture
def sample_calendar_df():
    return pd.DataFrame({
        "date": ["2011-01-29", "2011-01-30", "2011-01-31"],
        "wm_yr_wk": [11101, 11101, 11101],
        "event_name_1": [None, None, "SuperBowl"],
        "event_type_1": [None, None, "Sporting"],
        "snap_CA": [0, 0, 0],
    })

@pytest.fixture
def sample_prices_df():
    return pd.DataFrame({
        "store_id": ["CA_1", "CA_1"],
        "item_id": ["HOBBIES_1_001", "HOBBIES_1_001"],
        "wm_yr_wk": [11101, 11102],
        "sell_price": [1.99, 2.05],
    })
