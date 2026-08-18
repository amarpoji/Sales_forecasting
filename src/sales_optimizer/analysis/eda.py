import pandas as pd
import logging
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)

def load_subset_data(canonical_path: str, subset_config_path: str) -> pd.DataFrame:
    """Loads the canonical dataset and filters for the defined subset."""
    import yaml
    with open(subset_config_path, 'r') as f:
        subset = yaml.safe_load(f)
    
    df = pd.read_parquet(canonical_path)
    # Filter stores and products
    df = df[
        (df["store_id"].isin(subset["store_ids"])) & 
        (df["product_id"].isin(subset["product_ids"]))
    ]
    # Filter out protected holdout (d_1914 onwards)
    # We do this by mapping day_id to integer and filtering
    df["day_num"] = df["day_id"].str.extract(r'(\d+)').astype(int)
    df = df[df["day_num"] < 1914]
    
    logger.info("subset_data_loaded", extra={"rows": len(df)})
    return df

def generate_eda_plots(df: pd.DataFrame, output_dir: str):
    """Generates and saves exploratory plots."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 1. Target Distribution
    plt.figure(figsize=(10, 6))
    sns.histplot(df["units_sold"], bins=50)
    plt.title("Distribution of Units Sold")
    plt.savefig(f"{output_dir}/units_dist.png")
    
    # 2. Sales Over Time (Rolling mean)
    plt.figure(figsize=(12, 6))
    df.groupby("date")["units_sold"].sum().rolling(7).mean().plot()
    plt.title("7-Day Rolling Average Sales")
    plt.savefig(f"{output_dir}/rolling_sales.png")
    
    logger.info("eda_plots_saved", extra={"dir": output_dir})
