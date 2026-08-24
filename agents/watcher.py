import pandas as pd

POTENTIAL_WEIGHTS = {
    "high": 1.0,
    "medium": 0.6,
    "low": 0.2,
}

def score_and_prioritize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["risk_score"] = df.apply(
        lambda row: row["amount_inr"] * POTENTIAL_WEIGHTS.get(row["recovery_potential"], 0),
        axis=1
    )
    df = df.sort_values("risk_score", ascending=False).reset_index(drop=True)
    return df

if __name__ == "__main__":
    from data_loader import load_data, summarize
    df = load_data()
    prioritized = score_and_prioritize(df)
    print("Top 5 highest priority records:\n")
    print(prioritized[["event_id", "customer_name", "amount_inr", "failure_reason", "recovery_potential", "risk_score"]].head())
