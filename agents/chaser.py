import random
from audit.logger import log_action

MAX_FOLLOW_UPS = 3

def run(row: dict) -> dict:
    event_id      = row["event_id"]
    customer_name = row["customer_name"]
    customer_email= row["customer_email"]
    amount        = row["amount_inr"]
    failure_reason= row["failure_reason"]
    retry_count   = int(row["retry_count"])

    if retry_count >= MAX_FOLLOW_UPS:
        log_action(
            event_id, customer_name, customer_email, amount, failure_reason,
            agent="chaser_agent",
            action="escalate",
            outcome="escalated",
            amount_recovered=0,
            reason=f"no response after {MAX_FOLLOW_UPS} follow-ups — escalated to human"
        )
        return {"event_id": event_id, "outcome": "escalated", "reason": "escalated to human"}

    # Simulate follow-up — 55% chance invoice gets paid
    success = random.random() < 0.55

    if success:
        log_action(
            event_id, customer_name, customer_email, amount, failure_reason,
            agent="chaser_agent",
            action="invoice_followup",
            outcome="recovered",
            amount_recovered=amount,
            reason=f"invoice paid after follow-up #{retry_count + 1}"
        )
        return {"event_id": event_id, "outcome": "recovered", "amount_recovered": amount}
    else:
        log_action(
            event_id, customer_name, customer_email, amount, failure_reason,
            agent="chaser_agent",
            action="invoice_followup",
            outcome="failed",
            amount_recovered=0,
            reason=f"no payment after follow-up #{retry_count + 1}"
        )
        return {"event_id": event_id, "outcome": "failed", "amount_recovered": 0}
