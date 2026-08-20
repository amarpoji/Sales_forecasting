# AI Sales Forecasting Project — Final Report

## Executive conclusion

The forecasting experiment is complete. The selected **LightGBM Poisson — flexible** model passed the protected 28-day holdout evaluation and is accepted as the final forecasting model for this project subset.

On 2,632 completely protected forecasts, the selected model achieved:

| Metric | LightGBM | Recent 14-day baseline | Improvement |
| --- | ---: | ---: | ---: |
| MAE | **3.345** | 3.629 | 7.83% |
| RMSE | **4.968** | 5.566 | 10.74% |
| WAPE | **32.693%** | 35.468% | 2.775 points, 7.824% relative |
| Bias | **-0.727%** | -2.978% | closer to zero |

The model predicted 26,736.279 units against 26,932 actual units. Its total underforecast was therefore small: approximately 196 units, or 0.727%.

The final prediction file was generated before the protected targets were opened. Its SHA-256 fingerprint remained unchanged throughout evaluation:

`2c99f87fd6e89eb7d9604466e18b2368cdba695b83fcd3bab2569dbe13f3125c`

## 1. Business objective

The project developed a 28-day unit-sales forecasting system for a controlled subset of the M5 retail dataset. The forecasts are intended to support later inventory-planning decisions by estimating daily demand for each product-store combination.

The modeling grain is:

> One daily unit-sales forecast for one product in one store.

The project subset contains:

- 47 products;
- two California stores: CA_1 and CA_3;
- 94 product-store series;
- three categories: Foods, Hobbies, and Household;
- five departments;
- development history through `d_1913`;
- a protected 28-day holdout from `d_1914` through `d_1941`.

## 2. Data-quality and exploratory findings

The development EDA contained 179,822 rows: 94 series multiplied by 1,913 days. It passed the principal integrity checks:

- no duplicate rows;
- no duplicate date-store-product combinations;
- no missing calendar dates;
- every series contained all 1,913 expected development dates;
- no negative or non-finite sales;
- no zero, negative, or infinite available prices;
- no protected holdout rows in the EDA dataset.

Only 966 sell-price values were missing, representing 0.54% of development rows. All occurred before the first recorded sale for the affected series. None occurred with positive demand or inside the active-sales window.

Daily series-level demand was right-skewed:

- mean: 10.998 units;
- median: 7 units;
- 99th percentile: 65 units;
- maximum: 151 units;
- skewness: 2.838;
- zero-sales observations: 7.51%.

The top 1.04% of observations accounted for 7.52% of total units, showing that occasional high-demand days matter but do not dominate the complete dataset.

## 3. Demand structure

The 94 series were classified using average demand interval and squared coefficient of variation:

| Pattern | Series | Share |
| --- | ---: | ---: |
| Smooth | 75 | 79.79% |
| Erratic | 11 | 11.70% |
| Intermittent | 5 | 5.32% |
| Lumpy | 3 | 3.19% |

Most Foods series were smooth, while Hobbies contained a much larger proportion of erratic and lumpy demand. This later appeared in model evaluation: Hobbies remained the hardest category to forecast.

Demand also had strong calendar structure. Average weekend demand was substantially above the overall daily average:

- Saturday demand index: 122.27;
- Sunday demand index: 124.19;
- Wednesday demand index: 85.12, the lowest weekday level.

Monthly demand peaked in August with an index of 112.93. January was lowest at 88.48. Both stores moved together, with a raw daily-sales correlation of 0.801 and a 28-day rolling correlation of 0.780. After ordinary weekday effects were removed, the correlation remained 0.668, indicating shared demand movement beyond the weekly cycle.

## 4. Baseline experiment

Five rolling-origin validation folds were used. Each fold forecast the next 28 days for all 94 series, producing:

- 2,632 predictions per fold;
- 13,160 predictions across all folds.

The candidate baselines were:

- recent 7-day mean;
- recent 14-day mean;
- recent 28-day mean;
- repeated last-week pattern;
- seasonal naïve lag 28.

The recent 14-day mean was selected as the strongest overall benchmark:

| Baseline | MAE | RMSE | WAPE | Bias |
| --- | ---: | ---: | ---: | ---: |
| Recent 14-day mean | **3.755** | **5.729** | **39.545%** | -1.455% |
| Recent 28-day mean | 3.783 | 5.793 | 39.839% | -0.489% |
| Recent 7-day mean | 3.837 | 5.815 | 40.414% | -0.765% |
| Repeated last-week pattern | 4.511 | 6.768 | 47.511% | -0.765% |
| Seasonal naïve lag 28 | 4.664 | 7.135 | 49.125% | -0.489% |

