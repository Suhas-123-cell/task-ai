# Time Series Analysis and Forecasting

Time series data differs from the i.i.d. (independent and identically
distributed) assumption that underlies most standard machine learning:
observations are ordered in time and typically correlated with their own
recent past (autocorrelation), which means a random train/test split --
the default for most tabular ML -- leaks future information into training
and must be replaced with a chronological split (train on the past,
validate/test on a later period the model has not seen).

A time series is often decomposed into trend (long-run direction),
seasonality (a pattern that repeats at a fixed, known period, e.g. daily
or yearly), and residual/noise (whatever remains after removing trend and
seasonality). Stationarity -- roughly, that the series' statistical
properties (mean, variance, autocorrelation structure) do not change over
time -- is an assumption behind many classical forecasting models; a
non-stationary series (e.g. one with a clear upward trend) is often made
approximately stationary via differencing (modeling the change between
consecutive observations rather than the raw level) before fitting.

Classical models like ARIMA (AutoRegressive Integrated Moving Average)
combine autoregression (predicting a value from its own recent past
values), differencing (the "integrated" part, handling non-stationarity),
and a moving-average component (modeling the error term as a function of
past forecast errors). Exponential smoothing methods instead build a
forecast as a weighted average of past observations, with weights
decaying exponentially into the past, and can be extended (Holt-Winters)
to explicitly model trend and seasonality.

Modern approaches range from gradient-boosted trees over engineered
time-based features (lag values, rolling means/std, calendar features
like day-of-week) -- often a strong and simple baseline -- to
sequence models (RNNs, temporal convolutional networks, or
Transformer-based architectures) for problems with complex, long-range
temporal dependencies or many related series to forecast jointly.

Evaluation must respect time order: backtesting via a rolling-origin (or
"walk-forward") evaluation -- repeatedly training on data up to some
point in time and evaluating on the immediately following window, then
sliding that split point forward -- gives a much more honest estimate of
real deployed forecasting performance than a single, static train/test
split, because it tests the model's behavior across multiple different
forecast origins rather than just one.
