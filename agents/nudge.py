import random
from audit.logger import log_action

MAX_NUDGES = 2

def run(row: dict) -> dict:
    event_id      = row["event_id"]
    customer_name = row["customer_name"]
    customer_email= row["customer_email"]
    amount        = row["amount_inr"]
    failure_reason= row["failure_reason"]
    retry_count   = int(row["retry_count"])

    if retry_count >= MAX_NUDGES:
        log_action(
            event_id, customer_name, customer_email, amount, failure_reason,
            agent="nudge_agent",
            action="skip",
            outcome="unrecoverable",
            amount_recovered=0,
            reason=f"max nudges ({MAX_NUDGES}) already sent"
        )
        return {"event_id": event_id, "outcome": "unrecoverable", "reason": "max nudges reached"}

    # Simulate nudge — 50% chance customer completes checkout
    success = random.random() < 0.50

    if success:
        log_action(
            event_id, customer_name, customer_email, amount, failure_reason,
            agent="nudge_agent",
            action="checkout_reminder",
            outcome="recovered",
            amount_recovered=amount,
            reason="customer completed checkout after reminder"
        )
        return {"event_id": event_id, "outcome": "recovered", "amount_recovered": amount}
    else:
        log_action(
            event_id, customer_name, customer_email, amount, failure_reason,
            agent="nudge_agent",
            action="checkout_reminder",
            outcome="failed",
            amount_recovered=0,
            reason="customer did not respond to reminder"
        )
        return {"event_id": event_id, "outcome": "failed", "amount_recovered": 0}
