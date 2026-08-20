# Model Training and Tuning Report

## 1. Purpose of this stage

This stage moved the project from simple forecasting rules to a trained machine-learning model. The goal was not merely to obtain a lower error once, but to determine whether a model could consistently outperform the strongest baseline across several realistic forecasting periods without using future information.

The selected candidate is **LightGBM with a Poisson objective and the flexible configuration**.

Its cross-validation performance was:

| Metric | Selected LightGBM | Best baseline | Improvement |
| --- | ---: | ---: | ---: |
| MAE | 3.292 | 3.755 | about 12.3% |
| RMSE | 4.898 | 5.729 | about 14.5% |
| WAPE | 34.675% | 39.545% | 4.870 percentage points, about 12.3% relative |
| Bias | -1.055% | -1.455% | closer to zero |

These results justify promoting the flexible LightGBM configuration to the final holdout-evaluation stage. They do **not** yet constitute the final estimate of production performance because the protected holdout, days `d_1914` through `d_1941`, remains untouched.

## 2. Data used for modeling

The model used the feature dataset produced in the feature-engineering stage:

- 94 product-store time series
- 172,020 training rows
- development period from `d_84` through `d_1913`
- 64 model features: 10 categorical and 54 numerical
- target: `units_sold`
- forecast horizon: 28 days

The first 83 days were removed because the longest safe historical features require an 83-day warm-up period. The protected holdout was excluded throughout model development and tuning.

## 3. Intuition behind the model

LightGBM builds many small decision trees. Each new tree concentrates on patterns that the previous trees did not explain well. Taken together, the trees can represent nonlinear relationships such as:

- demand being different for each product and store;
- weekends affecting categories differently;
- recent demand level being more useful for one product than another;
- events, seasonality, and price conditions interacting with recent sales history.

The **Poisson objective** was chosen because the target is a non-negative count. It gives the model a loss function that is better aligned with unit-sales data than ordinary squared-error regression and naturally produces positive-valued expectations. Final predictions are still checked to ensure that they are finite and non-negative.

## 4. Forecast-safe feature strategy

The model used information that would be available when a 28-day forecast is created:

- product, department, category, store, and state identifiers;
- calendar and cyclical time features;
- weekday, month, season, event, Christmas, and SNAP indicators;
- demand lags at 28, 35, 42, and 56 days;
- rolling demand means and standard deviations over 7, 14, 28, and 56 days, shifted by 28 days;
- price level, price changes, reference-price comparisons, and time since a price change.

The 28-day shift is crucial. For a forecast made at the start of the horizon, every demand-based feature points to sales observed before the horizon begins. This prevents target leakage.

The strategy can be summarized as:

1. Use recent history to estimate the underlying demand level.
2. Use product and store identity to learn persistent differences between series.
3. Use calendar and event features to adjust for predictable timing effects.
4. Use price features as supporting context rather than assuming that every price decrease is a promotion.

## 5. Validation design

Five rolling-origin folds were used. Each fold trained on the past and evaluated the next 28 days.

| Fold | Training ends | Validation period |
| ---: | ---: | --- |
| 1 | `d_1773` | `d_1774`–`d_1801` |
| 2 | `d_1801` | `d_1802`–`d_1829` |
| 3 | `d_1829` | `d_1830`–`d_1857` |
| 4 | `d_1857` | `d_1858`–`d_1885` |
| 5 | `d_1885` | `d_1886`–`d_1913` |

Each validation fold contained 2,632 predictions: 94 series multiplied by 28 days. Across five folds, every candidate was evaluated on 13,160 forecasts.

Within each outer training period, the most recent 28 training days were used for early stopping. The selected number of boosting rounds was then used to retrain on the complete outer training period before predicting the untouched outer validation window. This kept model selection separate from performance measurement.

## 6. Metrics and how to interpret them

### Mean absolute error (MAE)

MAE is the average absolute difference between predicted and actual daily units. An MAE of 3.292 means that a product-store-day forecast missed by about 3.3 units on average.

### Root mean squared error (RMSE)

RMSE penalizes large misses more heavily than MAE. The selected model's RMSE of 4.898 indicates that it also reduced larger errors compared with the baseline RMSE of 5.729.

### Weighted absolute percentage error (WAPE)

WAPE divides total absolute error by total actual demand. It is useful here because individual percentage errors become unstable when actual demand is zero or very small. Lower is better.

### Bias

Bias compares total predicted units with total actual units. Negative bias means underforecasting. The selected model's bias of -1.055% is small, although it should continue to be monitored by store, category, and forecast week.

## 7. Baseline comparison

The strongest simple benchmark was the **recent 14-day mean**, which predicts each future day using a product-store series' average demand over its most recent 14 observed days.

| Model | MAE | RMSE | WAPE | Bias |
| --- | ---: | ---: | ---: | ---: |
| LightGBM Poisson, initial configuration | 3.301 | 4.914 | 34.769% | -1.778% |
| Recent 14-day mean | 3.755 | 5.729 | 39.545% | -1.455% |

The initial LightGBM model beat the baseline in every one of the five folds. This is stronger evidence than a single aggregate improvement because it shows that the gain was repeated across different forecast origins.

## 8. Controlled tuning

Only a small, deliberate tuning round was conducted. This avoided turning the five validation folds into an extensively searched pseudo-test set.

Three configurations were compared:

- **Compact:** fewer leaves, larger minimum leaf population, and stronger regularization. This favors simpler trees.
- **Current:** the original configuration with 31 leaves.
- **Flexible:** more leaves and smaller minimum leaf population, with regularization retained. This allows more detailed interactions.

