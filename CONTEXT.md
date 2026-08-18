# Senior ML Engineer Agent Instructions

## 1. Mission

Build a production-quality **AI Sales Forecasting and Inventory Optimizer** using the **M5 Forecasting - Accuracy** Walmart retail dataset. Convert historical product-store sales, prices, calendar events, and product hierarchy data into reliable demand forecasts and actionable replenishment recommendations.

The system must answer:

1. How many units of each product will each store sell over the next 7 days?
2. Which products are at risk of stockout or overstock?
3. How much inventory should be reordered, and why?

Treat this as a real engineering product, not a notebook-only demonstration. Every important result must be reproducible, tested, observable, and explainable.

---

## 2. Agent Role and Working Style

Act as a senior machine-learning engineer and data scientist. Own the full path from raw data to a deployable decision-support system.

For every task:

1. Inspect the existing repository, configuration, tests, and documentation before changing anything.
2. State assumptions when requirements or data semantics are unclear.
3. Prefer the smallest correct implementation that can be extended later.
4. Separate data ingestion, transformations, modeling, business logic, and presentation.
5. Do not silently invent business rules or data values.
6. Do not overwrite unrelated user changes.
7. Add or update tests with every material code change.
8. Run relevant checks before declaring the work complete.
9. Report what changed, what was verified, and any remaining limitations.

If a requirement is ambiguous and would materially affect correctness, stop and ask for clarification. Otherwise, make a conservative assumption, document it, and continue.

---

## 3. Initial MVP Scope

Build the first working version with:

- The official M5 Forecasting - Accuracy source files.
- 2 stores for the first development subset.
- 50-100 products.
- Daily sales granularity.
- At least 2 years of M5 history for development.
- A 7-day demand forecast horizon.
- Daily batch predictions.
- A global forecasting model across store-product combinations.
- A rule-based inventory optimizer using forecasts, safety stock, lead time, and inventory position.
- FastAPI for serving predictions.
- Streamlit for the business dashboard.
- PostgreSQL for persistent application data.

After the subset pipeline is correct and benchmarked, scale toward all 10 stores, 3,049 products, the complete available history, and an optional 28-day forecast horizon. Do not load or melt the complete dataset into memory until memory use has been measured and the pipeline supports partitioned processing.

---

## Official Dataset: M5 Forecasting - Accuracy

The project dataset is the Walmart sales data released for the **M5 Forecasting - Accuracy** competition.

Authoritative references:

- Competition: <https://www.kaggle.com/competitions/m5-forecasting-accuracy>
- Competitors Guide: <https://github.com/Mcompetitions/M5-methods/blob/master/M5-Competitors-Guide.pdf>
- Official methods and benchmarks: <https://github.com/Mcompetitions/M5-methods>

The dataset contains 3,049 products sold across 10 stores in California, Texas, and Wisconsin. Products are organized into three categories and seven departments. The evaluation dataset contains 1,941 known daily observations per bottom-level product-store series.

### Required raw files

Use these files from the original competition source:

| File | Required purpose |
|---|---|
| `sales_train_evaluation.csv` | Historical daily unit sales in wide `d_1` through `d_1941` format |
| `calendar.csv` | Maps `d_*` identifiers to dates, weekdays, events, and state-level SNAP indicators |
| `sell_prices.csv` | Weekly product price by `store_id`, `item_id`, and `wm_yr_wk` |
| `sample_submission.csv` | Reference only for the original competition forecast shape |

Do not substitute an unofficial repackaged dataset without documenting its provenance and verifying that its row counts, keys, and values match the original source.

### Raw-data handling

1. Keep downloaded competition files immutable under `data/raw/m5/`.
2. Do not commit the raw competition files or Kaggle credentials to Git.
3. Record filenames, byte sizes, and SHA-256 hashes in a dataset manifest.
4. Validate every file before transformation.
5. Preserve the original `d_*` identifier so transformed records remain traceable.
6. Write processed datasets in partitioned Parquet or an equivalent typed columnar format before loading application tables.
7. Treat PostgreSQL as an application and serving store, not necessarily as the first staging area for tens of millions of raw observations.

### Canonical transformation

Transform the wide sales table into the following canonical long-form grain:

```text
one row = one date x store_id x product_id
```

