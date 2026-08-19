# Baseline Forecasting Report

## AI Sales Forecasting and Inventory Optimizer

**Notebook:** `02_baseline_forecasting.ipynb`  
**Dataset:** Selected M5 Forecasting Accuracy development subset  
**Forecast horizon:** 28 days  
**Development period:** `d_1–d_1913`  
**Protected holdout:** `d_1914–d_1941`

---

## 1. Purpose

This report documents the process used to identify the strongest simple forecasting baseline for the selected M5 sales subset.

A baseline is a transparent forecasting rule that establishes the minimum performance expected from later machine-learning models. A more complex model should only be accepted if it improves meaningfully and consistently upon this benchmark.

The baseline selection process was designed to answer four questions:

1. Which simple historical-demand rule produces the most accurate 28-day forecasts?
2. Is its performance stable across different validation periods?
3. Does performance differ between stores and categories?
4. Does accuracy worsen as the forecast moves from day 1 toward day 28?

---

## 2. Development Data

The analysis used the same subset examined during exploratory data analysis.

| Item | Value |
|---|---:|
| Stores | 2 |
| Products | 47 |
| Product-store series | 94 |
| Historical days | 1,913 |
| Development rows | 179,822 |
| Forecast horizon | 28 days |

The two stores are `CA_1` and `CA_3`. The subset contains products from Foods, Hobbies, and Household.

The protected period `d_1914–d_1941` was not used for baseline construction, model comparison, or parameter selection.

---

## 3. Validation Design

### 3.1 Why a random split was not used

A random train-test split is unsuitable for time-series forecasting because it can allow future observations to influence predictions of earlier dates. It also does not reproduce the real forecasting process, in which only past information is available.

### 3.2 Rolling-origin validation

Five non-overlapping 28-day validation folds were created within the development period. The training window expanded with each fold.

| Fold | Training ends | Validation begins | Validation ends |
|---:|---:|---:|---:|
| 1 | `d_1773` | `d_1774` | `d_1801` |
| 2 | `d_1801` | `d_1802` | `d_1829` |
| 3 | `d_1829` | `d_1830` | `d_1857` |
| 4 | `d_1857` | `d_1858` | `d_1885` |
| 5 | `d_1885` | `d_1886` | `d_1913` |

Each fold contained:

- 94 product-store series;
- 28 forecast days per series;
- 2,632 forecast observations.

Across five folds, every baseline produced 13,160 predictions.

### 3.3 Leakage controls

All forecast inputs came from dates on or before the applicable training cutoff. No actual sales from inside a validation horizon were used to generate its forecasts.

The following checks were applied:

- every fold contained all 94 series;
- every series contained exactly 28 validation observations;
- no forecasts were missing;
- all source dates were no later than the training cutoff;
- predictions were non-negative;
- the protected holdout remained excluded.

---

## 4. Evaluation Metrics

Four complementary metrics were used.

| Metric | Interpretation |
|---|---|
| MAE | Average absolute forecast error in units |
| RMSE | Error measure that penalizes large misses more heavily |
| WAPE | Total absolute error divided by total actual demand |
| Bias | Net overforecasting or underforecasting relative to actual demand |

For bias:

- a positive value indicates overforecasting;
- a negative value indicates underforecasting;
- a value near zero indicates balanced aggregate forecasts.

WAPE was the primary comparison metric, supported by MAE, RMSE, bias, and stability across folds.

---

## 5. Baselines Evaluated

### 5.1 Seasonal naïve: lag 28

Each forecast used demand from exactly 28 days earlier:

$$
\hat{y}_t = y_{t-28}
$$

This preserves the same weekday because 28 days equal four complete weeks.

### 5.2 Repeated last-week pattern

The final seven observed training days were repeated four times across the 28-day horizon. This tested whether the most recent weekly pattern was more useful than observations from four weeks earlier.

### 5.3 Recent 7-day mean

The mean demand from the final seven training days was used as a constant forecast for all 28 future days.

### 5.4 Recent 14-day mean

The mean demand from the final 14 training days was used as a constant forecast for the complete horizon.

### 5.5 Recent 28-day mean

The mean demand from the final 28 training days was used as a constant forecast for the complete horizon.

The recent-mean baselines deliberately smooth noisy daily demand. Their main limitation is that they do not directly reproduce weekday variation.

