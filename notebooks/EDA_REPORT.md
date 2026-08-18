# M5 Exploratory Data Analysis Report

## AI Sales Forecasting and Inventory Optimizer

**Status:** Complete  
**Dataset:** M5 Forecasting — Accuracy  
**Analysis grain:** One row per date × store × product  
**Development period:** `d_1`–`d_1913`  
**Protected final holdout:** `d_1914`–`d_1941`

---

## 1. Executive Summary

This report documents the exploratory analysis performed for the demand-forecasting component of the AI Sales Forecasting and Inventory Optimizer project.

The development subset contains 47 products sold in two California stores (`CA_1` and `CA_3`), producing 94 product-store time series and 179,822 daily observations. The data covers 1,913 consecutive days from 2011-01-29 through 2016-04-24. The final 28 days, `d_1914`–`d_1941`, remain protected and were not used in this analysis.

The principal findings are:

- The dataset passed the core quality and continuity checks.
- Demand is mostly regular: 79.79% of series are classified as smooth.
- Hobbies is the most difficult category, with only 30% smooth series.
- Demand has strong weekly seasonality; weekend demand is approximately 35.9% higher than Monday-to-Friday demand overall.
- August is consistently the strongest month, while January is consistently weak.
- Christmas creates near-zero aggregate sales and must be modeled as a specific event.
- SNAP-CA days are associated with approximately 10.6% higher average sales than non-SNAP days.
- `CA_3` contributes 57.35% of units and has approximately 34.4% higher average daily demand than `CA_1`.
- Lag 28 is the strongest exact historical lag that is safely available across a direct 28-day forecast horizon.
- Shifted rolling averages improve signal stability, particularly for Hobbies and Household.
- Prices are slow-moving and mainly reflect long-term repricing rather than frequent promotions.
- M5 contains observed sales but no inventory-on-hand data, so true demand cannot always be separated from stockout-censored sales.

The EDA supports moving to leakage-safe baselines and rolling-origin validation. Further exploratory drilling into isolated price events is unlikely to improve the first forecasting model.

---

## 2. Business Objective

The forecasting system is intended to answer:

> How many units of each product will each store sell over the next 28 days, and how should those forecasts inform inventory decisions?

The forecasting target is daily `units_sold` at the product-store level. Forecasts will later be converted into reorder points, safety stock, stockout-risk indicators, and recommended order quantities.

This EDA focuses on four questions:

1. Is the development data reliable enough for modeling?
2. What kinds of demand patterns exist across products, stores, and categories?
3. Which historical and future-known variables are likely to be useful?
4. Which limitations and leakage risks must the modeling pipeline control?

---

## 3. Dataset Scope

| Metric | Value |
|---|---:|
| Rows | 179,822 |
| Columns | 11 |
| Start date | 2011-01-29 |
| End date | 2016-04-24 |
| Development days | 1,913 |
| Stores | 2 |
| Products | 47 |
| Product-store series | 94 |
| Categories | 3 |
| Departments | 5 |

The canonical dataset contains:

- `product_id`
- `department_id`
- `category_id`
- `store_id`
- `state_id`
- `day_id`
- `units_sold`
- `date`
- `week_id`
- `sell_price`
- `day_num`

The subset includes `CA_1` and `CA_3` and contains products from Foods, Hobbies, and Household.

### Holdout protection

The maximum day used during EDA is `d_1913`. No sales from `d_1914`–`d_1941` were used to calculate distributions, correlations, lags, rolling statistics, or price findings.

---

## 4. Data-Quality Assessment

### 4.1 Grain and uniqueness

- Duplicate full rows: 0
- Duplicate `(date, store_id, product_id)` combinations: 0
- Expected rows: 94 series × 1,913 days = 179,822
- Actual rows: 179,822

Every date-store-product combination is unique.

### 4.2 Missing values

All critical columns are complete. The only missing field is `sell_price`:

| Column | Missing rows | Missing percentage |
|---|---:|---:|
| `sell_price` | 966 | 0.54% |

All 966 missing-price rows have zero units sold. They occur before the first recorded positive sale for the affected product-store series. No missing prices occur inside an active-sales window, and no missing-price row has positive sales.

**Decision:** retain these values as missing. Do not forward-fill prices into the pre-sale period.

The first positive sale is an observed-data boundary, not a verified official product-launch date.