Map M5 fields as follows:

| Canonical field | M5 source |
|---|---|
| `date` | `calendar.date` joined through `d` |
| `day_id` | `d_1` ... `d_1941` |
| `store_id` | `sales_train_evaluation.store_id` |
| `product_id` | `sales_train_evaluation.item_id` |
| `department_id` | `sales_train_evaluation.dept_id` |
| `category_id` | `sales_train_evaluation.cat_id` |
| `state_id` | `sales_train_evaluation.state_id` |
| `units_sold` | Value from the corresponding `d_*` column |
| `week_id` | `calendar.wm_yr_wk` |
| `sell_price` | `sell_prices.sell_price` joined by store, product, and week |
| `event_name_1/2` | `calendar.event_name_1/2` |
| `event_type_1/2` | `calendar.event_type_1/2` |
| `snap_eligible_day` | State-appropriate `snap_CA`, `snap_TX`, or `snap_WI` |

Do not rename SNAP eligibility as a generic promotion. SNAP availability, calendar events, price movement, and derived discount signals are distinct features.

### Development subset

The default development subset must be deterministic and configurable. Select:

- Exactly 2 named stores.
- Between 50 and 100 named products with sufficient history.
- At least 2 years of observations ending before the final holdout.
- A mix of categories, demand volumes, and intermittent-demand patterns.

Persist the selected store IDs, product IDs, selection rule, and random seed in configuration. Never sample a different subset silently between runs.

### Scaling rules

The full bottom-level dataset contains more than 30,000 product-store series and becomes tens of millions of rows in long form. Therefore:

- Read only required columns.
- Specify compact dtypes explicitly.
- Process by store or bounded row groups when melting.
- Avoid repeated full-dataframe copies.
- Partition processed data by store and/or date.
- Push filters and aggregations into the storage engine where practical.
- Benchmark peak memory, runtime, and artifact size before increasing scope.
- Never solve an out-of-memory error by silently dropping data.

### Known dataset limitations

M5 does not provide authoritative on-hand inventory, purchase orders, backorders, supplier lead times, minimum-order quantities, or warehouse capacity. These values must be simulated for the portfolio decision layer and must never be described as Walmart-provided or observed facts.

---

## 4. Expected Architecture

The preferred flow is:

```text
Raw M5 CSV files
        -> ingestion
        -> schema and quality validation
        -> partitioned canonical dataset
        -> cleaned PostgreSQL application tables
        -> feature pipeline
        -> time-based training and backtesting
        -> model registry / versioned artifact
        -> batch forecasts
        -> inventory optimization
        -> prediction and recommendation tables
        -> FastAPI
        -> Streamlit dashboard
```

Keep these boundaries explicit:

- **Data layer:** ingestion, validation, cleaning, storage.
- **Feature layer:** deterministic feature generation.
- **Model layer:** training, evaluation, selection, serialization, inference.
- **Decision layer:** inventory calculations and business constraints.
- **Serving layer:** API contracts and dashboard.
- **Operations layer:** logging, configuration, testing, orchestration, monitoring.

---

## 5. Recommended Repository Structure

Follow the existing repository structure when one is already established. Otherwise use:

```text
sales-inventory-optimizer/
├── configs/
│   ├── base.yaml
│   └── local.example.yaml
├── data/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   └── predictions/
├── notebooks/
│   ├── 01_eda.ipynb
│   └── 02_model_experiments.ipynb
├── src/
│   └── sales_optimizer/
│       ├── api/
│       ├── data/
│       ├── features/
│       ├── inventory/
│       ├── models/
│       ├── monitoring/
│       ├── database/
│       ├── config.py
│       ├── exceptions.py
│       └── logging_config.py
├── dashboard/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── models/
├── scripts/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── README.md
└── CONTEXT.md
```

Notebooks are for exploration only. Production transformations and model logic must live in importable Python modules.

---

## 6. Configuration and Secrets

All environment-specific values must be configurable. Examples include:

- Database connection details.
- Input and output paths.
- Forecast horizon.
- Training cutoff dates.
- Feature windows.
- Random seeds.
- Model hyperparameters.
- Service-level targets.
- Default lead times.
- Logging level.

Rules:

1. Never hardcode secrets, passwords, tokens, or production connection strings.
2. Read secrets from environment variables or the platform's secret manager.
3. Commit only an example environment file with fake values.
4. Validate configuration at application startup and fail with a clear message when required values are missing.
5. Use one typed settings object as the source of truth.
6. Do not scatter direct environment-variable access throughout the codebase.

---

## 7. Logging Standards

Use the standard Python `logging` module or a structured logging wrapper. Never use `print()` for operational messages in production code.

### Required logging behavior

- Configure logging once at each application entry point.
- Inside modules, create loggers with `logging.getLogger(__name__)`.
- Prefer structured fields over long interpolated strings.
- Include identifiers such as `run_id`, `model_version`, `store_id`, `product_id`, and `forecast_date` when relevant.
- Log pipeline start, completion, duration, record counts, rejected rows, model metrics, model version, and output location.
- Use `logger.exception(...)` inside an exception handler when a traceback is useful.
- Never log secrets, credentials, full connection strings, payment data, or unnecessary customer-level data.
- Avoid per-row logging in large loops. Log aggregated counts and representative samples.

### Log levels

- `DEBUG`: diagnostics useful during development.
- `INFO`: normal lifecycle events and major business outputs.
- `WARNING`: recoverable anomalies, fallback behavior, or unexpected data that does not stop execution.
- `ERROR`: an operation failed and could not produce its promised result.
- `CRITICAL`: the service or core pipeline cannot operate safely.

Example:

```python
import logging
from time import perf_counter

logger = logging.getLogger(__name__)


def build_features(df):
    started_at = perf_counter()
    logger.info("feature_build_started", extra={"input_rows": len(df)})

    result = _create_features(df)

    logger.info(
        "feature_build_completed",
        extra={
            "input_rows": len(df),
            "output_rows": len(result),
            "duration_seconds": round(perf_counter() - started_at, 3),
        },
    )
    return result
```

---

## 8. Exception-Handling Standards

Use `try`/`except`, not “try and expect.” Exception handling must preserve failures, not hide them.

### Rules

1. Catch only exceptions the code can meaningfully handle.
2. Catch specific exception types instead of using bare `except:`.
3. Keep the `try` block as small as possible.
4. Never silently return `None`, an empty dataframe, or a default forecast after an unexpected failure.
5. Validate inputs before beginning expensive work.
6. Raise domain-specific exceptions at application boundaries.
7. Preserve the original cause with `raise ... from exc`.
8. Log an exception once at the boundary responsible for handling it. Avoid duplicate logging at every stack level.
9. Use `finally` or context managers for guaranteed resource cleanup.
10. Retries are allowed only for transient failures such as temporary database or network errors. Use bounded retries with backoff; do not retry validation or programming errors.

Define a small exception hierarchy:

```python
class SalesOptimizerError(Exception):
    """Base exception for expected application failures."""


class DataValidationError(SalesOptimizerError):
    """Input data violates the required contract."""


class FeatureBuildError(SalesOptimizerError):
    """Feature generation could not be completed."""


class ModelArtifactError(SalesOptimizerError):
    """A model artifact is missing, invalid, or incompatible."""


class InventoryOptimizationError(SalesOptimizerError):
    """A replenishment recommendation could not be calculated."""
```

Example:

```python
def load_sales(path):
    try:
        frame = pd.read_csv(path)
    except FileNotFoundError as exc:
        raise DataValidationError(f"Sales file was not found: {path}") from exc
    except pd.errors.ParserError as exc:
        raise DataValidationError(f"Sales file is not valid CSV: {path}") from exc

    validate_sales_schema(frame)
    return frame
```

At an application boundary:

```python
try:
    run_training_pipeline(settings)
except SalesOptimizerError:
    logger.exception("training_pipeline_failed")
    raise
```

---

## 9. Data Contracts and Validation

Define separate contracts for the immutable M5 raw files, canonical sales data, and simulated inventory data.

The minimum canonical sales columns are:

| Column | Type | Rule |
|---|---|---|
| `date` | date | Required and not in the unintended future |
| `day_id` | string | Required M5 `d_*` identifier |
| `store_id` | string | Required and non-empty |
| `product_id` | string | Required and non-empty |
| `department_id` | string | Required and non-empty |
| `category_id` | string | Required and non-empty |
| `state_id` | string | Required and non-empty |
| `units_sold` | numeric | Greater than or equal to zero |
| `week_id` | integer | Required M5 `wm_yr_wk` value |
| `sell_price` | numeric/nullable | Greater than zero when present |
| `snap_eligible_day` | integer | Must be 0 or 1 |

Simulated inventory must be stored separately with fields such as `on_hand`, `on_order`, `backorders`, `lead_time_days`, `minimum_order_quantity`, and `case_pack_size`. Every simulated table must include `simulation_version`, `simulation_seed`, and `is_simulated = true`.

Validate:

- Required columns and data types.
- Unique `(date, store_id, product_id)` records.
- Missing and duplicated dates.
- Negative or impossible values.
- Extreme values and sudden distribution shifts.
- Categorical values not seen during training.
- Timezone and date normalization.
- Data freshness.
- Row counts before and after transformations.
- Expected M5 day coverage and valid `d_*` to date mapping.
- Valid joins between sales, calendar, and price data.
- Duplicate price records for `(store_id, product_id, week_id)`.
- Price coverage by store, product, and date.
- Store-to-state consistency for selecting the correct SNAP field.

The explicit zero values in M5 sales history are observed zero unit sales and must be preserved. A record created or lost during transformation is not equivalent to an observed zero. Do not fill failed joins or missing transformed records with zero.

A missing M5 price can occur when a product was not sold or had no listed price for the relevant week. Preserve missingness, investigate its meaning, and apply a documented feature policy. Do not automatically forward-fill prices across a product's introduction boundary or beyond available evidence.

Quarantine invalid rows with a rejection reason when safe to do so. Fail the pipeline when a critical validation threshold is exceeded.

---

## 10. Database Engineering

Use migrations to create and change tables. Avoid creating production schemas ad hoc from application code.

Suggested tables:

- `stores`
- `products`
- `daily_sales`
- `inventory_snapshots`
- `calendar_events`
- `sell_prices`
- `inventory_simulations`
- `model_runs`
- `forecasts`
- `inventory_recommendations`

Database requirements:

- Use primary keys and foreign keys where appropriate.
- Add a unique constraint for `(date, store_id, product_id)` in daily sales.
- Index columns used in joins, date filters, and API lookups.
- Use parameterized queries or a safe ORM; never concatenate user input into SQL.
- Use transactions for multi-step writes.
- Make ingestion idempotent with deterministic keys or upserts.
- Use connection pooling in services.
- Always close sessions and connections through context managers.
- Store timestamps in UTC and convert for display only.
- Do not expose internal database errors directly through the API.

---

## 11. Feature Engineering

Features should be deterministic and reusable for both training and inference.

Initial feature set:

```text
lag_1
lag_7
lag_14
lag_28
rolling_mean_7
rolling_mean_14
rolling_mean_28
rolling_std_7
day_of_week
week_of_year
month
is_weekend
holiday
sell_price
price_change
discount_percentage
event_name_1
event_type_1
event_name_2
event_type_2
snap_eligible_day
store_id
product_id
department_id
category_id
state_id
```

### Leakage prevention

- Create lagged targets with `groupby(...).shift(...)` before rolling calculations when appropriate.
- Never allow a row to use target information from its forecast date or the future.
- Fit encoders, scalers, and imputers on training data only.
- Use feature availability dates, not merely event dates.
- Ensure inference uses the same feature definitions and column order as training.
- Add automated tests that deliberately attempt to detect future-data leakage.
- Compute price-derived features using only prices available at the forecast origin.
- Keep calendar features only when they would genuinely be known for the forecast horizon.
- Do not use future realized sales to populate rolling features for multi-step forecasts.

For forecasts beyond one day, implement and document one strategy:

- **Direct:** train a separate target or horizon indicator for each future step.
- **Recursive:** feed prior predictions back into later lag features.
- **Multi-output:** predict the complete horizon together.

Backtesting and production inference must use the same strategy. A backtest that uses true future lag values while production uses recursive predictions is invalid.

Feature code must not depend on notebook state, global mutable variables, or manual preprocessing.

---

## 12. Forecasting and Experimentation

### Required baselines

Train and report at least:

1. Previous day's demand.
2. Same day last week.
3. Seven-day moving average.

An advanced model is acceptable only when it is compared fairly against these baselines.

### Model progression

1. Naive baselines.
2. Linear model.
3. Tree-based model.
4. LightGBM or XGBoost global model.

Use chronological splits. Never use a random train/test split for the primary forecasting evaluation.

Prefer rolling-origin backtesting with multiple validation windows. Keep the final test period untouched until the approach has been selected.

For M5 development:

1. Use rolling validation windows strictly earlier than `d_1914` for experimentation.
2. Reserve `d_1914` through `d_1941` as the final 28-day local holdout when using `sales_train_evaluation.csv`.
3. For the 7-day MVP, evaluate all four non-overlapping 7-day segments of that final holdout and report performance by horizon.
4. Do not train on the final holdout while selecting features, hyperparameters, or forecasting strategy.
5. Record the exact forecast origin and maximum training `day_id` for every run.

Track:

- Dataset version or fingerprint.
- Git commit when available.
- Training period and cutoff date.
- Feature list and feature code version.
- Hyperparameters.
- Random seed.
- Metrics overall and by store, product, category, and forecast horizon.
- Model artifact path and checksum.
- Training duration and prediction duration.

Use fixed seeds where supported, but do not claim perfect reproducibility when libraries or hardware introduce nondeterminism.

---

## 13. Evaluation Standards

Primary forecasting metrics:

- MAE.
- RMSE.
- WAPE.
- Forecast bias.

For the full M5-scale phase, add the official hierarchical **WRMSSE** evaluation or a verified equivalent implementation. WRMSSE complements rather than replaces the MVP's interpretable unit and business metrics.

Business evaluation:

- Estimated stockout rate.
- Estimated overstock units.
- Service level or fill rate.
- Lost-sales cost.
- Holding cost.
- Improvement over the selected baseline.

Do not report “accuracy” without a precise definition. Always include units, evaluation dates, number of series, and comparison baseline.

Report aggregate metrics together with segmented metrics. A strong overall result can hide poor performance for low-volume products or individual stores.

Handle zero-demand series carefully. Do not use percentage metrics that divide by zero without an explicit policy.

The final model-selection rule should balance forecast quality, inference speed, maintainability, and business cost—not just the lowest RMSE.

---

## 14. Inventory Optimization

Keep forecasting separate from replenishment policy.

Because M5 contains sales but no inventory ledger, the inventory component is a reproducible simulation. Keep original `units_sold` unchanged as the forecasting target. Do not alter M5 sales to make the simulated inventory balance.

The simulator should process each store-product series in date order:

```text
opening_on_hand
    + purchase_orders_received_today
    - simulated_fulfilled_demand
    = closing_on_hand

simulated_fulfilled_demand = min(opening_on_hand + receipts, observed_or_forecast_demand)
simulated_lost_sales = max(0, observed_or_forecast_demand - available_inventory)
```

Use observed M5 unit sales as a demand proxy for historical policy simulation and model forecasts for future simulation. State clearly that observed sales may already be censored by real-world stock availability that is not included in M5.

Simulation inputs must be deterministic and configurable. Derive or assign lead time, starting stock, service level, minimum order quantity, case-pack size, holding cost, and stockout cost through documented rules. Never generate unseeded random inventory values independently for each date.

Calculate expected demand during lead time:

```text
lead_time_demand = sum(forecast for each day within lead time)
```

An initial safety-stock policy may use:

```text
safety_stock = service_factor * forecast_error_std * sqrt(lead_time_days)
```

Calculate:

```text
reorder_point = lead_time_demand + safety_stock
inventory_position = on_hand + on_order - backorders
recommended_order_quantity = max(0, target_stock - inventory_position)
```

Apply applicable business constraints:

- Minimum order quantity.
- Case-pack rounding.
- Supplier lead time.
- Maximum storage capacity.
- Shelf life.
- Current purchase orders.
- Backorders.
- Product availability.

Every recommendation should include an explanation containing the forecast, current inventory position, lead-time demand, safety stock, reorder point, and constraints applied.

Every simulated inventory record, API response, dashboard view, and exported recommendation must be labelled as simulated. Never present these recommendations as Walmart operational records or financially validated decisions.

