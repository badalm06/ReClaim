import pandas as pd
from pathlib import Path

DATA_PATH = Path(__file__).parent / "data" / "razorpay_failed_payments.csv"

def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    return df

def summarize(df: pd.DataFrame) -> None:
    total = len(df)
    revenue_at_risk = df["amount_inr"].sum()

    print(f"\n{'='*45}")
    print(f"  RECLAIM — Failed Payment Batch Summary")
    print(f"{'='*45}")
    print(f"  Total records       : {total}")
    print(f"  Revenue at risk     : ₹{revenue_at_risk:,.0f}")
    print(f"\n  Breakdown by failure type:")
    for ftype, count in df["failure_type"].value_counts().items():
        print(f"    {ftype:<28} {count} records")
    print(f"\n  Breakdown by recovery potential:")
    for pot, count in df["recovery_potential"].value_counts().items():
        print(f"    {pot:<28} {count} records")
    print(f"\n  Permanently blocked : {df['permanently_blocked'].sum()} records")
    print(f"{'='*45}\n")

if __name__ == "__main__":
    df = load_data()
    summarize(df)
