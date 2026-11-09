import pytest
from payout_models import (
    create_payout, get_payout, process_payout,
    calculate_fee, get_merchant_payouts, active_payouts
)
from payout_api import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def clear_payouts():
    active_payouts.clear()
    yield
    active_payouts.clear()


# --- Model Tests ---

def test_create_payout():
    p = create_payout("M001", 100.00, "USD")
    assert p["merchant_id"] == "M001"
    assert p["amount"] == 100.00
    assert p["status"] == "PENDING"


@pytest.mark.parametrize("amount", [0, -1])
def test_create_payout_rejects_non_positive_amount(amount):
    with pytest.raises(ValueError, match="amount must be greater than zero"):
        create_payout("M001", amount, "USD")
    assert active_payouts == []


@pytest.mark.parametrize("merchant_id", [None, "", "   "])
def test_create_payout_rejects_empty_merchant_id(merchant_id):
    with pytest.raises(ValueError, match="merchant_id must not be empty"):
        create_payout(merchant_id, 100.00, "USD")
    assert active_payouts == []


def test_create_payout_rejects_unsupported_currency():
    with pytest.raises(ValueError, match="Unsupported currency: GBP"):
        create_payout("M001", 100.00, "GBP")
    assert active_payouts == []


def test_calculate_fee_usd():
    fee = calculate_fee(100.00, "USD")
    assert fee == 3.20  # 100 * 0.029 + 0.30 = 3.20


def test_calculate_fee_eur():
    fee = calculate_fee(100.00, "EUR")
    assert fee == 4.00  # 100 * 0.035 + 0.50 = 4.00


def test_calculate_fee_gbp_rejects_unsupported_currency():
    with pytest.raises(ValueError, match="Unsupported currency: GBP"):
        calculate_fee(100.00, "GBP")


def test_process_payout():
    p = create_payout("M001", 250.00, "USD")
    result = process_payout(p["id"])
    assert result["status"] == "COMPLETED"
    assert result["net_amount"] == 250.00 - result["fee"]


def test_process_duplicate_is_idempotent():
    payout = create_payout("M001", 250.00, "USD")
    first_result = process_payout(payout["id"])
    processed_at = first_result["processed_at"]
    fee = first_result["fee"]
    net_amount = first_result["net_amount"]

    second_result = process_payout(payout["id"])

    assert second_result is first_result
    assert second_result["processed_at"] == processed_at
    assert second_result["fee"] == fee
    assert second_result["net_amount"] == net_amount


def test_process_payout_rejects_non_positive_amount():
    payout = create_payout("M001", 100.00, "USD")
    payout["amount"] = -100.00

    with pytest.raises(
        ValueError,
        match="Cannot process payout: amount must be greater than zero"
    ):
        process_payout(payout["id"])

    assert payout["status"] == "PENDING"
    assert "fee" not in payout


def test_process_nonexistent_payout():
    result = process_payout("fake-id-12345")
    assert result is None


# --- API Tests ---

def test_api_create_payout(client):
    resp = client.post("/payouts", json={
        "merchant_id": "M100",
        "amount": 500.00,
        "currency": "USD"
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["amount"] == 500.00


def test_api_create_payout_rejects_unsupported_currency(client):
    resp = client.post("/payouts", json={
        "merchant_id": "M100",
        "amount": 500.00,
        "currency": "GBP"
    })
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "Unsupported currency: GBP"
    assert active_payouts == []


@pytest.mark.parametrize(("merchant_id", "amount", "error"), [
    ("M100", 0, "amount must be greater than zero"),
    ("M100", -1, "amount must be greater than zero"),
    (None, 100, "merchant_id must not be empty"),
    ("", 100, "merchant_id must not be empty"),
    ("   ", 100, "merchant_id must not be empty"),
])
def test_api_create_payout_rejects_invalid_values(
    client, merchant_id, amount, error
):
    resp = client.post("/payouts", json={
        "merchant_id": merchant_id,
        "amount": amount,
        "currency": "USD"
    })

    assert resp.status_code == 400
    assert resp.get_json()["error"] == error
    assert active_payouts == []


def test_api_get_payout(client):
    resp = client.post("/payouts", json={
        "merchant_id": "M100",
        "amount": 200.00,
        "currency": "USD"
    })
    payout_id = resp.get_json()["id"]
    resp2 = client.get(f"/payouts/{payout_id}")
    assert resp2.status_code == 200


def test_api_merchant_payouts(client):
    client.post("/payouts", json={"merchant_id": "M200", "amount": 100.00, "currency": "USD"})
    client.post("/payouts", json={"merchant_id": "M200", "amount": 200.00, "currency": "USD"})
    resp = client.get("/merchants/M200/payouts")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 2
    assert data["total_amount"] == 300.00


def test_api_missing_fields(client):
    resp = client.post("/payouts", json={"merchant_id": "M300"})
    assert resp.status_code == 400


def test_api_process_unsupported_currency_returns_400(client):
    payout = create_payout("M001", 100.00, "USD")
    payout["currency"] = "GBP"

    resp = client.post(f"/payouts/{payout['id']}/process")

    assert resp.status_code == 400
    assert resp.get_json()["error"] == (
        "Cannot process payout: Unsupported currency: GBP"
    )
    assert payout["status"] == "PENDING"
    assert "fee" not in payout
