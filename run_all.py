"""Run the whole pipeline end to end.

    python run_all.py

Steps: download -> clean -> explore -> snapshots -> validation comparison
       -> final locked test + follow-up list.
"""
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
STEPS = [
    "download_data.py",
    "clean_data.py",
    "explore.py",
    "snapshots.py",
    "evaluate_validation.py",
    "final_test.py",
    "eda_risk.py",
    "score_latest.py",
]

for step in STEPS:
    print(f"\n{'=' * 60}\n>>> {step}\n{'=' * 60}")
    r = subprocess.run([sys.executable, str(SRC / step)], cwd=SRC)
    if r.returncode != 0:
        sys.exit(f"Step {step} failed")
print("\nPipeline complete. See outputs/ for figures and the follow-up list.")
