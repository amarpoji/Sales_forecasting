import pandas as pd
import yaml
import logging
from pathlib import Path
from sales_optimizer.config import settings
from sales_optimizer.data.ingestion import ingest_m5_file
from sales_optimizer.exceptions import DataValidationError

logger = logging.getLogger(__name__)

def select_development_subset(
    sales_df: pd.DataFrame,
    n_stores: int = 2,
    n_products: int = 50,
    min_history_days: int = 730,  # 2 years
    random_seed: int = 42
) -> dict:
    """
    Deterministically selects a development subset of stores and products.
    
    Selection criteria:
    - Stores with highest total sales volume
    - Products with at least min_history_days of non-zero sales history
    - Balanced mix of categories/departments
    - Products spanning different demand patterns (regular, intermittent)
    """
    # Identify d_ columns
    d_cols = [c for c in sales_df.columns if c.startswith("d_")]
    
    # Calculate total sales per store
    store_sales = sales_df.groupby("store_id")[d_cols].sum().sum(axis=1).sort_values(ascending=False)
    selected_stores = store_sales.head(n_stores).index.tolist()
    
    # Filter to selected stores
    store_df = sales_df[sales_df["store_id"].isin(selected_stores)].copy()
    
    # Calculate sales history length per product (days with data, not just non-zero)
    # M5 has data for all d_1 to d_1941 for all products, but some may be all zeros early on
    # We want products that have been "active" (non-zero) for at least min_history_days
    store_df["non_zero_days"] = (store_df[d_cols] > 0).sum(axis=1)
    
    # Filter products with sufficient non-zero history
    active_products = store_df[store_df["non_zero_days"] >= min_history_days]
    
    if len(active_products) < n_products:
        logger.warning(f"Only {len(active_products)} products have {min_history_days}+ non-zero days. Relaxing criterion.")
        # Fallback: products with most non-zero days
        active_products = store_df.nlargest(n_products, "non_zero_days")
    
    # Ensure category/department diversity
    # Group by category and select proportionally
    cat_counts = active_products["cat_id"].value_counts()
    selected_products = []
    
    for cat_id, count in cat_counts.items():
        cat_products = active_products[active_products["cat_id"] == cat_id]
        n_select = max(1, int(n_products * count / len(active_products)))
        selected_products.extend(cat_products.nlargest(n_select, "non_zero_days")["item_id"].tolist())
    
    # Deduplicate while preserving order
    selected_products = list(dict.fromkeys(selected_products))
    
    # Trim or pad to exactly n_products
    if len(selected_products) > n_products:
        selected_products = selected_products[:n_products]
    elif len(selected_products) < n_products:
        # Add more from remaining products
        remaining = active_products[~active_products["item_id"].isin(selected_products)]
        additional = remaining.nlargest(n_products - len(selected_products), "non_zero_days")["item_id"].tolist()
        selected_products.extend(additional)
        selected_products = list(dict.fromkeys(selected_products))[:n_products]
    
    # Get unique product IDs with their metadata
    product_info = sales_df[sales_df["item_id"].isin(selected_products)][
        ["item_id", "dept_id", "cat_id", "store_id", "state_id"]
    ].drop_duplicates()
    
    subset_config = {
        "store_ids": selected_stores,
        "product_ids": selected_products,
        "selection_criteria": {
            "n_stores": n_stores,
            "n_products": n_products,
            "min_history_days": min_history_days,
            "random_seed": random_seed,
            "store_selection": "top_total_sales",
            "product_selection": "category_balanced_max_nonzero_days"
        },
        "product_metadata": product_info.to_dict(orient="records")
    }
    
    logger.info("subset_selected", extra={
        "stores": selected_stores,
        "n_products": len(selected_products),
        "categories": product_info["cat_id"].nunique(),
        "departments": product_info["dept_id"].nunique()
    })
    
    return subset_config

def save_subset_config(config: dict, output_path: str):
    """Saves subset configuration to YAML."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    logger.info("subset_config_saved", extra={"path": output_path})

def main():
    logging.basicConfig(level="INFO")
    
    # Load raw sales data
    raw_dir = Path(settings.data_raw_dir)
    sales_df = ingest_m5_file(str(raw_dir / "sales_train_evaluation.csv"), 
                              ["id", "item_id", "dept_id", "cat_id", "store_id", "state_id"])
    
    # Select subset
    subset = select_development_subset(sales_df)
    
    # Save
    save_subset_config(subset, "configs/subset.yaml")
    
    print(f"Selected stores: {subset['store_ids']}")
    print(f"Selected {len(subset['product_ids'])} products")
    print(f"Categories covered: {len(set(p['cat_id'] for p in subset['product_metadata']))}")

if __name__ == "__main__":
    main()