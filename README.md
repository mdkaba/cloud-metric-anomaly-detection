# Evaluating Forecast-Based Alerts for Cloud Infrastructure Monitoring

Individual COEN 6314 project by Mamadou Kaba. Compare rolling statistical
thresholds, persistence forecasts and Random Forest forecasts on AWS monitoring
time series from the Numenta Anomaly Benchmark (NAB).

Forecast residuals detect unusual readings **after they arrive**. This project
does not predict future failures or equate benchmark annotations with incidents.

## Run the preprocessing milestone

Python 3.11 or newer; no external packages or AWS account needed:

```powershell
python src/download_data.py
python src/prepare_data.py
python -m unittest discover -s tests -v
```

Run commands from this repository. The first command needs internet access on
first use. It downloads the exact NAB revision in `config/data_manifest.json`
and verifies SHA-256 checksums. Subsequent runs can use verified local files.

## Outputs

- `data/raw/`: original data, annotations, source README and MIT license.
- `data/processed/<series>/`: chronological train/development/test feature CSVs
  and a separate evaluation eligibility mask. Raw/processed data are ignored by Git.
- `reports/tables/`: reproducible quality, event-count and split audits.
- `reports/data_collection_and_preprocessing.md`: findings and preparation decisions.
- `config/preprocessing.json`: frozen initial split and feature choices.

`target` is the reading being forecast, never an input feature. Anomaly labels
are kept separate. Use the lag/mean/std columns as predictors. Each series will
have its own model; metrics with different units are not pooled.

## Implementation

Completed: dataset download and checksum verification, data-quality audit,
duplicate handling, lag and rolling features, chronological splits, and
preprocessing tests.

Remaining: implement the rolling-threshold, persistence and Random Forest
methods; group and match alert episodes; select settings and thresholds on
development data; and evaluate the frozen methods on the test periods.

## Source and reuse

Source: https://github.com/numenta/NAB, `data/realAWSCloudwatch` and
`labels/combined_windows.json`. The source repository supplies an MIT license;
the downloader retains it with the raw data. Preserve its copyright and
permission notice when redistributing source material.

Reference: Ahmad, S., Lavin, A., Purdy, S., & Agha, Z. (2017).
Unsupervised real-time anomaly detection for streaming data. Neurocomputing.
https://doi.org/10.1016/j.neucom.2017.04.070
