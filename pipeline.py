import random
import pandas as pd
from data_loader import load_data
from agents.watcher import score_and_prioritize
from agents.diagnosis import get_recovery_category
from agents.router import route
from audit.logger import init_db, clear_logs, get_all_logs

random.seed(42)

def run_pipeline(progress_callback=None) -> dict:
    init_db()
    clear_logs()

    df = load_data()
    df = score_and_prioritize(df)
    records = df.to_dict(orient="records")
    total = len(records)

    results = []
    total_recovered = 0
    total_at_risk   = df["amount_inr"].sum()

    print(f"\nStarting pipeline — {total} records to process\n")

    for i, row in enumerate(records):
        category = get_recovery_category(row)
        result   = route(row, category)
        results.append(result)

        outcome  = result.get("outcome", "unknown")
        recovered = result.get("amount_recovered", 0)
        total_recovered += recovered

        print(f"  [{i+1:02d}/{total}] {row['event_id']} | {row['failure_reason']:<28} | {category:<22} | {outcome}")

        if progress_callback:
            progress_callback(i + 1, total, row, outcome)

    # Summary
    outcomes = [r["outcome"] for r in results]
    n_recovered    = outcomes.count("recovered")
    n_failed       = outcomes.count("failed")
    n_unrecoverable= outcomes.count("unrecoverable")
    n_escalated    = outcomes.count("escalated")
    recovery_rate  = (n_recovered / total) * 100

    summary = {
        "total":            total,
        "recovered":        n_recovered,
        "failed":           n_failed,
        "unrecoverable":    n_unrecoverable,
        "escalated":        n_escalated,
        "total_at_risk":    total_at_risk,
        "total_recovered":  total_recovered,
        "recovery_rate":    round(recovery_rate, 1),
    }

    print(f"\n{'='*50}")
    print(f"  PIPELINE COMPLETE")
    print(f"{'='*50}")
    print(f"  Total processed    : {total}")
    print(f"  Recovered          : {n_recovered}  ({recovery_rate:.1f}%)")
    print(f"  Failed             : {n_failed}")
    print(f"  Unrecoverable      : {n_unrecoverable}")
    print(f"  Escalated          : {n_escalated}")
    print(f"  Revenue at risk    : ₹{total_at_risk:,.0f}")
    print(f"  Revenue recovered  : ₹{total_recovered:,.0f}")
    print(f"{'='*50}\n")

    return summary

if __name__ == "__main__":
    run_pipeline()
