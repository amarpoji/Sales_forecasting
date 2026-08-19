# Feature Engineering Report

## AI Sales Forecasting and Inventory Optimizer

This report explains the feature-engineering work completed in `03_feature_engineering.ipynb`. It describes what each feature means, why it may help forecasting, and how the pipeline prevents information from the future leaking into model training.

## 1. Objective

The goal is to predict daily unit sales for each product-store series over a **28-day forecast horizon**.

The development subset contains:

- 47 products;
- 2 stores: `CA_1` and `CA_3`;
- 94 product-store series;
- daily observations from `d_1` to `d_1913`;
- a protected 28-day holdout from `d_1914` to `d_1941`.

Feature engineering converts the original sales table into useful signals that a machine-learning model can learn from. The final features describe four broad questions:

1. **When is the forecast date?**
2. **Is there an event or SNAP programme on or near that date?**
3. **What was demand like before the forecast began?**
4. **What is happening to the product's price?**

## 2. Central Strategy: Forecast Safety

### The problem

Suppose the model must forecast the next 28 days from one forecast origin. When it predicts forecast day 20, the actual sales from forecast days 1 to 19 will not yet be known.

Using those values as features during validation would make the model appear better than it could be in real use. This is called **target leakage**.

### The solution

All demand-derived features obey a 28-day safety gap:

- the shortest exact demand lag is 28 days;
- rolling-demand calculations shift sales by 28 days before calculating statistics;
- no demand from inside the forecast horizon is used as a predictor.

For a row representing day `t`:

- `lag_28` uses demand from `t - 28`;
- the forecast-safe 14-day mean uses demand from `t - 41` through `t - 28`;
- the forecast-safe 56-day mean uses demand from `t - 83` through `t - 28`.

Calendar, event, SNAP, and planned-price information are different. They may describe the forecast date itself because they are treated as information known before forecasting.

## 3. Calendar Features

Calendar features tell the model where a date sits within familiar time cycles.

### Basic calendar components

The notebook creates features such as:

- year;
- month;
- quarter;
- day of month;
- day of week;
- week of year;
- day of year;
- weekend indicator;
- month-start and month-end indicators;
- continuous time index.

### Intuition

Our EDA showed a strong weekly pattern. Saturday and Sunday demand was substantially higher than midweek demand. A `day_of_week` or `is_weekend` feature allows the model to learn this directly.

Month and day-of-year features help represent annual seasonality. For example, demand was generally stronger from June to September and weakest in January.

The continuous time index helps the model recognise gradual long-term changes rather than treating 2011 and 2016 as identical periods.

### Cyclical encoding

The notebook also creates sine and cosine versions of weekday, month, and day of year.

These features represent the fact that time cycles wrap around:

- Sunday is close to Monday;
- December is close to January;
- the end of one year is close to the beginning of the next.

Without cyclical encoding, ordinary numbers make December and January look far apart even though they are adjacent.

## 4. Event and SNAP Features

The M5 calendar supplies event names, event types, and California SNAP indicators.

Features include:

- first and second event names;
- first and second event types;
- whether any event occurs;
- number of events on the date;
- whether the date is Christmas;
- whether California SNAP benefits are active.

### Intuition

Events can change shopping behaviour. Some may increase demand, while closures or unusual trading days may sharply reduce it.

Christmas was particularly important in the EDA. Total demand was nearly zero on several Christmas dates. A general weekday feature cannot explain that behaviour because Christmas moves across weekdays. The explicit event information gives the model a way to recognise it.

SNAP days also showed higher average demand than non-SNAP days, so the `snap_CA` feature may help explain recurring demand changes associated with benefit availability.

## 5. Event-Proximity Features

An event may influence demand before or after the event itself. The notebook therefore adds:

- days since the most recent event;
- days until the next event;
- event within the previous seven days;
- event within the next seven days;
- days since Christmas;
- days until Christmas;
- within seven days before Christmas;
- within seven days after Christmas.

### Intuition

Customers may buy early in preparation for a holiday, delay shopping until after an event, or change behaviour during the surrounding week. An event-day flag alone cannot capture these effects.

The Christmas proximity features are especially useful because they distinguish the normal pre-Christmas period, the closure-like Christmas effect, and the recovery period afterward.

These features are forecast-safe because event dates are published calendar information and do not depend on future sales.

## 6. Exact Demand Lags

The exact lag features are:

- `units_sold_lag_28`;
- `units_sold_lag_35`;
- `units_sold_lag_42`;
- `units_sold_lag_56`.

### Intuition

A lag asks a simple question: **How many units did this same product in this same store sell a fixed number of days ago?**

All chosen lags are multiples of seven, so they preserve the weekday relationship. For example, a Saturday forecast is compared with earlier Saturdays.

The EDA showed that Foods benefited particularly from the exact lag-28 relationship. Food demand is relatively smooth and strongly connected to repeated weekly shopping behaviour.

No lag shorter than 28 days is included in the direct 28-day forecasting design. A lag of 7 or 14 would be unavailable for some forecast dates unless the system recursively used its own earlier predictions.

## 7. Forecast-Safe Rolling Demand Features

Rolling means and standard deviations are calculated over windows of:

- 7 days;
- 14 days;
- 28 days;
- 56 days.

Before each calculation, sales are shifted by the full 28-day forecast horizon.

### Rolling mean

The rolling mean represents the recent demand level before the forecast window.

It smooths individual spikes and zero-sales days. This is helpful for noisier series where one exact lag may not represent normal demand.

The baseline investigation found that the recent 14-day mean was the strongest simple overall benchmark. That result supports including forecast-safe rolling averages in the machine-learning feature set.