| Configuration | MAE | RMSE | WAPE | Bias |
| --- | ---: | ---: | ---: | ---: |
| Flexible | **3.292** | **4.898** | **34.675%** | **-1.055%** |
| Current | 3.301 | 4.914 | 34.769% | -1.778% |
| Compact | 3.308 | 4.913 | 34.836% | -1.323% |

The differences are small, so the tuning result should not be overstated. Nevertheless, the flexible configuration had the best overall MAE, RMSE, WAPE, bias, and WAPE stability.

Its fold-level WAPE had a mean of 34.702%, a standard deviation of 0.828 percentage points, and a range from 33.636% to 35.674%.

## 9. Fold-by-fold configuration result

| Fold | Winning configuration | WAPE |
| ---: | --- | ---: |
| 1 | Flexible | 35.250% |
| 2 | Flexible | 35.674% |
| 3 | Flexible | 34.834% |
| 4 | Flexible | 34.116% |
| 5 | Compact | 33.623% |

The flexible configuration won four of five folds. The compact configuration won the final fold by a narrow margin. Combined with its best aggregate score and lowest WAPE standard deviation, this supports selecting the flexible model without further tuning.

## 10. Performance across business segments

The initial LightGBM configuration improved on the 14-day baseline in both stores, all categories, and all four forecast weeks. Because the tuned flexible model changed performance only slightly, these diagnostics describe the general behavior of the selected modeling approach.

### Stores

| Store | LightGBM WAPE | Baseline WAPE | Relative improvement |
| --- | ---: | ---: | ---: |
| CA_1 | 37.434% | 44.723% | 16.296% |
| CA_3 | 32.881% | 35.878% | 8.352% |

### Categories

| Category | LightGBM WAPE | Baseline WAPE | Interpretation |
| --- | ---: | ---: | --- |
| FOODS | 29.564% | 34.700% | strongest accuracy and a meaningful gain |
| HOBBIES | 67.455% | 70.806% | hardest category; intermittent and lumpy demand remains challenging |
| HOUSEHOLD | 49.361% | 52.723% | modest but consistent improvement |

### Forecast weeks

| Forecast week | LightGBM WAPE | Baseline WAPE |
| ---: | ---: | ---: |
| 1 | 34.769% | 38.492% |
| 2 | 34.520% | 38.213% |
| 3 | 34.126% | 41.642% |
| 4 | 35.664% | 39.912% |

Accuracy did not collapse at the far end of the 28-day horizon. However, week four had a -4.976% bias for the initial configuration, so longer-horizon underforecasting deserves attention in the final evaluation.

## 11. What the model learned

Gain-based feature importance showed that recent demand levels dominated the model:

| Feature | Mean gain share |
| --- | ---: |
| 28-day rolling mean | 32.510% |
| 56-day rolling mean | 19.156% |
| 14-day rolling mean | 18.930% |
| 7-day rolling mean | 9.004% |
| Product identity | 7.224% |
| 28-day lag | 3.026% |
| Day of week | 1.361% |

The four rolling means together contributed about 79.6% of total gain. Intuitively, the model first estimates each series' recent demand level, then adjusts that estimate using product identity, weekly timing, longer lags, events, seasonality, and price context.

Feature importance is not causal evidence. A high importance does not mean that changing that feature would directly cause sales to change, and correlated features can divide importance among themselves.

## 12. Final model decision

The development-stage model is locked as:

- model family: LightGBM
- objective: Poisson
- selected configuration: flexible
- number of leaves: 63
- minimum child samples: 50
- learning rate: 0.03
- row subsampling: 0.80
- column subsampling: 0.90
- L1 regularization: 0.20
- L2 regularization: 2.00
- maximum estimators: determined through early stopping

No additional tuning should be performed before the protected holdout evaluation. Continuing to optimize against the same five folds would increase the risk of validation overfitting for very small expected gains.

## 13. Required saved artifacts

The training notebook should finish by saving and reload-checking:

- the final LightGBM model trained on all development rows through `d_1913`;
- model metadata containing feature names, categorical levels, parameters, and the selected iteration count;
- flexible-model cross-validation predictions;
- fold and overall cross-validation metrics;
- the tuning comparison table.

Reloading the saved model and reproducing identical predictions is the final technical check for this notebook.

## 14. Next stage: protected holdout evaluation

The next notebook should be named `05_holdout_evaluation.ipynb`.

Its order of operations should be strict:

1. Load the saved model and metadata.
2. Construct forecast-safe features for `d_1914` through `d_1941` without loading their sales targets.
3. Validate that there are exactly 2,632 feature rows: 94 series × 28 days.
4. Generate and save predictions.
5. Only after predictions are frozen, load the protected actual sales.
6. Calculate overall, store, category, and forecast-week metrics.
7. Compare the holdout result with the 14-day baseline and the cross-validation range.

The final model should be accepted only if the holdout result confirms a meaningful and operationally reasonable improvement. If holdout performance deteriorates, the correct response is diagnosis—not additional tuning against the holdout.

## 15. Stage conclusion

The modeling stage achieved its objective. A forecast-safe Poisson LightGBM consistently beat the strongest simple baseline, won across stores, categories, forecast weeks, and all five original validation folds, and showed stable performance during a controlled tuning comparison.

The flexible configuration is the best development-stage candidate. The analysis phase for model selection is now complete; the project should proceed to one prediction-first evaluation on the untouched 28-day holdout.