The averaging baselines performed better than exact-pattern repetition because averaging reduced daily noise. The recent 14-day mean offered the best balance between recency and stability.

## 5. Forecast-safe feature engineering

The feature dataset contained 172,020 rows from `d_84` through `d_1913`, with 64 model features: 10 categorical and 54 numerical.

The first 83 days were used as warm-up history. This was required by the longest feature: a 56-day rolling statistic shifted backward by the 28-day forecast horizon. The earliest valid row therefore requires 83 earlier positions.

The features included:

- product, department, category, store, and state identity;
- weekday, month, quarter, annual position, and cyclical encodings;
- events, event proximity, Christmas proximity, and SNAP status;
- exact demand lags at 28, 35, 42, and 56 days;
- rolling demand means and standard deviations over 7, 14, 28, and 56 days;
- current and historical price context;
- price-change direction and magnitude;
- a 28-day reference price and time since the latest change.

Demand rolling windows were shifted by 28 days before calculation. Thus, all features for every day in a 28-day forecast use only demand known before the forecast begins.

The price reference was verified during holdout reconstruction as:

> The median available price over the previous 28 days, excluding the current day.

This definition is robust to brief price movements and was reproduced exactly: every reconstructed price feature matched the stored development feature with zero difference.

## 6. Machine-learning model

LightGBM was chosen because it can model nonlinear interactions among recent demand, product identity, calendar context, events, and price while handling categorical features efficiently.

The Poisson objective was used because daily units sold are non-negative counts.

The development validation design used five outer rolling-origin folds:

| Fold | Training ends | Validation period |
| ---: | ---: | --- |
| 1 | `d_1773` | `d_1774`–`d_1801` |
| 2 | `d_1801` | `d_1802`–`d_1829` |
| 3 | `d_1829` | `d_1830`–`d_1857` |
| 4 | `d_1857` | `d_1858`–`d_1885` |
| 5 | `d_1885` | `d_1886`–`d_1913` |

The latest 28 days inside each outer training period were used for early stopping. After selecting the iteration count, the model was retrained on the complete outer training period and evaluated on the untouched outer validation window.

## 7. Initial model result

The first Poisson LightGBM already passed the main development test:

| Model | MAE | RMSE | WAPE | Bias |
| --- | ---: | ---: | ---: | ---: |
| Initial LightGBM | **3.301** | **4.914** | **34.769%** | -1.778% |
| Recent 14-day mean | 3.755 | 5.729 | 39.545% | -1.455% |

LightGBM beat the baseline in all five validation folds, both stores, all three categories, and all four forecast weeks.

## 8. Controlled tuning and model selection

Only three configurations were compared to limit validation overfitting:

| Configuration | MAE | RMSE | WAPE | Bias |
| --- | ---: | ---: | ---: | ---: |
| Flexible | **3.292** | **4.898** | **34.675%** | **-1.055%** |
| Current | 3.301 | 4.914 | 34.769% | -1.778% |
| Compact | 3.308 | 4.913 | 34.836% | -1.323% |

The flexible configuration won four of five folds. It also had the best aggregate metrics and lowest WAPE standard deviation. The compact model won the fifth fold by a narrow margin.

The flexible model was therefore locked with:

- Poisson objective;
- learning rate 0.03;
- 63 leaves;
- minimum child samples 50;
- row subsampling 0.80;
- column subsampling 0.90;
- L1 regularization 0.20;
- L2 regularization 2.00;
- final boosting duration determined by early stopping.

No additional tuning was performed after selection.

## 9. What the model learned

Gain-based feature importance was dominated by recent demand estimates:

| Feature | Mean gain share |
| --- | ---: |
| 28-day rolling mean | 32.510% |
| 56-day rolling mean | 19.156% |
| 14-day rolling mean | 18.930% |
| 7-day rolling mean | 9.004% |
| Product identity | 7.224% |
| Lag 28 | 3.026% |
| Day of week | 1.361% |

The four rolling means contributed approximately 79.6% of total gain. Intuitively, the model first estimates the normal recent demand level and then adjusts it using product identity, exact lags, weekday, seasonality, events, and price context.

Feature importance describes predictive usage, not causality. It does not prove that changing a feature will cause demand to change.

## 10. Prediction-first protected evaluation

The holdout evaluation followed a strict sequence:

1. The locked model and metadata were loaded.
2. A target-free grid of 94 series × 28 days was constructed.
3. Calendar, demand, and price features were reproduced.
4. All 64 model features and categorical levels were validated.
5. Exactly 2,632 finite, non-negative predictions were generated.
6. Predictions were saved and fingerprinted.
7. Only then were the actual `d_1914`–`d_1941` sales opened.
8. The fingerprint was verified again after evaluation.

