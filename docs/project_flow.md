# Project Flow - AI Sales Forecasting and Inventory Optimizer

## Project Mission
Convert historical Walmart M5 product-store sales into reliable demand forecasts and actionable replenishment recommendations. The system answers:
1. How many units of each product will each store sell over the next 7 days?
2. Which products are at risk of stockout or overstock?
3. How much inventory should be reordered, and why?

## Source of Truth
- CONTEXT.md in project root is the master specification for all phases, standards, and expectations.

---

## Progress Log

### Phase 1: Foundation (COMPLETE)

What was built:
- Project directory structure under `src/sales_optimizer/` with clean layer separation (api, data, features, inventory, models, monitoring, database).
- `pyproject.toml` with production + dev dependencies (pandas, numpy, scikit-learn, lightgbm, fastapi, uvicorn, streamlit, pydantic, sqlalchemy, psycopg2, pyyaml; dev: pytest, ruff, mypy).
- `src/sales_optimizer/exceptions.py` - domain exception hierarchy (SalesOptimizerError, DataValidationError, FeatureBuildError, ModelArtifactError, InventoryOptimizationError).
- `src/sales_optimizer/config.py` - Pydantic Settings object (single source of truth, env-file driven).
- `configs/base.yaml` - dataset manifest declarations, development subset selection (CA_1, TX_1, 50 products, seed 42), forecast horizon, log level.
- `tests/fixtures/m5_data.py` - deterministic M5-shaped fixtures (sales, calendar, prices) for offline testing.
- `scripts/generate_manifest.py` + `data/raw/dataset_manifest.md` - SHA-256 hashes of the four official M5 files.

Why it matters:
- Errors fail clearly with domain meaning (Section 8).
- All config values are centralized and typed (Section 6).
- Raw data immutability is proven by hashes (Section 3, Rule 3).

Pitfalls discovered:
- The machine has a Windows-layout venv (`.venv/Scripts/python.exe`), must run scripts through it, not system python (pyenv shim is broken under WSL).
- System python is externally managed (PEP 668) - do not pip install into it.

### Phase 2: Data pipeline (IN PROGRESS - one step left)

What was built:
- `src/sales_optimizer/data/ingestion.py` - `ingest_m5_file()` reads raw CSVs, checks existence, parses, validates expected columns, logs row counts.
- `src/sales_optimizer/data/transformation.py` - `transform_to_long()` melts wide M5 sales (d_1..d_1941) into canonical long form, joins calendar for date/week_id, renames to canonical schema (item_id -> product_id, dept_id -> department_id, cat_id -> category_id, wm_yr_wk -> week_id).
- `src/sales_optimizer/data/validation.py` - `validate_sales_schema()` enforces the canonical contract: required columns, units_sold >= 0, unique (date, store_id, product_id).
- `scripts/build_canonical_dataset.py` - orchestrates ingest -> transform -> price join -> validate -> write `data/processed/canonical_sales.parquet`.
- `tests/integration/test_data_pipeline.py` + `tests/conftest.py` - integration test passes (1 passed) using the deterministic fixtures.

Why it matters:
- Wide-to-long is the mandated canonical grain (Section 3, Canonical transformation).
- Validation enforces Section 9 data contracts; observed zeros preserved.
- Parquet output is partitioned-ready for full-scale (Section 3 scaling rules).

Pitfalls discovered:
- `sell_prices.csv` uses `item_id` and `wm_yr_wk` - must be renamed to canonical `product_id` / `week_id` BEFORE the merge with canonical_df, otherwise pandas raises KeyError on the right-hand keys (`on` keys must exist in BOTH frames).
- The price join name mismatch was hit twice: first `product_id` missing, then `week_id` missing. Root cause: prices_df is loaded raw; canonical names only exist after transform_to_long.

Next step for Phase 2:
- Run `build_canonical_dataset.py` end-to-end on the real M5 data and confirm `data/processed/canonical_sales.parquet` is produced.
- Benchmark peak memory + runtime of the melt (inform the full-scale decision, Section 3 scaling rules).

---

## Upcoming Phases

### Phase 3: EDA and baselines (NEXT)
- Analyze M5 demand patterns: intermittent demand, price coverage, events, hierarchy.
- Implement naive baselines: previous day, same day last week, 7-day moving average.
- Establish rolling-origin evaluation harness + protected d_1914-d_1941 holdout (28 days = 4 x 7-day segments for MVP).

### Phase 4: ML forecasting
- Leakage-safe features (lags, rolling stats, calendar, price signals).
- Candidate models: linear -> tree -> LightGBM global model.
- Rolling backtests, model selection, versioned artifact.

### Phase 5: Inventory optimization
- Deterministic simulated inventory layer (M5 has no inventory ledger).
- Lead-time demand, safety stock, reorder point, order constraints.
- Every output labeled simulated.

### Phase 6: Product interfaces
- FastAPI endpoints (/health, /ready, /forecasts, /inventory/recommendations, /predictions).
- Streamlit dashboard (actual vs forecast, stockout/overstock risk, order qty).

### Phase 7: Deployment and operations
- Docker + PostgreSQL orchestration, CI quality gates, monitoring + retraining rules.