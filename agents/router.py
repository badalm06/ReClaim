from agents.retry  import run as retry_run
from agents.nudge  import run as nudge_run
from agents.chaser import run as chaser_run
from audit.logger  import log_action

def route(row: dict, category: str) -> dict:
    if category == "payment_retry":
        return retry_run(row)
    elif category == "checkout_nudge":
        return nudge_run(row)
    elif category in ("subscription_retry", "receivables_chase"):
        return chaser_run(row)
    else:
        # unrecoverable — log and skip
        log_action(
            row["event_id"], row["customer_name"], row["customer_email"],
            row["amount_inr"], row["failure_reason"],
            agent="router",
            action="skip",
            outcome="unrecoverable",
            amount_recovered=0,
            reason=f"diagnosed as unrecoverable: {row.get('failure_reason')}"
        )
        return {"event_id": row["event_id"], "outcome": "unrecoverable", "reason": "unrecoverable"}
