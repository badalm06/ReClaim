from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

RECOVERY_CATEGORIES = {
    "payment_retry":      ["card_declined", "wrong_cvv", "network_timeout", "payment_gateway_error", "upi_timeout", "insufficient_funds"],
    "checkout_nudge":     ["checkout_abandoned"],
    "subscription_retry": ["subscription_lapsed", "mandate_rejected"],
    "receivables_chase":  ["invoice_overdue"],
    "unrecoverable":      [],
}

def get_recovery_category(row: dict) -> str:
    if row.get("permanently_blocked") == True or str(row.get("permanently_blocked")).lower() == "true":
        return "unrecoverable"

    failure_reason = row.get("failure_reason", "")
    for category, reasons in RECOVERY_CATEGORIES.items():
        if failure_reason in reasons:
            return category

    llm = ChatOpenAI(model="gpt-4o-mini", max_tokens=50)
    prompt = f"""You are a payment recovery classifier.
Given this failed payment, return ONLY one of these categories (no explanation):
payment_retry, checkout_nudge, subscription_retry, receivables_chase, unrecoverable

failure_reason: {row.get('failure_reason')}
failure_type: {row.get('failure_type')}
retry_count: {row.get('retry_count')}
permanently_blocked: {row.get('permanently_blocked')}"""

    response = llm.invoke([HumanMessage(content=prompt)])
    category = response.content.strip().lower()
    return category if category in RECOVERY_CATEGORIES else "unrecoverable"

if __name__ == "__main__":
    test_cases = [
        {"failure_reason": "card_declined",       "failure_type": "payment_failure",      "retry_count": 1, "permanently_blocked": False},
        {"failure_reason": "checkout_abandoned",  "failure_type": "checkout_dropout",     "retry_count": 0, "permanently_blocked": False},
        {"failure_reason": "bank_blocked",        "failure_type": "payment_failure",      "retry_count": 3, "permanently_blocked": True},
        {"failure_reason": "invoice_overdue",     "failure_type": "receivable",           "retry_count": 0, "permanently_blocked": False},
        {"failure_reason": "subscription_lapsed", "failure_type": "subscription_failure", "retry_count": 1, "permanently_blocked": False},
    ]
    print("Diagnosis test:\n")
    for case in test_cases:
        category = get_recovery_category(case)
        print(f"  {case['failure_reason']:<28} → {category}")