---

## 6. Overall Baseline Performance

| Rank | Model | MAE | RMSE | WAPE | Bias |
|---:|---|---:|---:|---:|---:|
| 1 | Recent 14-day mean | 3.755 | 5.729 | 39.545% | -1.455% |
| 2 | Recent 28-day mean | 3.783 | 5.793 | 39.839% | -0.489% |
| 3 | Recent 7-day mean | 3.837 | 5.815 | 40.414% | -0.765% |
| 4 | Repeated last-week pattern | 4.511 | 6.768 | 47.511% | -0.765% |
| 5 | Seasonal naïve: lag 28 | 4.664 | 7.135 | 49.125% | -0.489% |

### 6.1 Main result

The recent 14-day mean achieved the lowest MAE, RMSE, and WAPE.

Compared with the previous-best repeated last-week baseline, it delivered approximately:

- 16.8% lower MAE;
- 15.4% lower RMSE;
- 7.966 percentage points lower WAPE.

The results show that smoothing recent product-level demand is more effective than directly copying noisy daily observations.

### 6.2 Interpretation of the history windows

- The 7-day mean is responsive but can be influenced by an unusual recent week.
- The 28-day mean is stable but may react too slowly to recent demand changes.
- The 14-day mean provides the strongest observed balance between responsiveness and smoothing.

The 28-day mean has slightly better aggregate bias, but its point-level errors are marginally higher.

---

## 7. Stability Across Validation Folds

| Model | Mean MAE | SD of MAE | Mean RMSE | Mean fold WAPE | SD of WAPE | Best WAPE | Worst WAPE | Mean bias | Fold wins |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Recent 14-day mean | 3.755 | 0.187 | 5.721 | 39.635% | 3.053 | 36.673% | 43.214% | -1.360% | 2 |
| Recent 28-day mean | 3.783 | 0.198 | 5.786 | 39.961% | 3.656 | 36.779% | 45.315% | -0.326% | 2 |
| Recent 7-day mean | 3.837 | 0.234 | 5.804 | 40.462% | 2.685 | 37.905% | 44.398% | -0.716% | 1 |
| Repeated last-week pattern | 4.511 | 0.358 | 6.747 | 47.561% | 3.878 | 44.298% | 53.854% | -0.716% | 0 |
| Seasonal naïve: lag 28 | 4.664 | 0.351 | 7.105 | 49.320% | 5.826 | 44.626% | 58.539% | -0.326% | 0 |

The 14-day and 28-day means each won two folds, while the 7-day mean won one. The seasonal-pattern baselines did not win any fold.

Although the 14-day mean did not win every individual fold, it produced:

- the lowest average MAE;
- the lowest average RMSE;
- the lowest average fold WAPE;
- the lowest worst-fold WAPE.

This supports its selection as the primary baseline.

---

## 8. Store-Level Findings

| Store | Best baseline | MAE | RMSE | WAPE | Bias |
|---|---|---:|---:|---:|---:|
| CA_1 | Recent 28-day mean | 3.504 | 5.375 | 44.501% | +0.295% |
| CA_3 | Recent 14-day mean | 3.988 | 6.064 | 35.878% | -3.021% |

CA_3 has higher absolute errors but lower WAPE because its sales volume is higher. An error of approximately four units therefore represents a smaller percentage of CA_3 demand.

The results suggest that CA_1 benefits from longer smoothing, while CA_3 benefits from a more responsive recent-demand estimate.

---

## 9. Category-Level Findings

| Category | Best baseline | MAE | RMSE | WAPE | Bias |
|---|---|---:|---:|---:|---:|
| Foods | Recent 14-day mean | 4.118 | 6.116 | 34.700% | -1.177% |
| Hobbies | Recent 28-day mean | 4.188 | 6.673 | 70.628% | +0.867% |
| Household | Recent 28-day mean | 2.642 | 3.954 | 52.347% | -2.111% |

Foods is the easiest category to forecast in relative terms. Hobbies is the most difficult, with a best WAPE of 70.628%.

Hobbies has an MAE similar to Foods but much lower demand volume. Consequently, a similar absolute error becomes a much larger percentage error.

These results agree with the EDA findings:

- Foods benefits from a shorter, more responsive demand window.
- Hobbies and Household benefit from longer averaging that suppresses noise.
- Lower-volume and irregular demand is harder to forecast accurately in percentage terms.

The segment-specific winners were identified using the same validation results. They should therefore guide feature engineering rather than be treated as independently validated custom models.

---

## 10. Forecast-Horizon Findings

The recent 14-day mean was the best baseline in every seven-day portion of the 28-day horizon.

| Forecast week | MAE | RMSE | WAPE | Bias |
|---:|---:|---:|---:|---:|
| 1: days 1–7 | 3.659 | 5.404 | 38.492% | -1.581% |
| 2: days 8–14 | 3.725 | 5.709 | 38.213% | -4.003% |
| 3: days 15–21 | 3.881 | 6.010 | 41.642% | +0.403% |
| 4: days 22–28 | 3.754 | 5.777 | 39.912% | -0.528% |

Accuracy does not deteriorate continuously as the forecast moves further into the future. Week 4 performs better than Week 3, showing that calendar effects and demand shocks matter more than horizon distance alone.

---

## 11. Christmas-Day Diagnostic

All five baselines showed an exceptional error spike on horizon day 19.

The cause was confirmed by examining horizon day 19 separately within each validation fold.

| Fold | Date | Actual units | 14-day mean forecast | Absolute error | Daily WAPE |
|---:|---|---:|---:|---:|---:|
| 1 | 2015-12-25 | 3 | 930.357 | 927.357 | 30,911.905% |
| 2 | 2016-01-22 | 712 | 854.929 | 142.929 | 20.074% |
| 3 | 2016-02-19 | 926 | 818.357 | 107.643 | 11.624% |
| 4 | 2016-03-18 | 845 | 885.357 | 40.357 | 4.776% |
| 5 | 2016-04-15 | 751 | 908.643 | 157.643 | 20.991% |

On Christmas Day 2015, actual demand across all 94 series fell to only three units, while the historical baseline forecast normal demand.

This observation has two important implications:

1. Historical-demand features alone cannot anticipate exceptional closures or event behaviour.
2. Daily WAPE becomes unstable when actual demand is close to zero and should not be interpreted in isolation.

The future model needs specific calendar information rather than only a general event-day flag.

---

## 12. Final Baseline Decision

### Primary benchmark

**Recent 14-day mean**

This model is selected because it provides the strongest overall accuracy, the best average performance across folds, the lowest worst-fold WAPE, and the best result in every forecast week.

Any machine-learning model should be compared against the following primary benchmark:

| Metric | Benchmark value |
|---|---:|
| MAE | 3.755 units |
| RMSE | 5.729 units |
| WAPE | 39.545% |
| Bias | -1.455% |

### Secondary benchmark

**Recent 28-day mean**

This remains a useful secondary reference because its accuracy is close to the 14-day mean and its aggregate bias is smaller.

### Seasonal reference baselines

The lag-28 and repeated-week methods remain useful sanity checks, but both are clearly weaker than recent-demand smoothing.

---

## 13. Requirements for the Next Modeling Stage

The baseline results directly motivate the following feature groups:

### Historical-demand features

- lag 28;
- longer forecast-safe lags such as 35, 42, 49, and 56;
- shifted 7-, 14-, and 28-day rolling averages;
- rolling variability and recent trend features.

All rolling calculations must be shifted sufficiently to prevent sales inside the 28-day forecast horizon from leaking into feature values.

### Calendar features

- day of week;
- weekend indicator;
- month and seasonal position;
- event name;
- event type;
- Christmas indicator;
- days before and after major events;
- SNAP-CA status;
- forecast-horizon day.

### Hierarchical identifiers

- store;
- product;
- category;
- department.

### Price features

- available sell price;
- relative price position;
- price-change indicators;
- price history constructed without future information.

---

## 14. Completion Status

The baseline discovery stage is complete.

Completed work includes:

- leakage-safe rolling-origin validation;
- five baseline implementations;
- overall metric comparison;
- fold-stability analysis;
- store and category breakdowns;
- forecast-horizon evaluation;
- Christmas anomaly diagnosis;
- primary and secondary benchmark selection.

The next project notebook should be:

`03_feature_engineering.ipynb`

Its purpose will be to construct forecast-safe features for the first global machine-learning model while keeping `d_1914–d_1941` protected.
