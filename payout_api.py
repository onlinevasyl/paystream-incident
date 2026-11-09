from flask import Flask, request, jsonify
from payout_models import (
    create_payout, get_payout, get_merchant_payouts,
    process_payout, active_payouts
)

app = Flask(__name__)


@app.route("/payouts", methods=["POST"])
def create():
    data = request.get_json()
    try:
        payout = create_payout(
            data["merchant_id"],
            data["amount"],
            data["currency"],
            data.get("memo")
        )
    except KeyError as error:
        return jsonify({"error": f"Missing required field: {error.args[0]}"}), 400
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    return jsonify(payout), 201


@app.route("/payouts/<payout_id>", methods=["GET"])
def get(payout_id):
    p = get_payout(payout_id)
    if p is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(p), 200


@app.route("/payouts/<payout_id>/process", methods=["POST"])
def process(payout_id):
    try:
        result = process_payout(payout_id)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    if result is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(result), 200


@app.route("/merchants/<merchant_id>/payouts", methods=["GET"])
def merchant_payouts(merchant_id):
    payouts = get_merchant_payouts(merchant_id)
    total = sum(p["amount"] for p in payouts)
    return jsonify({
        "merchant_id": merchant_id,
        "payouts": payouts,
        "total_amount": total,
        "count": len(payouts)
    }), 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)
