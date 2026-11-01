"""Causal univariate features, chronological splits and a separate annotation audit.

No anomaly labels are included in model-ready CSVs. The annotation audit is for
split feasibility only; it must not be used to tune models on test performance.
"""
import csv
from collections import defaultdict
from datetime import datetime
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]

def save_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"No rows to write: {path}")
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def read_series(path):
    groups = defaultdict(list)
    missing = invalid = out_of_order = 0
    previous = None
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        try:
            stamp = datetime.fromisoformat(row["timestamp"])
        except (ValueError, TypeError):
            raise ValueError(f"Invalid timestamp in {path.name}; resolve before proceeding")
        out_of_order += int(previous is not None and stamp < previous)
        previous = stamp
        if not row["value"].strip():
            missing += 1
            groups[stamp].append(float("nan"))
            continue
        try:
            value = float(row["value"])
        except ValueError:
            value = float("nan")
        if not math.isfinite(value):
            invalid += 1
        groups[stamp].append(value)
    stamps = sorted(groups)
    values = [statistics.median(groups[t]) if all(math.isfinite(v) for v in groups[t]) else float("nan") for t in stamps]
    quality = dict(raw_rows=len(rows), unique_rows=len(stamps), missing_values=missing,
                   invalid_values=invalid, duplicate_excess=len(rows)-len(stamps),
                   conflicting_duplicate_groups=sum(len(set(v)) > 1 for v in groups.values() if len(v)>1),
                   out_of_order_rows=out_of_order)
    return stamps, values, quality

def make_features(stamps, values, cadence, lags, windows):
    """Require a full, finite, regularly spaced preceding context; never fill gaps."""
    history = max(lags + windows)
    rows = []
    for i in range(history, len(values)):
        if not all(math.isfinite(v) for v in values[i-history:i+1]):
            continue
        if any((stamps[j]-stamps[j-1]).total_seconds() != cadence for j in range(i-history+1, i+1)):
            continue
        row = {"timestamp": stamps[i].isoformat(sep=" "), "target": values[i]}
        row.update({f"lag_{lag}": values[i-lag] for lag in lags})
        for window in windows:
            prior = values[i-window:i]
            row[f"mean_{window}"] = statistics.mean(prior)
            row[f"std_{window}"] = statistics.pstdev(prior)
        rows.append(row)
    return rows

def main():
    config = json.loads((ROOT / "config/preprocessing.json").read_text())
    labels = json.loads((ROOT / "data/raw/labels/combined_windows.json").read_text())
    audits, splits, events = [], [], []
    for path in sorted((ROOT / "data/raw/data/realAWSCloudwatch").glob("*.csv")):
        stamps, values, quality = read_series(path)
        a = int(len(stamps)*config["train_fraction"])
        b = int(len(stamps)*(config["train_fraction"]+config["development_fraction"]))
        if not 1 < a < b < len(stamps):
            raise ValueError("Invalid split sizes")
        cadence = statistics.median((stamps[i]-stamps[i-1]).total_seconds() for i in range(1,a))
        features = make_features(stamps, values, cadence, config["lags"], config["rolling_windows"])
        windows = [(datetime.fromisoformat(s), datetime.fromisoformat(e)) for s,e in labels[f"realAWSCloudwatch/{path.name}"]]
        bounds = [("train",0,a), ("development",a,b), ("test",b,len(stamps))]
        boundary_windows = [(s,e) for s,e in windows if any(s < t <= e for t in (stamps[a],stamps[b]))]
        eligible = {r["timestamp"] for r in features}
        quality.update(series=path.stem, cadence_seconds=cadence,
                       irregular_intervals=sum((stamps[i]-stamps[i-1]).total_seconds()!=cadence for i in range(1,len(stamps))),
                       annotation_windows=len(windows), annotated_readings=sum(any(s<=t<=e for s,e in windows) for t in stamps),
                       boundary_windows=len(boundary_windows), usable_rows=len(features))
        audits.append(quality)
        for name,lo,hi in bounds:
            selected = [r for r in features if stamps[lo] <= datetime.fromisoformat(r["timestamp"]) <= stamps[hi-1]]
            save_csv(ROOT / f"data/processed/{path.stem}/{name}.csv",selected)
            full = [(s,e) for s,e in windows if stamps[lo]<=s and e<=stamps[hi-1]]
            scorable = [r for r in selected if not any(s<=datetime.fromisoformat(r["timestamp"])<=e for s,e in boundary_windows)]
            splits.append(dict(series=path.stem,split=name,start=str(stamps[lo]),end=str(stamps[hi-1]),
                               readings=hi-lo,feature_rows=len(selected),complete_windows=len(full),
                               windows_with_eligible_readings=sum(any(s<=datetime.fromisoformat(r["timestamp"])<=e for r in selected) for s,e in full),
                               scorable_rows=len(scorable),exposure_days=len(scorable)*cadence/86400))
        for number,(s,e) in enumerate(windows):
            owner = next((name for name,lo,hi in bounds if stamps[lo]<=s and e<=stamps[hi-1]),"excluded_boundary")
            events.append(dict(series=path.stem,window_id=number,start=str(s),end=str(e),split=owner))
        # Separate evaluation metadata; never join this into training features.
        save_csv(ROOT / f"data/processed/{path.stem}/evaluation_mask.csv",[
            dict(timestamp=str(t),eligible=str(t) in eligible,
                 excluded_boundary=any(s<=t<=e for s,e in boundary_windows)) for t in stamps])
    save_csv(ROOT / "reports/tables/data_quality.csv",audits)
    save_csv(ROOT / "reports/tables/split_summary.csv",splits)
    save_csv(ROOT / "reports/tables/annotation_windows.csv",events)
    totals = {k:sum(r[k] for r in audits) for k in ["raw_rows","unique_rows","missing_values","invalid_values","duplicate_excess","conflicting_duplicate_groups","irregular_intervals","annotation_windows","annotated_readings","boundary_windows","usable_rows"]}
    totals["series"] = len(audits)
    totals["split_complete_windows"] = {name:sum(r["complete_windows"] for r in splits if r["split"]==name) for name in ["train","development","test"]}
    (ROOT / "reports/tables/totals.json").write_text(json.dumps(totals,indent=2)+"\n")
    print(json.dumps(totals,indent=2))

if __name__ == "__main__":
    main()