### 4.3 Numeric validity

- Negative sales rows: 0
- Non-finite sales rows: 0
- Zero or negative available prices: 0
- Infinite available prices: 0

### 4.4 Date continuity

- Expected dates: 1,913
- Observed dates: 1,913
- Missing calendar dates: 0
- Series with incomplete date coverage: 0

Every product-store series contains one observation for every development date.

### Quality conclusion

The canonical development subset is structurally suitable for forecasting. Remaining concerns relate to business interpretation—particularly availability and stockouts—rather than missing rows or invalid values.

---

## 5. Target Distribution

### 5.1 Zero and positive sales

| Sales status | Rows | Percentage |
|---|---:|---:|
| Zero sales | 13,511 | 7.51% |
| Positive sales | 166,311 | 92.49% |

The subset is not dominated by zero demand.

### 5.2 Descriptive statistics

| Statistic | Units sold |
|---|---:|
| Mean | 10.998 |
| Standard deviation | 12.700 |
| Minimum | 0 |
| 25th percentile | 3 |
| Median | 7 |
| 75th percentile | 14 |
| 90th percentile | 25 |
| 95th percentile | 35 |
| 99th percentile | 65 |
| Maximum | 151 |

Sales skewness is 2.838, indicating a strong right tail. The mean exceeds the median because a small number of high-volume observations pull it upward.

### 5.3 High-demand tail

Using 65 units as the global 99th-percentile threshold:

- High-demand observations: 1,869
- Percentage of observations: 1.04%
- Share of all units: 7.52%

The tail is highly concentrated. Four product-store series account for approximately 94.11% of tail units, led by `FOODS_3_586` and `FOODS_3_252`.

The global threshold should not be treated as a universal anomaly boundary. For example, `CA_3 / FOODS_3_586` has mean daily sales of 70.25 and median daily sales of 69, making values around 65 normal for that series.

**Implication:** outlier treatment, if needed, must be series-aware and business-aware. High observed demand should not be automatically capped or deleted.

---

## 6. Product-Store Demand Patterns

Demand patterns were classified using Average Demand Interval (ADI) and squared coefficient of variation (CV²) calculated from positive-demand quantities.

| Pattern | Series | Percentage | Interpretation |
|---|---:|---:|---|
| Smooth | 75 | 79.79% | Frequent, relatively stable positive demand |
| Erratic | 11 | 11.70% | Frequent but variable positive quantities |
| Intermittent | 5 | 5.32% | Irregular timing but relatively stable positive quantities |
| Lumpy | 3 | 3.19% | Irregular timing and variable positive quantities |

The evidence does **not** support describing the whole subset as highly intermittent. Only eight of 94 series are intermittent or lumpy.

### 6.1 Patterns by store

| Store | Smooth | Erratic | Intermittent | Lumpy |
|---|---:|---:|---:|---:|
| CA_1 | 37 | 3 | 5 | 2 |
| CA_3 | 38 | 8 | 0 | 1 |

Smooth demand dominates both stores. All five intermittent series occur in `CA_1`, while `CA_3` contains more erratic series. The proportion of non-smooth series is similar, but the type of difficulty differs.

### 6.2 Patterns by category

| Category | Smooth | Erratic | Intermittent | Lumpy | Smooth percentage |
|---|---:|---:|---:|---:|---:|
| Foods | 53 | 6 | 0 | 1 | 88.33% |
| Hobbies | 3 | 4 | 1 | 2 | 30.00% |
| Household | 19 | 1 | 4 | 0 | 79.17% |

Hobbies is the most difficult category: 70% of its ten selected series are non-smooth. This conclusion applies to the development subset and should not be generalized to every M5 Hobbies product.

---

## 7. Temporal Demand Patterns

### 7.1 Broad movement

The aggregate 28-day rolling average shows recurring rises and declines rather than a single continuous upward or downward trend. Daily totals fluctuate substantially around the smoother medium-term pattern.

The aggregate series is influenced heavily by high-volume Food products, so it is used for portfolio-level context rather than product-level inference.

### 7.2 Exceptionally low days

The five lowest-demand dates are all December 25:

| Date | Total units |
|---|---:|
| 2011-12-25 | 0 |
| 2012-12-25 | 1 |
| 2013-12-25 | 2 |
| 2014-12-25 | 0 |
| 2015-12-25 | 3 |

