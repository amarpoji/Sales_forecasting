from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Base application settings
    app_name: str = "Sales Inventory Optimizer"
    log_level: str = "INFO"
    
    # Paths
    data_raw_dir: str = "data/raw"
    data_processed_dir: str = "data/processed"
    
    # Forecast Settings
    forecast_horizon: int = 7
    
    # Database (Placeholder for now)
    database_url: str = "sqlite:///./sales_inventory.db"
    
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
