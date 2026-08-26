import random
from audit.logger import log_action

MAX_RETRIES = 3

def run(row: dict) -> dict:
    event_id      = row["event_id"]
    customer_name = row["customer_name"]
    customer_email= row["customer_email"]
    amount        = row["amount_inr"]
    failure_reason= row["failure_reason"]
    retry_count   = int(row["retry_count"])
    blocked       = str(row.get("permanently_blocked", "False")).lower() == "true"

    # Graceful failure — stop immediately
    if blocked or retry_count >= MAX_RETRIES:
        reason = "permanently blocked by bank" if blocked else f"max retries ({MAX_RETRIES}) reached"
        log_action(
            event_id, customer_name, customer_email, amount, failure_reason,
            agent="retry_agent",
            action="skip",
            outcome="unrecoverable",
            amount_recovered=0,
            reason=reason
        )
        return {"event_id": event_id, "outcome": "unrecoverable", "reason": reason}

    # Simulate retry — 70% success for high potential, 40% for medium
    potential   = row.get("recovery_potential", "medium")
    success_rate= 0.70 if potential == "high" else 0.40
    success     = random.random() < success_rate

    if success:
        log_action(
            event_id, customer_name, customer_email, amount, failure_reason,
            agent="retry_agent",
            action="payment_retry",
            outcome="recovered",
            amount_recovered=amount,
            reason=f"retry succeeded on attempt {retry_count + 1}"
        )
        return {"event_id": event_id, "outcome": "recovered", "amount_recovered": amount}
    else:
        log_action(
            event_id, customer_name, customer_email, amount, failure_reason,
            agent="retry_agent",
            action="payment_retry",
            outcome="failed",
            amount_recovered=0,
            reason=f"retry failed on attempt {retry_count + 1}"
        )
        return {"event_id": event_id, "outcome": "failed", "amount_recovered": 0}
