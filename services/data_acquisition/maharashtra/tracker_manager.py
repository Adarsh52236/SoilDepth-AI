"""
SoilDepth-AI — Phase 3 Operational Ground-Truth Tracker Management Utility
Author: Senior Geospatial Data Engineer & Pipeline Developer, SoilDepth-AI
Purpose: Validates and manages the 5 Maharashtra institutional ground-truth requests.
         Enforces anti-fabrication gates (verifying that no request is marked SUBMITTED
         without tangible evidence files archived in the repository).
"""

import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
METADATA_DIR = REPO_ROOT / "dataset" / "Maharashtra" / "metadata"
ACQUISITION_DIR = REPO_ROOT / "dataset" / "Maharashtra" / "acquisition"
TRACKER_CSV = METADATA_DIR / "operational_ground_truth_tracker.csv"

VALID_STATUSES = [
    "DRAFTED",
    "APPROVED",
    "SUBMITTED",
    "ACKNOWLEDGED",
    "DATA_RECEIVED",
    "DATA_VERIFIED",
]

EXPECTED_REQUEST_IDS = [
    "SOILDEPTH-REQ-2026-001",
    "SOILDEPTH-REQ-2026-002",
    "SOILDEPTH-REQ-2026-003",
    "SOILDEPTH-REQ-2026-004",
    "SOILDEPTH-REQ-2026-005",
]


class GroundTruthTrackerManager:
    """
    Operational manager for Maharashtra institutional ground-truth acquisition.
    """

    def __init__(self, tracker_csv: Optional[Path] = None, acquisition_dir: Optional[Path] = None):
        self.tracker_csv = tracker_csv or TRACKER_CSV
        self.acquisition_dir = acquisition_dir or ACQUISITION_DIR

    def load_tracker(self) -> pd.DataFrame:
        if not self.tracker_csv.exists():
            raise FileNotFoundError(f"Operational tracker not found: {self.tracker_csv}")
        return pd.read_csv(self.tracker_csv)

    def validate_tracker(self) -> Dict[str, Any]:
        """
        Validates schema, valid statuses, and enforces anti-fabrication evidence rules.
        """
        issues: List[str] = []
        df = self.load_tracker()

        # 1. Row count & request IDs
        if len(df) != 5:
            issues.append(f"Expected 5 institutional requests, found {len(df)}")

        req_ids = df["request_id"].tolist()
        for exp in EXPECTED_REQUEST_IDS:
            if exp not in req_ids:
                issues.append(f"Missing expected request ID: {exp}")

        # 2. Status validity & anti-fabrication evidence checks
        for _, row in df.iterrows():
            req_id = str(row["request_id"])
            status = str(row["submission_status"]).strip().upper()

            if status not in VALID_STATUSES:
                issues.append(f"Request {req_id} has invalid status '{status}'. Must be one of {VALID_STATUSES}")

            ev_dir = REPO_ROOT / str(row.get("evidence_directory", ""))
            if not ev_dir.exists():
                issues.append(f"Request {req_id} evidence directory does not exist: {ev_dir}")
                continue

            # Check evidence required for SUBMITTED and higher states
            if status in ["SUBMITTED", "ACKNOWLEDGED", "DATA_RECEIVED", "DATA_VERIFIED"]:
                receipts = [f for f in (ev_dir / "receipts").glob("*") if f.name != ".gitkeep"]
                emails = [f for f in (ev_dir / "email_evidence").glob("*") if f.name != ".gitkeep"]
                if len(receipts) == 0 and len(emails) == 0:
                    issues.append(
                        f"Anti-Fabrication Violation: Request {req_id} is marked '{status}', "
                        f"but no evidence files exist in '{ev_dir / 'receipts'}' or '{ev_dir / 'email_evidence'}'."
                    )

            # Check data files required for DATA_RECEIVED and DATA_VERIFIED
            if status in ["DATA_RECEIVED", "DATA_VERIFIED"]:
                datasets = [f for f in (ev_dir / "received_datasets").glob("*") if f.name != ".gitkeep"]
                if len(datasets) == 0:
                    issues.append(
                        f"Anti-Fabrication Violation: Request {req_id} is marked '{status}', "
                        f"but no data files exist in '{ev_dir / 'received_datasets'}'."
                    )

        return {
            "is_valid": len(issues) == 0,
            "total_requests": len(df),
            "issues": issues,
        }

    def print_summary(self) -> None:
        """Prints a human-readable operational summary."""
        df = self.load_tracker()
        print("\n" + "=" * 90)
        print(" SOILDEPTH-AI — PHASE 3 OPERATIONAL GROUND-TRUTH ACQUISITION TRACKER")
        print("=" * 90)
        print(f" {'Request ID':<24} | {'Status':<14} | {'Institution':<30} | {'Follow-up':<14}")
        print("-" * 90)
        for _, r in df.iterrows():
            inst = str(r['institution'])[:30]
            print(f" {r['request_id']:<24} | {r['submission_status']:<14} | {inst:<30} | {r['follow_up_date']:<14}")
        print("=" * 90 + "\n")


def main():
    parser = argparse.ArgumentParser(description="SoilDepth-AI Ground-Truth Tracker Utility")
    parser.add_argument("--validate", action="store_true", help="Run high-assurance integrity validation")
    parser.add_argument("--summary", action="store_true", help="Print operational summary table")
    args = parser.parse_args()

    mgr = GroundTruthTrackerManager()
    if args.validate or (not args.validate and not args.summary):
        res = mgr.validate_tracker()
        if res["is_valid"]:
            print(f"[OK] Operational tracker is valid. All {res['total_requests']} requests adhere to protocol.")
        else:
            print(f"[ERROR] Tracker validation failed with {len(res['issues'])} issues:")
            for iss in res["issues"]:
                print(f"  - {iss}")

    if args.summary:
        mgr.print_summary()


if __name__ == "__main__":
    main()
