# Data Collection and Preprocessing

Evaluating Forecast-Based Alerts for Cloud Infrastructure Monitoring
Mamadou Kaba | COEN 6314 | November 1, 2026

Infrastructure alerts must balance false alarms against missed anomalies. My project compares rolling statistical thresholds, persistence forecasting and Random Forest forecasting to assess whether learned forecasts improve this balance. This milestone prepares a common dataset and chronological evaluation periods so differences in alert performance can be attributed to the methods rather than inconsistent data handling.

## Data obtained and its role in the comparison

I downloaded all 17 series in the Numenta Anomaly Benchmark (NAB) realAWSCloudwatch subset and its combined anomaly-window annotations [1]. The historical recordings cover CPU, network, disk and request metrics. The source repository provides an MIT license permitting reuse subject to retaining its copyright and permission notice. I retained the license and original files and recorded the source revision and file checksums for reproducibility.

Each series supplies a timestamp and one metric value. Persistence will forecast the next reading from the previous value; Random Forest will use recent readings and rolling statistics. Their forecast errors will produce anomaly scores after the new reading arrives. The rolling-threshold baseline will compare that reading with recent level and variability. Anomaly windows are separate evaluation labels, never model inputs; this is anomaly detection, not advance failure prediction.

## Data quality and preparation decisions

| Observed finding | Preparation decision and reason |
| --- | --- |
| 17 series; 67,740 readings; 1.86 MB of CSVs | Keep series separate because metric units and operating patterns differ. |
| No missing or non-finite values; 19 irregular intervals | Do not fill or interpolate gaps. Require complete, regularly spaced history so artificial values do not affect alerts. |
| 22 excess duplicate rows across two series; one conflicting timestamp | Use the median at each duplicate timestamp to avoid repeated observations and an arbitrary choice among conflicting values. |
| 30 windows; 6,312 of 67,718 unique readings inside windows (9.32%) | Keep the natural imbalance and unusual values. Removing extremes or balancing classes could distort false-alarm and detection evaluation. |

The typical cadence is five minutes, so faster changes are not resolved. Timezones and duplicate arrival order are unspecified; I preserve timestamps and assume same-timestamp readings are available together. These short historical recordings cannot establish current production reliability. Annotation windows provide timing tolerance, not verified incident durations; their 9.32% coverage is not an incident rate.

## Features and fair comparison

I created lags of 1, 2, 3, 6 and 12 readings and the mean and population standard deviation of the preceding 6 and 12 readings. These give Random Forest recent level and variability over five minutes to one hour; lag 1 also supplies persistence, while rolling statistics support the threshold baseline. All features exclude the current target reading. No scaling is fitted because the tree model does not require it and each series will be modelled separately.

Cadence is estimated from training timestamps only. Predictions require a finite target and 12 preceding readings at that cadence. Warm-up and interrupted histories exclude 410 unique readings, leaving 67,308 forecast examples. All methods will use these same eligible timestamps, even though persistence needs less history, to avoid giving one method an easier evaluation set. Any later learned preprocessing will be fitted on training data only.

## Chronological split and leakage prevention

Within each series, I assigned the first 20% of unique timestamps to training, the next 40% to development (validation) and the final 40% to testing. There is no random shuffle or pooling across series. Earlier observations may supply history at the start of a later period, as they would in sequential monitoring.

| Period | Forecast examples | Complete windows | Series with windows |
| --- | --- | --- | --- |
| Training | 13,296 | 0 | 0 |
| Development | 26,956 | 13 | 11 |
| Test | 27,056 | 13 | 11 |

This split retains events for development and testing at the cost of limited training history: 236-931 usable examples per series, most commonly 794. Four windows cross boundaries and are excluded from scoring and its monitored-time denominator, but their readings remain in observed history. Zero complete training windows therefore does not establish anomaly-free training. The regression target is a metric value, so labelled anomalies are not required for fitting.

The feasibility audit inspected annotation locations and counts, including the test period, before model fitting. No test performance has been calculated. The split is now fixed. Models will be fitted on training data; feature choices, model settings and alert thresholds will be selected on development data. Test labels will be used for scoring only after these choices are frozen.

## Progress and remaining limitations

Acquisition, cleaning and feature generation are complete, with per-series audit tables saved. Four checks passed for causal features, gap handling, missing-value handling and chronological split separation. Models and alert-performance evaluation are not yet implemented, and no access problem remains.

The main constraint is only 13 complete test windows across 11 series. I will keep all series for false-alert analysis, mark detection rates undefined where no events exist, and report per-series results plus equal-weight summaries with denominators. Gap exclusions and the conflicting duplicate remain measurement limitations; I will retain their audit records and identify affected series when interpreting errors. Next, I will implement shared alert-episode rules and the three methods, select settings on development data, and evaluate false alert episodes per monitored day, windows detected and detection timing at comparable false-alert rates. Conclusions will remain limited to this benchmark.

[1] Numenta Anomaly Benchmark. https://github.com/numenta/NAB. Exact revision and checksums: config/data_manifest.json.
