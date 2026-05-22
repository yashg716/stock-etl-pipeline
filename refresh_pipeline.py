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
    print("\nStarting REFRESH pipeline...\n")

    run_step(
        ["python", "auto_refresh.py"],
        cwd=ROOT,
        step_name="Auto refresh - load only new data"
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

    print("\nREFRESH pipeline finished successfully.")

if __name__ == "__main__":
    main()