# PayStream Payout API

A small Flask API and in-memory model for creating, viewing, and processing
merchant payouts. Payout data is held in process memory and is lost when the
application stops; this project is a development/demo service, not a
production-ready payment system.

## Requirements

- Python 3
- Flask
- pytest (for running the tests)

Install the dependencies:

```bash
python -m pip install Flask pytest
```

## Run the service

```bash
python payout_api.py
```

The development server listens on `http://127.0.0.1:5000`. The app currently
starts Flask with debug mode enabled; do not expose this development server to
the public internet.

## API

All request and response bodies use JSON.

### Create a payout

`POST /payouts`

Required request fields:

```json
{
  "merchant_id": "M100",
  "amount": 500.00,
  "currency": "USD"
}
```

Optional field: `memo`.

- `201 Created` with the created payout for valid input.
- `400 Bad Request` with an `error` message if a required field is missing,
  the merchant ID is empty, the amount is not positive, or the currency is
  unsupported.

Supported currencies are USD and EUR. Amounts must be greater than zero.

### Get a payout

`GET /payouts/<payout_id>`

- `200 OK` with the payout if found.
- `404 Not Found` if the payout does not exist.

### Process a payout

`POST /payouts/<payout_id>/process`

- `200 OK` with the completed payout. Reprocessing an already completed payout
  returns its existing result.
- `400 Bad Request` with an `error` message if the payout cannot be processed,
  including an invalid amount or unsupported currency.
- `404 Not Found` if the payout does not exist.

Fee schedule:

- USD: 2.9% of the amount plus 0.30.
- EUR: 3.5% of the amount plus 0.50.

### List a merchant's payouts

`GET /merchants/<merchant_id>/payouts`

Returns the merchant ID, payout list, total amount, and payout count. An
unknown merchant currently receives `200 OK` with an empty list and total of
zero.

## Run tests

From the project directory:

```bash
python -m pytest -v
```

## Project files

- `payout_api.py` — Flask routes and HTTP responses.
- `payout_models.py` — payout creation, lookup, fee calculation, and processing.
- `test_payouts.py` — model and API regression tests.
- `incident_log.txt` — production incident notes and triage.
- `incident_triage_analysis.txt` — incident/code cross-reference.
- `PROJECT_TRACKER.txt` — bugs, fixes, and follow-up status.