---

## 15. API Engineering

Use explicit request and response schemas. Suggested endpoints:

```text
GET  /health
GET  /ready
GET  /forecasts/{store_id}/{product_id}
GET  /inventory/recommendations
POST /predictions
```

Requirements:

- Validate all external inputs.
- Return stable, versioned response contracts.
- Use suitable HTTP status codes.
- Add a request or correlation ID to logs.
- Return safe user-facing errors, not tracebacks.
- Set request timeouts and bounded payload sizes.
- Load the model once at startup when practical, not on every request.
- Expose model version and forecast generation timestamp.
- Keep retraining separate from ordinary public prediction endpoints.
- Add authentication and authorization before exposing sensitive or administrative endpoints.
- Test both successful and failure responses.

Health means the process is running. Readiness means required dependencies and model artifacts are available.

---

## 16. Dashboard Standards

The dashboard should support decisions, not merely display charts.

Include:

- Actual versus forecast demand.
- Forecast horizon and model version.
- Current inventory and reorder point.
- Stockout and overstock risk.
- Recommended order quantity.
- Forecast confidence or uncertainty when available.
- Filters for store, product, category, and risk level.
- Clear “data last updated” timestamps.

The dashboard must distinguish:

- Historical actuals.
- Backtest predictions.
- Future forecasts.
- Simulated inventory recommendations.

Do not hide missing data, stale predictions, or model failures behind empty charts.

---

## 17. Testing Strategy

Use `pytest` unless the repository already uses another testing framework.

### Unit tests

Test:

- Schema validation.
- Duplicate detection.
- Lag and rolling-window calculations.
- Leakage prevention.
- Metric calculations.
- Safety stock and reorder point calculations.
- Minimum order and case-pack constraints.
- Configuration validation.
- Custom exception behavior.

### Integration tests

Test:

- Raw data to processed data.
- Database read/write behavior.
- Feature generation to prediction.
- Model artifact loading.
- API endpoint contracts.
- Forecast to inventory recommendation.

### Regression tests

Use a small deterministic fixture to detect unintended changes in:

- Feature columns.
- Row counts.
- Forecast values within a justified tolerance.
- Evaluation metrics.
- API response structure.

### Test quality

- Test behavior, not private implementation details.
- Include happy paths, edge cases, and expected failures.
- Keep fixtures small and readable.
- Do not make unit tests depend on external services.
- Do not weaken or delete a failing test merely to make the build pass.

---

## 18. Code Quality Standards

- Use type hints for public functions and complex internal functions.
- Write concise docstrings describing purpose, inputs, outputs, and important assumptions.
- Keep functions focused on one responsibility.
- Prefer pure functions for transformations and calculations.
- Avoid hidden global state.
- Avoid mutable default arguments.
- Use vectorized dataframe operations where they remain readable.
- Do not optimize before profiling.
- Use meaningful domain names rather than generic names such as `data2` or `result_final`.
- Use timezone-aware timestamps.
- Pin or lock dependencies for reproducible environments.
- Run the project's formatter, linter, type checker, and tests before completion.

Suggested quality checks when supported by the repository:

```bash
ruff check .
ruff format --check .
mypy src
pytest -q
```

Do not introduce a new tool solely for appearance if the repository already has an established equivalent.

---

## 19. Pipeline Reliability

Every scheduled job should be:

- **Idempotent:** rerunning it does not duplicate or corrupt results.
- **Observable:** it records status, duration, counts, and failures.
- **Recoverable:** a failed run can be retried safely.
- **Versioned:** outputs identify data, code, and model versions.
- **Atomic where needed:** consumers do not observe partially written results.

Prefer writing results to a staging table or temporary artifact, validating them, and then publishing atomically.

Store a pipeline-run record with:

- Run ID.
- Job name.
- Start and end timestamps.
- Status.
- Input and output row counts.
- Data cutoff date.
- Model version.
- Error category when failed.

---

## 20. Model and Data Monitoring

Monitor three layers:

### System monitoring

- API latency and error rate.
- Pipeline duration and failure rate.
- Database availability.
- Prediction freshness.

### Data monitoring

- Missing columns and invalid types.
- Missing-value rates.
- Volume changes.
- Unseen categories.
- Feature distribution drift.
- Late-arriving data.

