Act as a senior data scientist and ML engineer. Perform a complete, reproducible exploratory data analysis for our **AI Sales Forecasting and Inventory Optimizer** using the **M5 Forecasting – Accuracy** dataset.

Before making changes, read `CONTEXT.md` completely and inspect the existing repository. Follow its architecture, logging, validation, exception-handling, testing, reproducibility, and data-leakage requirements.

## Objective

Analyze the M5 dataset to determine:

1. Whether the data is suitable for demand forecasting.
2. What trends, seasonality and demand patterns exist.
3. How demand differs between stores, states, categories, departments and products.
4. How prices, calendar events and SNAP-eligible days relate to sales.
5. How much intermittent and zero demand exists.
6. What data-quality problems must be resolved.
7. Which features should be considered during feature engineering.
8. Which forecasting baselines and modeling approaches should be tested later.

Do not train the final machine-learning model during this task. This task is specifically for data understanding and EDA.

## M5 source files

Use the original files under `data/raw/m5/`:

* `sales_train_evaluation.csv`
* `calendar.csv`
* `sell_prices.csv`

Use `sample_submission.csv` only if it is useful for understanding the original competition output format.

Do not modify the raw files.

## Scope

Use the deterministic development subset defined in project configuration:

* Exactly 2 stores.
* Between 50 and 100 products.
* At least 2 years of historical observations.
* A mixture of categories, departments, sales volumes and intermittent-demand patterns.

If the subset has not been configured, create an explicit configuration containing:

* Selected store IDs.
* Selected product IDs or a deterministic selection rule.
* Start and end dates.
* Random seed.
* Selection justification.

Do not silently select a different subset between runs.

Use only data up to `d_1913` for exploratory analysis and development decisions. Keep `d_1914` through `d_1941` protected as the final local holdout. Do not plot, summarize or use holdout target values to make feature or modeling decisions.

## Engineering requirements

Reuse the existing production modules wherever possible:

* `ingestion.py` for safely loading the raw CSV files.
* `transformation.py` for converting sales from wide to long format and joining calendar and price data.
* `validation.py` for enforcing the canonical data contract.

Do not duplicate production transformation logic inside the notebook.

Use proper logging instead of `print()` in production modules. Log:

* Input files.
* Selected stores and products.
* Input and output row counts.
* Date coverage.
* Missing values.
* Duplicate counts.
* Transformation duration.
* Output locations.

Use specific exception types and fail clearly when required files, columns or joins are invalid. Do not use bare `except:` or silently return empty dataframes.

The complete M5 dataset can produce tens of millions of long-form rows. Avoid melting the entire dataset unnecessarily. Filter the wide sales table to the selected stores and products before melting, use explicit dtypes and avoid unnecessary dataframe copies.

## Canonical dataset

The analysis-ready dataset should have one row per:

```text
date × store_id × product_id
```

It should contain, where applicable:

```text
date
day_id
week_id
store_id
product_id
department_id
category_id
state_id
units_sold
sell_price
event_name_1
event_type_1
event_name_2
event_type_2
snap_eligible_day
```

Do not rename SNAP eligibility as a generic promotion.

## Required data-quality analysis

Investigate and report:

1. Whether all required columns exist.
2. Date and `day_id` coverage.
3. Number of stores, products, departments and categories.
4. Duplicate `(date, store_id, product_id)` records.
5. Negative or impossible sales values.
6. Missing calendar joins.
7. Missing price values and their patterns.
8. Duplicate price keys for `(store_id, product_id, week_id)`.
9. Store-to-state consistency.
10. Products with incomplete selling histories.
11. Products introduced late in the dataset.
12. Long consecutive periods of zero sales.
13. Unexpected gaps created during transformation.
14. Row counts before and after every major transformation.

Preserve explicit M5 zero-sales observations. Do not treat failed joins or missing records as zero sales.

Explain whether missing prices appear before product introduction, after product discontinuation or within active selling periods. Do not automatically forward-fill prices without evidence.

## Required exploratory analysis

### 1. Dataset overview

Report:

* Date range.
* Number of observations.
* Number of stores and states.
* Number of products.
* Number of departments and categories.
* Number of unique product-store series.
* Memory usage of the processed subset.
* Number and percentage of zero-sales observations.
* Number and percentage of missing prices.

### 2. Target distribution

Analyze `units_sold` using:

* Summary statistics.
* Histogram on the original scale.
* Histogram using `log1p(units_sold)`.
* Box plots by category and store.
* Relevant percentiles.
* Identification of extreme demand values.

Do not automatically delete outliers. Explain whether they could represent promotions, events, seasonality or genuine high-demand periods.

### 3. Sales over time

Visualize and analyze:

* Total daily sales.
* Weekly sales.
* Monthly sales.
* Seven-day and twenty-eight-day rolling averages.
* Demand trends by store.
* Demand trends by category.
* Demand trends by department.