The next-lowest daily total is 560 units. Christmas is therefore a structural calendar effect, not a missing date or an ordinary random outlier.

**Decision:** retain these observations and use specific event features.

### 7.3 Weekly seasonality

All 15 highest-demand dates occur on weekends: 11 Sundays and four Saturdays.

| Day | Mean daily sales | Median | Demand index |
|---|---:|---:|---:|
| Monday | 993.61 | 987 | 96.11 |
| Tuesday | 896.39 | 886 | 86.71 |
| Wednesday | 879.99 | 872 | 85.12 |
| Thursday | 895.14 | 884 | 86.59 |
| Friday | 1,021.89 | 1,010 | 98.85 |
| Saturday | 1,264.07 | 1,258 | 122.27 |
| Sunday | 1,283.85 | 1,294 | 124.19 |

Average weekend demand is approximately 35.9% higher than average Monday-to-Friday demand.

The pattern exists in every category:

| Category | Saturday index | Sunday index | Approximate weekend uplift versus weekdays |
|---|---:|---:|---:|
| Foods | 122.88 | 123.89 | 36.2% |
| Hobbies | 123.43 | 115.87 | 29.9% |
| Household | 118.39 | 128.80 | 36.5% |

The exact weekend peak differs by category, supporting interactions between category and weekday.

### 7.4 Monthly seasonality

| Month | Demand index |
|---|---:|
| January | 88.48 |
| February | 93.84 |
| March | 93.81 |
| April | 97.27 |
| May | 98.73 |
| June | 106.94 |
| July | 109.28 |
| August | 112.93 |
| September | 103.21 |
| October | 100.85 |
| November | 97.94 |
| December | 99.39 |

Average August demand is approximately 27.6% higher than January demand. August has the highest within-year demand index in every complete year from 2012 through 2015, confirming that the aggregate result is not driven by one unusual year.

June through September form a recurring high-demand period. January is consistently below average. December has the highest variability because it contains the Christmas collapse.

### 7.5 Events and SNAP

| Day type | Days | Mean sales | Median sales | Demand index |
|---|---:|---:|---:|---:|
| Event day | 154 | 996.95 | 1,016.5 | 96.43 |
| No recorded event | 1,759 | 1,037.04 | 1,003.0 | 100.31 |

The event-day mean is lower while the median is slightly higher. Events are heterogeneous: some increase sales and others, especially Christmas, reduce sales sharply. A single `has_event` flag is insufficient; event name and type should be retained.

| SNAP status | Days | Mean sales | Median sales | Demand index |
|---|---:|---:|---:|---:|
| Non-SNAP day | 1,283 | 998.95 | 970 | 96.63 |
| SNAP-CA day | 630 | 1,104.82 | 1,075 | approximately 106.87 |

SNAP-day mean demand is approximately 10.6% higher than non-SNAP-day demand. This is an association, not proof of causality, because SNAP timing may overlap with weekday and monthly patterns. `snap_CA` is nevertheless a useful future-known feature.

---

## 8. Store-Level Differences

| Store | Total units | Mean daily sales | Median daily sales | Standard deviation | Share of units |
|---|---:|---:|---:|---:|---:|
| CA_1 | 843,548 | 440.96 | 417 | 117.12 | 42.65% |
| CA_3 | 1,134,136 | 592.86 | 583 | 112.50 | 57.35% |

`CA_3` has approximately 34.4% higher average daily demand than `CA_1`. Their absolute standard deviations are similar, but relative variability is greater in `CA_1`:

- Approximate `CA_1` coefficient of variation: 0.27
- Approximate `CA_3` coefficient of variation: 0.19

The correlation between daily aggregate store sales is 0.801. After removing each store's normal weekday effect, correlation falls to 0.668. Shared weekly seasonality explains part of their co-movement, while broader common demand movements remain.

The 28-day rolling-average correlation is 0.780. Store identity must be included, and errors should be reported separately for each store.

---

## 9. Historical-Demand Relationships

### 9.1 General lag correlations

Median correlation across the 94 series:

| Lag | Median correlation |
|---|---:|
| 1 | 0.321 |
| 7 | 0.301 |
| 14 | 0.271 |
| 28 | 0.263 |

