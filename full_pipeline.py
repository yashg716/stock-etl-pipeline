import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DBT_DIR = ROOT / "stock_transforms"

def run_step(command, cwd=None, step_name=""):
    print(f"\n{'='*70}")
    print(f"RUNNING: {step_name}")
    print(f"COMMAND: {' '.join(command)}")
    print(f"{'='*70}\n")

    result = subprocess.run(command, cwd=cwd, shell=True)

    if result.returncode != 0:
        print(f"\nFAILED at step: {step_name}")
        sys.exit(result.returncode)

    print(f"\nCOMPLETED: {step_name}")

def main():
    print("\nStarting FULL pipeline...\n")

    run_step(
        ["python", "phase1.py"],
        cwd=ROOT,
        step_name="Phase 1 - Initial raw load"
    )

    run_step(
        ["python", "phase2.py"],
        cwd=ROOT,
        step_name="Phase 2 - Optimization / transformed load"
    )

    run_step(
        ["dbt", "run"],
        cwd=DBT_DIR,
        step_name="dbt run"
    )

    run_step(
        ["dbt", "test"],
        cwd=DBT_DIR,
        step_name="dbt test"
    )

    print("\nFULL pipeline finished successfully.")

if __name__ == "__main__":
    main()