The prediction range was 1.096 to 86.580 units.

## 11. Final holdout result

| Metric | Cross-validation | Protected holdout |
| --- | ---: | ---: |
| LightGBM WAPE | 34.675% | **32.693%** |
| Baseline WAPE | 39.545% | 35.468% |
| LightGBM improvement, points | 4.870 | 2.775 |
| Relative LightGBM improvement | 12.315% | 7.824% |

Both models performed better on the holdout than their cross-validation averages, suggesting that this holdout period was somewhat easier. LightGBM's relative advantage narrowed, but remained meaningful and consistent with genuine generalization.

## 12. Holdout performance by store

| Store | LightGBM WAPE | Baseline WAPE | Relative improvement | LightGBM bias |
| --- | ---: | ---: | ---: | ---: |
| CA_1 | **33.700%** | 37.974% | 11.255% | +0.955% |
| CA_3 | **31.990%** | 33.717% | 5.124% | -1.902% |

The model won in both stores. CA_1 showed the larger gain and a substantial correction of the baseline's -4.983% bias. CA_3 remained more accurate overall but received a smaller relative improvement.

## 13. Holdout performance by category

| Category | LightGBM WAPE | Baseline WAPE | Relative improvement | LightGBM bias |
| --- | ---: | ---: | ---: | ---: |
| Foods | **28.155%** | 30.946% | 9.020% | -1.764% |
| Hobbies | **71.466%** | 75.126% | 4.871% | +5.210% |
| Household | **45.441%** | 47.756% | 4.848% | +3.374% |

The model won in all three categories. Foods was the strongest and most commercially reliable category. Hobbies remained difficult because of its low-volume, erratic, intermittent, and lumpy series. Its +5.210% bias should be monitored even though it was far better than the baseline's +19.972% bias.

## 14. Final acceptance checks

Every final check passed:

| Check | Result |
| --- | --- |
| Lower WAPE than baseline | Passed |
| Lower MAE than baseline | Passed |
| Lower RMSE than baseline | Passed |
| Absolute overall bias below 5% | Passed |
| WAPE no worse than the worst CV fold | Passed |
| Finite, non-negative predictions | Passed |
| Correct prediction count | Passed |
| Frozen prediction fingerprint unchanged | Passed |

## 15. Final decision

**LightGBM Poisson — flexible is accepted as the final model for this project subset.**

The result is supported by:

- improvement over the strongest baseline in cross-validation;
- wins in all five original LightGBM-versus-baseline validation folds;
- controlled tuning rather than an extensive search;
- exact, forecast-safe feature reconstruction;
- a prediction-first protected holdout evaluation;
- lower holdout MAE, RMSE, and WAPE;
- low overall holdout bias;
- wins in both stores and all three categories;
- unchanged frozen-prediction fingerprint.

## 16. Limitations

The accepted result applies to this controlled subset, not automatically to the entire M5 hierarchy or a different retailer.

Important limitations include:

- only 47 products and two stores were modeled;
- the holdout contains one 28-day period;
- Hobbies accuracy remains weak despite improvement;
- prices are predictive context, not causal promotion estimates;
- inventory cost, lead time, service level, and stock availability were not part of this forecasting experiment;
- prediction intervals were not yet produced;
- the model has not yet been tested in a live recurring forecasting process.

## 17. Recommended next phase

Model experimentation should stop here. The next phase is operationalization:

1. Package the exact feature pipeline used in training and holdout evaluation into reusable functions.
2. Add automated schema, leakage, row-count, missing-value, and category-level checks.
3. Produce a standard 28-day forecast table for every product-store series.
4. Add prediction intervals or empirical uncertainty estimates.
5. Connect forecasts to inventory rules using lead time, safety stock, service-level targets, minimum order quantities, and holding/stockout costs.
6. Monitor WAPE, bias, and data drift by store, category, series, and horizon after every forecast cycle.
7. Establish a retraining policy rather than retraining automatically after every new day.

The immediate technical notebook after this completed experiment should focus on inference packaging and reproducibility, not further tuning.

## 18. Project status

| Stage | Status |
| --- | --- |
| Data preparation | Complete |
| Exploratory data analysis | Complete |
| Baseline forecasting | Complete |
| Feature engineering | Complete |
| LightGBM training | Complete |
| Controlled tuning | Complete |
| Protected holdout evaluation | Complete |
| Final model acceptance | Complete |
| Inference pipeline | Next phase |
| Inventory optimization | Future phase |

The forecasting research experiment is formally concluded.
