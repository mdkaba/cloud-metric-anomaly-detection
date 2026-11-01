# Evaluation protocol for the modelling milestone

Data preparation and chronological splits are implemented. The methods, alert
episode matching and evaluation described below remain to be implemented.

1. Fit a separate forecasting model per series using training CSVs only. Persistence
   predicts `lag_1`; Random Forest uses the lag/rolling predictors. The rolling
   baseline compares the new reading with a preceding rolling centre and spread.
   Scores and alerts are produced after the new reading arrives.
2. Keep model feature selection, hyperparameters, scale floors and alert thresholds
   confined to training/development. Freeze all settings before final testing.
   The preliminary annotation audit is disclosed; do not evaluate test scores
   during development. Do not use annotation-window columns as predictors.
3. Group consecutive flagged eligible readings at the expected cadence into an
   episode. A non-alert, missing interval, excluded interval or split boundary
   ends an episode. Apply the identical rule to all methods. Episodes must not
   bridge periods where predictions are ineligible.
4. Match an episode to the first complete annotation window containing one of
   its flagged timestamps. Each episode can match at most one window. A window
   is detected if at least one episode matches it; repeated matches do not add
   detections. Episodes with no match are false alert episodes. Detection time
   is the first flagged timestamp in that window, relative to its start. This
   is benchmark timing, not time before a real infrastructure failure.
5. Report false alert episodes per eligible monitored day, detected/total complete
   windows, missed windows and timing for matched windows. Exclude the four
   boundary-crossing windows and their exposure consistently. Show detection
   denominators and timing sample sizes; timing alone omits missed anomalies.
6. Compare development operating points at similar false-alert budgets, then
   report the actual achieved test false-alert rates without retuning on test.
   Choose the numeric budgets and a deterministic tie-break before model search.
   If rates cannot be closely matched, report the mismatch rather than claiming
   a matched comparison.
7. Publish per-series results and an equal-weight macro summary. Detection is
   undefined for series without complete windows; exclude those only from the
   detection macro average and disclose its denominator. Keep these series in
   false-alert summaries. Report micro counts as secondary context, not as the
   only comparison. Count metadata alone is not proof of statistical power.

Before final evaluation, add unit tests for episode grouping, boundary/gap resets,
matching, repeated alerts, no-event series and exposure denominators.
