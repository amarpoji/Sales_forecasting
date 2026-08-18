# M5 Forecasting - Accuracy Dataset Overview

The M5 Forecasting - Accuracy dataset, provided by Walmart, contains hierarchical unit sales data for 3,049 products across 10 stores in California (CA), Texas (TX), and Wisconsin (WI).

## Core Files
1. **sales_train_evaluation.csv**: Historical daily unit sales.
2. **calendar.csv**: Date-specific metadata (events, SNAP eligibility).
3. **sell_prices.csv**: Weekly product prices per store.
4. **sample_submission.csv**: Format template for forecasts.

## Key Data Characteristics
- **Grain**: Daily unit sales per store per product.
- **Hierarchy**: Products categorized into Departments and Categories.
- **Temporal Coverage**: 1,941 days of history + 28 days of evaluation horizon.
- **Constraints**: Contains sparse data (many zero-sales days) and relies on external calendar/price metadata for feature engineering.

## Purpose
Used for developing demand forecasting models and simulating replenishment policies (inventory optimization).