Historical demand is informative but not sufficient by itself. Relationships weaken gradually with age, while weekly and four-week patterns remain visible.

### 9.2 Category differences

| Lag | Foods | Hobbies | Household |
|---|---:|---:|---:|
| 1 | 0.373 | 0.085 | 0.264 |
| 7 | 0.343 | 0.111 | 0.265 |
| 14 | 0.303 | 0.116 | 0.243 |
| 28 | 0.315 | 0.073 | 0.201 |

Foods has the strongest historical dependence. Hobbies has weak linear lag relationships, consistent with its erratic and lumpy series.

### 9.3 Forecast-safe exact lags

For a direct 28-day batch forecast, lag values of 28 days or more are available for every horizon day at the forecast origin.

| Safe lag | All series | Foods | Hobbies | Household |
|---|---:|---:|---:|---:|
| 28 | 0.263 | 0.315 | 0.073 | 0.201 |
| 35 | 0.243 | 0.286 | 0.093 | 0.191 |
| 42 | 0.208 | 0.264 | 0.080 | 0.171 |
| 49 | 0.189 | 0.248 | 0.082 | 0.160 |
| 56 | 0.215 | 0.254 | 0.060 | 0.154 |

Lag 28 is the strongest safe exact lag overall. The modest rebound at lag 56 may reflect an eight-week relationship, particularly for Foods, but this must be tested through time-based validation.

### 9.4 Forecast-safe rolling averages

Rolling means were constructed by shifting demand 28 days before applying the rolling window.

| Window | All series | Foods | Hobbies | Household |
|---|---:|---:|---:|---:|
| 7 days | 0.261 | 0.293 | 0.124 | 0.215 |
| 14 days | 0.269 | 0.295 | 0.135 | 0.232 |
| 28 days | 0.253 | 0.296 | 0.166 | 0.238 |

Foods benefits more from the exact lag-28 value, which preserves the same weekday. Hobbies and Household benefit from smoothing, which reduces noise.

### Leakage rule

For a 28-day batch forecast, actual lag-1, lag-7, and lag-14 values are not known for every future day. They can only be used with a properly designed recursive or horizon-specific strategy. Using actual sales from inside the validation or holdout horizon would be target leakage.

---

## 10. Price Analysis

### 10.1 Variation

Across the 94 product-store series:

- Mean unique prices: 2.86
- Median unique prices: 3
- Median relative price range: 9.76%
- 90th-percentile relative range: 17.94%
- Maximum relative range: 33.56%

Prices contain meaningful variation for some products but move much more slowly than daily demand.

### 10.2 Transition frequency

- Total transitions: 207
- Mean transitions per series: 2.20
- Median transitions per series: 2
- 90% of series have five or fewer transitions
- Maximum transitions in one series: 9

Price increases account for 147 transitions (71.01%), with a median increase of 6.33%. Decreases account for 60 transitions (28.99%), with a median decrease of 5.56% in absolute terms.

Percentage increases and decreases are asymmetric. A fall from 2.98 to 1.98 is −33.56%, while returning from 1.98 to 2.98 is +50.51%.

### 10.3 Price-spell duration

Completed interior price spells exclude each series' first and final observed spell because their full durations may extend outside the development period.

- Completed interior spells: 123
- Median duration: 385 days
- Mean duration: 490.91 days
- 25th percentile: 133 days
- 75th percentile: 693 days
- Minimum: 7 days
- Maximum: 1,785 days

| Duration | Spells | Percentage |
|---|---:|---:|
| 1–28 days | 3 | 2.44% |
| 29–90 days | 14 | 11.38% |
| More than 90 days | 106 | 86.18% |

Most price changes are long-term repricing rather than temporary promotions.

### 10.4 Short discount-like spells

Only three completed spells last 28 days or less. All occur in `CA_3` Foods products, fall below both adjacent prices, and return exactly to the previous price:

| Product | Duration | Price pattern |
|---|---:|---|
| `FOODS_2_197` | 28 days | 3.28 → 3.00 → 3.28 |
| `FOODS_3_217` | 7 days | 2.98 → 1.98 → 2.98 |
| `FOODS_3_400` | 7 days | 2.98 → 1.99 → 2.98 |

Observed sales did not rise during these spells. `FOODS_2_197` experienced an almost complete sales collapse in both stores during the same period, indicating a shared product or availability issue rather than a simple CA_3 price response. The other two samples are seven-day, low-volume events and are too small for reliable elasticity estimates.

