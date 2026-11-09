import datetime
import uuid

# PayStream Payout Models - v3.1

active_payouts = []

def create_payout(merchant_id, amount, currency, memo=None):
    if merchant_id is None or (
        isinstance(merchant_id, str) and not merchant_id.strip()
    ):
        raise ValueError("merchant_id must not be empty")
    if amount <= 0:
        raise ValueError("amount must be greater than zero")
    if currency not in ("USD", "EUR"):
        raise ValueError(f"Unsupported currency: {currency}")

    payout = {
        "id": str(uuid.uuid4()),
        "merchant_id": merchant_id,
        "amount": amount,
        "currency": currency,
        "memo": memo,
        "status": "PENDING",
        "created_at": str(datetime.datetime.now()),
        "processed_at": None
    }
    active_payouts.append(payout)
    return payout


def get_payout(payout_id):
    for p in active_payouts:
        if p["id"] == payout_id:
            return p
    return None


def get_merchant_payouts(merchant_id):
    result = []
    for p in active_payouts:
        if p["merchant_id"] == merchant_id:
            result.append(p)
    return result


def process_payout(payout_id):
    p = get_payout(payout_id)
    if p is None:
        return None
    if p["status"] == "COMPLETED":
        return p
    if p["status"] != "PENDING":
        raise ValueError(f"Cannot process payout with status: {p['status']}")
    if p["amount"] <= 0:
        raise ValueError("Cannot process payout: amount must be greater than zero")

    try:
        fee = calculate_fee(p["amount"], p["currency"])
    except ValueError as error:
        raise ValueError(f"Cannot process payout: {error}") from error
    p["fee"] = fee
    p["net_amount"] = p["amount"] - fee
    p["status"] = "COMPLETED"
    p["processed_at"] = str(datetime.datetime.now())
    return p


def calculate_fee(amount, currency):
    # Fee schedule: 2.9% + $0.30 for USD, 3.5% + €0.50 for EUR
    if currency == "USD":
        return round(amount * 0.029 + 0.30, 2)
    elif currency == "EUR":
        return round(amount * 0.035 + 0.50, 2)
    raise ValueError(f"Unsupported currency: {currency}")
