"""Prepare a small, documented sample for Homework 4: US Traffic Accidents.

Run from any working directory:
    python prepare_data.py "C:/path/to/US_Accidents_March23.csv"
    python prepare_data.py "C:/path/to/US_Accidents_March23.csv" --fraction 0.01

Outputs are saved beside this script by default (where app.py looks for them).
The original CSV is never modified. Source missing counts are calculated on all
rows, while record exclusions and deduplication apply ONLY to sampled rows.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
COLUMNS = [
    "ID", "State", "Severity", "Start_Time", "Start_Lat", "Start_Lng",
    "Weather_Condition", "Visibility(mi)", "Temperature(F)",
    "Wind_Speed(mph)",
]
NUMERIC_COLUMNS = [
    "Severity", "Start_Lat", "Start_Lng", "Visibility(mi)",
    "Temperature(F)", "Wind_Speed(mph)",
]
SEED = 42
CHUNK_SIZE = 250_000


def exclude_rows(frame: pd.DataFrame, reason: str, is_valid: pd.Series, report: dict) -> pd.DataFrame:
    """Count disjoint exclusions: each rejected row is counted once."""
    before = len(frame)
    kept = frame.loc[is_valid.fillna(False)].copy()
    report[reason] = int(before - len(kept))
    return kept


def weather_group(values: pd.Series) -> np.ndarray:
    """Categorize weather descriptions for readable visualizations."""
    s = values.fillna("Unknown").astype("string").str.lower()
    tests = [
        s.eq("unknown"),
        s.str.contains(r"thunder|t-storm", regex=True, na=False),
        s.str.contains(r"snow|sleet|ice|freez|blizzard|wintry|hail", regex=True, na=False),
        s.str.contains(r"rain|drizzle|shower", regex=True, na=False),
        s.str.contains(r"fog|mist|haze", regex=True, na=False),
        s.str.contains(r"cloud|overcast", regex=True, na=False),
        s.str.contains(r"fair|clear", regex=True, na=False),
        s.str.contains(r"wind|dust|smoke|sand", regex=True, na=False),
    ]
    names = [
        "Unknown", "Thunderstorm", "Snow/Ice", "Rain", "Fog/Mist/Haze",
        "Cloudy", "Clear/Fair", "Wind/Dust/Smoke",
    ]
    return np.select(tests, names, default="Other")


def run(csv_path: str | Path, output_dir: str | Path = PROJECT_DIR, fraction: float = 0.02) -> dict:
    """Create the sampled CSV, state/year aggregate, and preparation report."""
    if not 0 < fraction <= 1:
        raise ValueError("The sampling fraction must be between 0 (exclusive) and 1.")
    input_path = Path(csv_path).expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(
            f"Dataset not found: {input_path}\n"
            "Download US_Accidents_March23.csv from Kaggle, then pass its FULL file path."
        )
    output_path = Path(output_dir).expanduser().resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    source_rows = 0
    source_missing = pd.Series(0, index=COLUMNS, dtype="int64")
    sample_parts: list[pd.DataFrame] = []
    rng = np.random.default_rng(SEED)

    for chunk in pd.read_csv(input_path, usecols=COLUMNS, chunksize=CHUNK_SIZE, low_memory=False):
        source_rows += len(chunk)
        source_missing += chunk.isna().sum().reindex(COLUMNS, fill_value=0)
        selected = rng.random(len(chunk)) < fraction
        if selected.any():
            sample_parts.append(chunk.loc[selected].copy())

    if not sample_parts:
        raise ValueError("No rows were sampled; increase --fraction and try again.")
    df = pd.concat(sample_parts, ignore_index=True)
    sample_n = len(df)
    missing_before = df.isna().sum().to_dict()

    for name in NUMERIC_COLUMNS:
        df[name] = pd.to_numeric(df[name], errors="coerce")
    # US-Accidents timestamps are local wall times, with no timezone adjustment.
    df["Start_Time"] = pd.to_datetime(df["Start_Time"], errors="coerce", format="mixed")
    df["State"] = df["State"].astype("string").str.strip().str.upper()
    df["ID"] = df["ID"].astype("string").str.strip()

    excluded: dict[str, int] = {}
    df = exclude_rows(df, "Missing or blank ID", df["ID"].notna() & df["ID"].ne(""), excluded)
    df = exclude_rows(df, "Missing or blank State", df["State"].notna() & df["State"].ne(""), excluded)
    df = exclude_rows(df, "Invalid Start_Time", df["Start_Time"].notna(), excluded)
    df = exclude_rows(df, "Invalid Severity (must be 1 to 4)", df["Severity"].isin([1, 2, 3, 4]), excluded)
    df = exclude_rows(
        df, "Invalid latitude/longitude",
        df["Start_Lat"].between(-90, 90) & df["Start_Lng"].between(-180, 180), excluded,
    )

    before = len(df)
    df = df.drop_duplicates(subset="ID", keep="first").copy()
    excluded["Duplicate ID among sampled rows"] = int(before - len(df))
    if df.empty:
        raise ValueError("All sampled rows were excluded during cleaning.")

    df["Weather_Condition"] = (
        df["Weather_Condition"].astype("string").str.strip()
        .replace("", pd.NA).fillna("Unknown")
    )
    df["Weather_Group"] = weather_group(df["Weather_Condition"])

    invalid_negative_weather: dict[str, int] = {}
    for col in ("Visibility(mi)", "Wind_Speed(mph)"):
        invalid_negative_weather[col] = int((df[col] < 0).sum())
        df[col] = df[col].mask(df[col] < 0)

    df["Severity"] = df["Severity"].astype("int8")
    df["Year"] = df["Start_Time"].dt.year.astype("int16")
    df["Month"] = df["Start_Time"].dt.month.astype("int8")
    df["Hour"] = df["Start_Time"].dt.hour.astype("int8")
    df["Day_of_Week"] = df["Start_Time"].dt.day_name()
    df = df.sort_values("Start_Time").reset_index(drop=True)

    cleaned_path = output_path / "US_Accidents_Cleaned.csv"
    df.to_csv(cleaned_path, index=False)
    by_state_year = (
        df.groupby(["State", "Year"], observed=True).size()
        .reset_index(name="Sample_Accident_Count")
    )
    by_state_year.to_csv(output_path / "Accidents_By_State_Year.csv", index=False)

    report = {
        "source": "US-Accidents, https://www.kaggle.com/datasets/sobhanmoosavi/us-accidents/",
        "original_filename": input_path.name,
        "columns_selected": COLUMNS,
        "source_rows_inspected": int(source_rows),
        "source_missing_counts_selected_columns": {k: int(v) for k, v in source_missing.items()},
        "sampling_method": "Independent random row sampling streamed through the entire CSV",
        "sampling_fraction": float(fraction),
        "random_seed": SEED,
        "chunk_size": CHUNK_SIZE,
        "sampled_rows_before_cleaning": int(sample_n),
        "sample_missing_counts_before_cleaning": {k: int(v) for k, v in missing_before.items()},
        "sample_exclusions_applied_sequentially": excluded,
        "total_sampled_rows_excluded": int(sum(excluded.values())),
        "final_cleaned_sample_rows": int(len(df)),
        "final_sample_missing_counts": {k: int(v) for k, v in df.isna().sum().items()},
        "invalid_negative_weather_values_set_to_missing": invalid_negative_weather,
        "cleaned_sample_earliest_start": str(df["Start_Time"].min()),
        "cleaned_sample_latest_start": str(df["Start_Time"].max()),
        "cleaned_csv_size_mb": round(cleaned_path.stat().st_size / 1_048_576, 2),
        "missing_value_policy": {
            "essential_fields": "Reject sampled rows with missing ID, State, date/time, severity, or coordinates",
            "weather_condition": "Replace missing/blank descriptions with Unknown",
            "numeric_weather": "Keep missing readings as NaN; convert negative visibility/wind speed to NaN",
        },
        "notes": [
            "Missing-value counts for selected original columns are calculated across the FULL source file.",
            "Validity exclusions and duplicate checks apply to the RANDOM SAMPLE, not all 7.7M source records.",
            "Rows failing multiple criteria are counted only at their first failed criterion.",
            "Sampling is Bernoulli, so sample size is approximate rather than exactly a fixed percentage.",
            "Severity 1-4 measures traffic impact/delay, not injury/fatality severity.",
            "Original timestamps are treated as local wall times without timezone conversion.",
            "Weather descriptions were grouped heuristically; categories may be imperfect.",
            "Incomplete periods, changing reporting coverage, and lack of exposure data limit comparisons.",
            "All counts in the dashboard are from the cleaned sample, not estimates of population totals.",
        ],
    }
    report_path = output_path / "preparation_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Source records inspected: {source_rows:,}")
    print(f"Randomly sampled records: {sample_n:,}")
    print(f"Excluded from sample:     {sum(excluded.values()):,}")
    print(f"Final cleaned records:   {len(df):,}")
    print("\nExclusions (sequential, in sampled records):")
    for reason, count in excluded.items():
        print(f"  {reason}: {count:,}")
    print(f"\nOutput directory: {output_path}")
    print(f"Cleaned CSV size: {report['cleaned_csv_size_mb']} MB")
    for name in ("US_Accidents_Cleaned.csv", "Accidents_By_State_Year.csv", "preparation_report.json"):
        print(f"  {output_path / name}")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sample and clean US Accidents data for Streamlit Homework 4")
    parser.add_argument("csv_path", help="Full path to US_Accidents_March23.csv")
    parser.add_argument("--fraction", type=float, default=0.02, help="Random selection probability (default: 0.02)")
    parser.add_argument("--output-dir", default=str(PROJECT_DIR), help="Where to save outputs (default: app.py folder)")
    args = parser.parse_args()
    run(args.csv_path, args.output_dir, args.fraction)