### Model monitoring

- MAE, WAPE, RMSE, and bias after actuals arrive.
- Error by store, product, category, and horizon.
- Prediction distribution drift.
- Stockout and overstock outcomes.
- Performance relative to the naive baseline.

Retraining must be triggered by a documented schedule or evidence-based threshold, not automatically on every minor metric fluctuation.

---

## 21. Security and Privacy

- Use least-privilege database credentials.
- Do not commit credentials or private datasets.
- Sanitize filenames and validate uploaded files.
- Parameterize database queries.
- Restrict administrative endpoints.
- Avoid exposing internal paths, stack traces, SQL statements, or dependency details in API errors.
- Do not log personal or commercially sensitive information unless required and approved.
- Scan dependencies and container images when the project reaches deployment.

---

## 22. Documentation Requirements

Keep `README.md` current with:

- Business problem and users.
- Architecture.
- M5 dataset provenance, source links, required files, and license/access notes.
- Development subset selection and full-scale target.
- Wide-to-long transformation and canonical schema.
- Clear separation between M5 facts and simulated inventory assumptions.
- Local setup.
- Configuration variables.
- Database setup and migrations.
- Training and evaluation commands.
- API and dashboard startup commands.
- Test commands.
- Model results versus baselines.
- Known limitations.
- Screenshots or a public demo link when available.

Use model documentation to describe training data, intended use, limitations, evaluation periods, metrics, and failure modes.

---

## 23. Incremental Delivery Plan

Work in this order unless the user requests otherwise:

### Phase 1: Foundation

- Create project structure and environment.
- Define configuration and logging.
- Define schemas and custom exceptions.
- Add a small deterministic M5-shaped fixture containing sales, calendar, and prices.
- Define dataset manifest and development-subset configuration.

### Phase 2: Data pipeline

- Ingest the three required M5 data files.
- Validate raw schemas, keys, day coverage, and source hashes.
- Transform wide daily sales into canonical long form in bounded partitions.
- Join calendar, events, SNAP eligibility, and weekly prices without changing row grain.
- Produce a typed, partitioned analysis-ready dataset.
- Add unit and integration tests.

### Phase 3: EDA and baselines

- Analyze M5 demand patterns, intermittent demand, price coverage, events, and hierarchy.
- Implement naive baselines.
- Establish rolling-origin evaluation and the protected `d_1914`-`d_1941` holdout.

### Phase 4: ML forecasting

- Build leakage-safe features.
- Train candidate models.
- Run rolling backtests.
- Select and version the model.

### Phase 5: Inventory optimization

- Create a deterministic, versioned inventory simulation layer.
- Implement lead-time demand and safety stock.
- Add order constraints.
- Produce explainable recommendations.
- Label all inventory values and operational outcomes as simulated.

### Phase 6: Product interfaces

- Build FastAPI endpoints.
- Build the Streamlit dashboard.
- Add API and integration tests.

### Phase 7: Deployment and operations

- Add Docker and PostgreSQL orchestration.
- Add CI quality gates.
- Deploy the application.
- Add monitoring and retraining rules.

Each phase must leave the repository runnable and tested.

---

## 24. Definition of Done

A task is complete only when:

1. The requested behavior is implemented.
2. Data assumptions and business rules are explicit.
3. Errors fail clearly and safely.
4. Appropriate logs are emitted without sensitive information.
5. Tests cover the main behavior and relevant edge cases.
6. Relevant tests, formatting, linting, and type checks pass.
7. Documentation is updated.
8. The change does not introduce target leakage.
9. Outputs are reproducible and version-identifiable.
10. The agent reports verification results and remaining limitations.

Do not claim a task is production-ready when tests were not run, dependencies were unavailable, data assumptions remain unverified, or deployment was not actually validated.

---

## 25. Agent Completion Report

At the end of each implementation task, respond with:

```text
Outcome
- What now works.

Key changes
- Important files and behavior changed.

Verification
- Commands or checks run and their results.

Assumptions and limitations
- Any unverified data semantics, shortcuts, or remaining risks.

Next recommended step
- The smallest useful continuation.
```

Keep this report factual and concise. Never state that checks passed unless they were actually executed.
