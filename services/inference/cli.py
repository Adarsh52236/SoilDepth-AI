"""
SoilDepth-AI — Model 1 Production Inference CLI
Author: Senior Data Engineer & ML Pipeline Developer, SoilDepth-AI
Purpose: Command-line interface to execute Model 1 inference on prepared daily inputs,
         single records, or CSV batches, outputting standardized JSON responses.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pandas as pd
from services.inference.predictor import Model1Predictor
from services.modelling.config import PROCESSED_DATA_DIR, STATION_ID


def run_cli():
    parser = argparse.ArgumentParser(
        description="SoilDepth-AI Model 1 Production Inference CLI (Station AAMU-JTG)"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        default=None,
        help="Path to input features CSV file for batch inference"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Path to output JSON file (prints to stdout if omitted)"
    )
    parser.add_argument(
        "--csv-out",
        type=str,
        default=None,
        help="Optional path to export predictions as a flat CSV file"
    )
    parser.add_argument(
        "--date", "-d",
        type=str,
        default=None,
        help="Filter batch inference to a single specific date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--models-dir",
        type=str,
        default=None,
        help="Custom path to models directory (defaults to models/baselines/AAMU-JTG)"
    )
    parser.add_argument(
        "--catalog",
        action="store_true",
        help="Print operational model catalog metadata and exit"
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Run inference on a 5-day demonstration sample from the test set"
    )

    args = parser.parse_args()

    predictor = Model1Predictor(models_dir=args.models_dir)

    if args.catalog:
        catalog = predictor.get_model_catalog()
        print(catalog.model_dump_json(indent=2))
        return

    # Determine input data source
    if args.sample or (args.input is None):
        sample_csv = PROCESSED_DATA_DIR / f"{STATION_ID}_all_depths_features_daily.csv"
        if not sample_csv.exists():
            sample_csv = PROCESSED_DATA_DIR / f"{STATION_ID}_sm_20cm_daily.csv"

        if not sample_csv.exists():
            print(f"Error: Sample data file not found at {sample_csv}", file=sys.stderr)
            sys.exit(1)

        df = pd.read_csv(sample_csv)
        # Select 5 sample days from the holdout test set (2023)
        df_sample = df[(df["date_utc"] >= "2023-06-01") & (df["date_utc"] <= "2023-06-05")].copy()
        if df_sample.empty:
            df_sample = df.tail(5).copy()

        print(f"Running inference on {len(df_sample)} sample records from {sample_csv.name}...\n", file=sys.stderr)
        batch_response = predictor.predict_dataframe(df_sample)
    else:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: Input file not found: {input_path}", file=sys.stderr)
            sys.exit(1)

        df = pd.read_csv(input_path)
        if args.date:
            date_col = "date_utc" if "date_utc" in df.columns else ("date" if "date" in df.columns else None)
            if not date_col:
                print(f"Error: Date column not found in input CSV to filter by {args.date}", file=sys.stderr)
                sys.exit(1)
            df = df[df[date_col] == args.date]
            if df.empty:
                print(f"Error: No records found for date {args.date}", file=sys.stderr)
                sys.exit(1)

        batch_response = predictor.predict_dataframe(df)

    json_str = batch_response.model_dump_json(indent=2)

    # Export to output file if specified
    if args.output:
        out_p = Path(args.output)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            f.write(json_str)
        print(f"JSON prediction response saved to: {out_p}", file=sys.stderr)
    else:
        print(json_str)

    # Optional flat CSV output
    if args.csv_out:
        csv_rows = []
        for r in batch_response.results:
            csv_rows.append({
                "date": r.date,
                "station_id": r.station_id,
                "sm_5cm_pred_m3_m3": r.predictions["sm_5cm"].volumetric_soil_moisture,
                "sm_10cm_pred_m3_m3": r.predictions["sm_10cm"].volumetric_soil_moisture,
                "sm_20cm_pred_m3_m3": r.predictions["sm_20cm"].volumetric_soil_moisture,
                "sm_50cm_pred_m3_m3": r.predictions["sm_50cm"].volumetric_soil_moisture,
                "status": r.status,
            })
        df_out = pd.DataFrame(csv_rows)
        csv_p = Path(args.csv_out)
        csv_p.parent.mkdir(parents=True, exist_ok=True)
        df_out.to_csv(csv_p, index=False)
        print(f"Flat CSV predictions saved to: {csv_p}", file=sys.stderr)


if __name__ == "__main__":
    run_cli()