**Conclusion:** the subset does not support credible causal price-elasticity estimation. Price is best treated as a slow-moving contextual feature for the first model.

### Price leakage rules

- Full-history median prices are acceptable for retrospective EDA but not as training features.
- Relative price features must use past-only reference values unless an official regular price is known.
- Future prices may only be used if planned prices are genuinely available at the forecast origin.
- Labels such as `returned_to_previous_price` use future information and must not be model features.

---

## 11. Feature Recommendations

### 11.1 Future-known features

| Group | Candidate features |
|---|---|
| Identifiers | `store_id`, `product_id`, `department_id`, `category_id` |
| Calendar | day of week, weekend flag, month, quarter, week of year |
| Events | event name, event type, Christmas indicator |
| Benefits | `snap_CA` |
| Price | future planned price only when known at forecast time |

### 11.2 Historical features

| Group | Candidate features |
|---|---|
| Exact safe lags | `lag_28`, `lag_35`, `lag_42`, `lag_49`, `lag_56` |
| Safe rolling means | 7-, 14-, and 28-day windows after a 28-day shift |
| Optional safe volatility | rolling standard deviation after the same shift |
| Price history | past-relative price, past price change, days since past price change |
| Missingness | price-missing indicator |

Tree-based models such as LightGBM can learn interactions among store, category, calendar, lag, and price features. Simpler baselines remain necessary to demonstrate incremental value.

---

## 12. Modeling and Validation Requirements

### 12.1 Baselines

The baseline harness should include only strategies whose information is available at the forecast origin. Initial candidates include:

- Safe seasonal naive forecast using lag 28
- Repeated recent-week seasonal pattern, implemented without reading future actuals
- Safe shifted rolling-mean forecast

Any previous-day or previous-week baseline must define whether it is recursive and must never consume actual observations from inside the evaluation horizon.

### 12.2 Time-based validation

Random train-test splitting is prohibited. Use rolling-origin validation with 28-day validation windows inside `d_1`–`d_1913`, followed by one final evaluation on the protected `d_1914`–`d_1941` holdout.

### 12.3 Metrics

Report more than one metric:

- MAE for intuitive unit error
- RMSE for sensitivity to large misses
- WAPE or a scaled metric for portfolio comparison
- Forecast bias to detect systematic over- or under-forecasting
- Metrics by store, category, demand pattern, and forecast horizon

For closer alignment with the M5 benchmark, RMSSE or WRMSSE can be added after the basic evaluation harness is stable.

### 12.4 Reproducibility and engineering controls

- Feature generation must be deterministic and cutoff-aware.
- Every run must log data range, row count, feature configuration, validation windows, model parameters, and metrics.
- Validation functions must fail loudly when protected dates enter development features.
- Model artifacts must record the dataset version and feature schema.
- Exceptions must include actionable context rather than being silently ignored.

---

## 13. Inventory-Optimization Limitations

M5 does not provide:

- Inventory on hand
- Confirmed stockout flags
- Lost sales
- Supplier lead times
- Order costs
- Holding costs
- Service-level targets

Observed `units_sold` may therefore be lower than true customer demand when stock is unavailable.

The inventory phase must clearly separate observed facts from assumptions. Lead time, service level, starting inventory, ordering constraints, and cost parameters should be configurable and documented. Inventory recommendations should initially be presented as scenario-based decisions rather than claims about Walmart's actual historical inventory.

---

## 14. Final Conclusions

The M5 development subset is suitable for building a serious forecasting pipeline. It contains clean and complete daily histories, strong calendar structure, meaningful store and category differences, and usable historical-demand signals.

The earlier description of the subset as highly intermittent should be replaced. Demand is predominantly smooth, while difficulty is concentrated in Hobbies and a small number of intermittent or lumpy series.

The first modeling iteration should prioritize:

1. Leakage-safe baselines
2. Rolling-origin validation
3. Future-known calendar, event, and SNAP features
4. Forecast-safe lags and rolling statistics
5. Store, product, and category interactions
6. Cautious use of known price information

The project should now move from EDA to baseline forecasting. Additional micro-analysis of isolated historical price events has diminishing value for the first model and should only be revisited if validation shows that price features materially improve forecasts.