Discuss trend changes, recurring patterns, unusual peaks and periods of low demand.

### 4. Seasonality

Investigate:

* Day-of-week patterns.
* Week-of-year patterns.
* Monthly patterns.
* Weekend versus weekday demand.
* Annual seasonality when enough history exists.
* Autocorrelation at lags 1, 7, 14 and 28.

Explain which lag and rolling-window features appear justified by the findings.

### 5. Store and product hierarchy

Compare:

* States.
* Stores.
* Categories.
* Departments.
* High-, medium- and low-volume products.
* High- and low-volatility product-store series.

Identify whether one global model appears reasonable or whether strong differences may require store, category or segment-specific treatment.

### 6. Intermittent demand

Measure for each product-store series:

* Percentage of zero-sales days.
* Average interval between non-zero sales.
* Length of the longest zero-sales run.
* Mean and standard deviation of non-zero demand.
* Coefficient of variation where meaningful.

Create understandable demand segments such as:

* Regular demand.
* Intermittent demand.
* Highly intermittent demand.
* Recently introduced product.
* Potentially discontinued product.

Document the segmentation rules instead of assigning subjective labels manually.

### 7. Price analysis

Investigate:

* Price distribution by category and store.
* Price changes over time.
* Number of price changes per product.
* Relationship between price and units sold.
* Demand before, during and after major price reductions.
* Missing-price patterns.

Any derived discount feature must use a documented reference price, such as a trailing historical median. Do not use future prices to calculate a historical discount feature.

Do not claim that correlation proves price causation.

### 8. Calendar events and SNAP

Analyze:

* Sales on event versus non-event days.
* Sales around major event windows.
* Event effects by category.
* SNAP-eligible versus non-SNAP days for the appropriate state.
* Interaction between store state and SNAP indicator.

Do not interpret SNAP eligibility as a normal retail promotion.

### 9. Representative series

Select several clearly documented product-store examples:

* High-volume regular demand.
* Low-volume intermittent demand.
* Highly seasonal demand.
* High-volatility demand.
* Product with significant price movement.
* Product with substantial missing-price history.

Plot each series and explain why it represents that behavior.

### 10. Forecasting implications

Based on evidence from the EDA, recommend:

* Appropriate lag features.
* Rolling-window features.
* Calendar features.
* Price features.
* Categorical features.
* Potential demand segmentation.
* Suitable naive baselines.
* Suitable evaluation metrics.
* Potential modeling risks.
* Data-quality issues requiring resolution before training.

Distinguish evidence-based recommendations from hypotheses that still need backtesting.

## Required outputs

Create or update:

```text
notebooks/01_eda.ipynb
reports/eda_report.md
reports/figures/
```

The notebook should be readable from top to bottom and reproducible from a clean kernel.

The Markdown report should include:

1. Executive summary.
2. Dataset and subset description.
3. Data-quality findings.
4. Demand patterns.
5. Seasonality findings.
6. Store and product comparisons.
7. Intermittent-demand findings.
8. Price and event findings.
9. Modeling implications.
10. Limitations.
11. Recommended next steps.

Save important figures using clear filenames. Do not save every experimental chart.

If reusable analysis logic is required, place it in an importable module such as:

```text
src/sales_optimizer/analysis/eda.py
```

Do not place reusable business logic only inside the notebook.

## Visualisation standards

Every chart must have:

* A descriptive title.
* Labelled axes.
* Units.
* A readable legend when needed.
* Appropriate date formatting.
* A concise interpretation in the notebook or report.

Avoid decorative charts, unreadable plots containing hundreds of series and charts that repeat the same information.

## Testing

Add or update tests for any production code changed during this task.

At minimum, verify:

* Subset selection is deterministic.
* The protected holdout is excluded.
* Wide-to-long transformation preserves expected sales totals.
* Calendar joins do not change the intended row count.
* Canonical keys are unique.
* Negative sales are rejected.
* State-specific SNAP selection is correct.
* Price joins use the correct store-product-week keys.

Use small M5-shaped fixtures for tests. Unit tests must not require the complete dataset.

## Completion criteria

The task is complete only when:

1. The notebook runs from start to finish.
2. The EDA report is generated.
3. Important figures are saved.
4. Raw files remain unchanged.
5. The protected holdout remains unused.
6. Data-quality problems are documented.
7. Findings are supported by actual calculations and plots.
8. Relevant tests pass.
9. Formatting and linting checks pass where configured.
10. No claim is made about a check that was not actually executed.

Finish with a concise report containing:

```text
Outcome
- What was completed.

Key findings
- The most important evidence from the EDA.

Files changed
- Files created or modified.

Verification
- Commands executed and their results.

Assumptions and limitations
- Unverified interpretations or dataset limitations.

Next recommended step
- The smallest useful task after EDA.
```