### Rolling standard deviation

The rolling standard deviation describes how variable demand was during the historical window.

Two products may have the same average demand but behave differently:

- one may sell close to 10 units every day;
- another may alternate between 0 and 20 units.

Their rolling means are similar, but their rolling standard deviations are very different. This helps the model distinguish stable and volatile series.

### Why use several windows?

- 7 days reacts quickly to recent changes;
- 14 days balances recency and stability;
- 28 days represents approximately one month;
- 56 days provides a more stable long-term demand level.

The model can decide which window is most useful for each product, store, category, and forecast situation.

## 8. Price Features

The price feature group includes:

- filled selling price;
- original price-missing indicator;
- absolute price change;
- percentage price change;
- 28-day reference price;
- price index relative to the reference;
- discount percentage from the reference;
- price-increase indicator;
- price-decrease indicator;
- below-reference-price indicator;
- days since the latest price change.

### Missing-price treatment

EDA found 966 missing-price rows, representing only 0.54% of the dataset. They occurred before the first recorded positive sale, and no positive-sales row had a missing price.

The notebook therefore:

1. keeps a `price_was_missing` indicator;
2. fills the price within each product-store series;
3. avoids using sales values to perform the fill.

The indicator preserves the information that the original price was unavailable.

### Price changes

Absolute and percentage changes tell the model whether the current price differs from the previous available daily price.

The direction indicators make the signal easier to interpret:

- `is_price_increase = 1` means the price rose;
- `is_price_decrease = 1` means the price fell.

### Reference price and price index

The 28-day reference price is the median of the preceding 28 price observations.

The price index is:

`current price / reference price × 100`

Interpretation:

- 100 means the price matches its recent reference;
- below 100 means it is cheaper;
- above 100 means it is more expensive.

Discount depth expresses how far the price is below its recent reference. This is more comparable across products than an absolute price reduction because a RM0.50 reduction has a different meaning for a RM1 product and a RM10 product.

### Days since price change

This feature distinguishes a new price change from a long-established price level. A price reduction introduced today may behave differently from the same price after several months.

### Operational assumption

These current-date price features assume future selling prices are known or planned for the 28-day forecast horizon, as in the M5 data. In a real deployment where future prices are unknown, the system must either:

- receive the planned future price schedule;
- run alternative price scenarios; or
- omit features that require future prices.

## 9. Warm-Up Strategy

The longest historical calculation needs:

- a 28-day forecast-safety shift; and
- a 56-day rolling window.

Therefore, the first:

`28 + 56 - 1 = 83 days`

of each series do not have every required demand-history feature.

These rows are removed from model training instead of artificially filling historical demand features. This leaves:

- 1,830 usable days per series;
- 94 series;
- 172,020 modelling rows.

Removing the warm-up rows gives the model a clean dataset in which every selected feature is available.

## 10. Feature Validation Strategy

The notebook performs several checks before saving the dataset.

### Structural checks

- every requested feature column exists;
- feature names are unique;
- every product-store-date combination is unique;
- all 94 series have equal usable date coverage;
- the final row count matches the expected calculation.

### Numerical checks

- the target contains no missing or negative values;
- model features contain no missing values after warm-up removal;
- numerical features contain no infinite values;
- binary features contain only zero and one;
- filled prices are positive.

### Leakage checks

- demand lags start at 28 days;
- rolling demand is shifted by 28 days;
- a direct test confirms that `lag_28` matches the observation exactly 28 days earlier;
- the maximum development day remains `d_1913`;
- `d_1914` to `d_1941` remain excluded.

### Persistence checks

After saving the Parquet dataset and JSON manifest, the notebook reloads them and confirms:

- the row count is unchanged;
- the column order is unchanged;
- the manifest matches the selected feature list;
- the protected holdout is still absent.

## 11. Final Modelling Dataset

The finished feature dataset is saved as:

`data/processed/features/development_features.parquet`

The feature definition is saved as:

`data/processed/features/feature_manifest.json`

The manifest records the target, series keys, categorical features, numerical features, forecast horizon, warm-up period, and holdout boundaries. This ensures that later notebooks use the same feature contract.

## 12. Overall Modelling Strategy

The project now follows this sequence:

1. **EDA:** understand data quality, demand behaviour, seasonality, events, prices, and series differences.
2. **Baseline validation:** establish a realistic performance benchmark using five 28-day rolling-origin folds.
3. **Feature engineering:** create forecast-safe explanatory variables without touching the final holdout.
4. **Machine-learning validation:** train models using the same rolling-origin logic and compare them with the recent 14-day mean baseline.
5. **Holdout evaluation:** use `d_1914` to `d_1941` only after model and hyperparameter decisions are complete.

The primary baseline to beat is the **recent 14-day mean**, which achieved approximately:

- MAE: 3.755 units;
- RMSE: 5.729 units;
- WAPE: 39.545%;
- bias: -1.455%.

The recent 28-day mean remains a useful secondary benchmark because it performed almost as well and had lower overall bias.

## 13. Next Step

The next notebook should be:

`04_model_training.ipynb`

It should:

1. load the saved feature dataset and manifest;
2. reproduce the five rolling-origin folds;
3. train the first gradient-boosted tree model;
4. handle categorical features consistently;
5. evaluate MAE, RMSE, WAPE, and bias;
6. compare every fold directly with the recent 14-day mean baseline;
7. inspect performance by store, category, demand pattern, and forecast horizon;
8. leave the protected holdout untouched.

The feature-engineering phase is complete when all notebook checks pass and both saved artifacts reload successfully.
