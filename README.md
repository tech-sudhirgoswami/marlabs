# Marlabs GenAI Spring Boot Candidate Assessment

Local two-service implementation for the **Employee policy and reimbursement triage** assessment.

## What is implemented

- **Spring Boot public API**
  - `POST /answer`
  - `POST /batches`
  - validates `X-Caller-Id`
  - validates `as_of`
  - owns caller/tenant/role context
  - validates manifest/file correspondence
  - preserves manifest order
  - returns safe public responses
- **Python policy/document service**
  - UTF-8 TXT extraction
  - text-based PDF extraction
  - deterministic offline policy retrieval/model double
  - policy eligibility filtering before generation
  - ambiguity/conflict handling
  - exact-byte duplicate detection support
- **Policy safety**
  - caller tenant and role come only from the caller lookup
  - policy eligibility is based on metadata: tenant, role, approval state, effective dates
  - submitted requests are never policy
  - prompt-injection text is treated as document data
  - no automatic claim approval or payment
- **Testing**
  - policy outcomes
  - caller access
  - effective dates
  - evidence quotations
  - ambiguous amounts
  - exact duplicates
  - mixed completed/failed batch
  - provider timeout/unavailable/malformed-output behavior in Python unit tests

## Repository structure

```text
spring-api/              Spring Boot public API
python-service/          Python extraction + retrieval + deterministic generation
data/policies/           Supplied policy corpus, unchanged
data/requests/           Synthetic request files 01-08
examples/responses/      Representative JSON
scripts/                 Helper scripts
```

## Prerequisites

- Java 17+
- Maven 3.9+
- Python 3.11+
- `pip`

No paid LLM, API key, database, OCR engine, or cloud account is required.

## 1. Start Python service

```bash
cd python-service
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8001
```

## 2. Start Spring Boot

In another terminal:

```bash
cd spring-api
mvn spring-boot:run
```

Spring listens on `http://localhost:8080`.

## 3. Run automated tests

Python:

```bash
cd python-service
pytest -q
```

Spring:

```bash
cd spring-api
mvn test
```

## 4. Exercise `/answer`

```bash
curl -X POST http://localhost:8080/answer ^
  -H "Content-Type: application/json" ^
  -H "X-Caller-Id: atlas-employee-01" ^
  -d "{"question":"What is my annual certification reimbursement limit?","as_of":"2026-09-21"}"
```

Linux/macOS:

```bash
curl -X POST http://localhost:8080/answer   -H "Content-Type: application/json"   -H "X-Caller-Id: atlas-employee-01"   -d '{"question":"What is my annual certification reimbursement limit?","as_of":"2026-09-21"}'
```

Expected business result: `ANSWERED`, with the current Atlas employee certification policy (`INR 25000`) and a verbatim citation.

## 5. Exercise `/batches`

The supplied synthetic files are already under `data/requests`.

Linux/macOS:

```bash
curl -X POST http://localhost:8080/batches   -H "X-Caller-Id: atlas-employee-01"   -F 'metadata={"batch_id":"demo-01","as_of":"2026-09-21","documents":[{"document_id":"request-01","filename":"request-01.txt"},{"document_id":"request-02","filename":"request-02.pdf"},{"document_id":"request-03","filename":"request-03.txt"},{"document_id":"request-04","filename":"request-04.txt"},{"document_id":"request-05","filename":"request-05.txt"},{"document_id":"request-06","filename":"request-06.txt"},{"document_id":"request-07","filename":"request-07.txt"},{"document_id":"request-08","filename":"request-08.txt"}]}'   -F 'files=@../data/requests/request-01.txt'   -F 'files=@../data/requests/request-02.pdf'   -F 'files=@../data/requests/request-03.txt'   -F 'files=@../data/requests/request-04.txt'   -F 'files=@../data/requests/request-05.txt'   -F 'files=@../data/requests/request-06.txt'   -F 'files=@../data/requests/request-07.txt'   -F 'files=@../data/requests/request-08.txt'
```

A Windows PowerShell example is in `scripts/run-batch.ps1`.

## Response shape chosen for batch items

```json
{
  "document_id": "request-01",
  "processing_status": "COMPLETED",
  "extracted": {
    "benefit": "certification reimbursement",
    "amount": 18000,
    "currency": "INR",
    "reference": "CERT-101"
  },
  "field_evidence": {
    "benefit": {"quote": "I request certification reimbursement of INR 18000 for a completed cloud certification."},
    "amount": {"quote": "I request certification reimbursement of INR 18000 for a completed cloud certification."},
    "currency": {"quote": "I request certification reimbursement of INR 18000 for a completed cloud certification."},
    "reference": {"quote": "Reference: CERT-101"}
  },
  "policy": {
    "status": "ANSWERED",
    "answer": "The applicable annual certification reimbursement limit is INR 25000.",
    "citations": [
      {
        "chunk_id": "atlas-cert-current",
        "quote": "The annual certification reimbursement limit for employees is INR 25000."
      }
    ]
  },
  "review_required": true,
  "issues": [
    "Human review is mandatory for every submitted request.",
    "The annual policy limit does not establish remaining balance, expense eligibility, or payable amount."
  ],
  "duplicate_of": null,
  "error": null
}
```

For `request-03`, the two different stated amounts remain unresolved and are not guessed.
For `request-06`, `duplicate_of` is `request-01`.
For `request-08`, the item is `FAILED` because it is zero-byte/unreadable; other items continue.

## Error shape and codes

Errors are returned as `{"error": {"code": "<STABLE_CODE>", "message": "<safe message>"}}` with a non-2xx status. Item-level failures inside `/batches` use the same `error` field inside the result object with HTTP 200 for the batch.

| Code | HTTP | Where |
|---|---|---|
| `MISSING_CALLER`, `UNKNOWN_CALLER` | 400 | `X-Caller-Id` missing or not in the caller directory |
| `INVALID_QUESTION` | 400 | `/answer` with blank question |
| `INVALID_AS_OF` | 400 | `as_of` missing or not `YYYY-MM-DD` |
| `INVALID_METADATA` | 400 | `/batches` metadata missing/invalid |
| `DUPLICATE_MANIFEST_IDENTIFIER` | 400 | repeated `document_id` or `filename` in manifest |
| `FILE_MANIFEST_MISMATCH` | 400 | missing/extra file parts or filename mismatch |
| `INVALID_REQUEST` | 400 | generic request processing failure |
| `PYTHON_SERVICE_UNAVAILABLE` | 502 | Python dependency failure (provider timeout/unavailable) |
| `MALFORMED_MODEL_OUTPUT` | 502 | provider returned an unusable shape |
| `EMPTY_FILE` | item | zero-byte upload |
| `UNREADABLE_FILE` | item | empty/unreadable document text |
| `INVALID_UTF8` | item | non-UTF-8 TXT upload |
| `PDF_EXTRACTION_FAILED` | item | text-based PDF could not be parsed |
| `UNSUPPORTED_FILE_TYPE` | item | extension other than `.txt`/`.pdf` |
| `PROCESSING_FAILED` | item | unexpected item-level failure |

Policy findings (`status: ANSWERED|INSUFFICIENT_EVIDENCE|CONFLICT`) are never HTTP failures; non-2xx responses are reserved for request/dependency/processing failures.

## Policy decision behavior

Only policy records that are:

1. `Approved`
2. for the caller's tenant
3. for the caller's role
4. effective on `as_of` (`effective_from <= as_of < effective_to`)

are eligible.

If exactly one eligible relevant policy supports the requested benefit, the result is `ANSWERED`.
If there is no sufficient eligible evidence, the result is `INSUFFICIENT_EVIDENCE`.
If multiple simultaneously applicable eligible policies disagree, the result is `CONFLICT`.

The assessment explicitly says no precedence rule is supplied for contradictory, simultaneously applicable policies, so the implementation does **not** invent one. This is why Atlas home-office questions at the supplied date produce `CONFLICT`.

## Offline model double

`python-service/app/model.py` is a deterministic provider interface. It is deliberately not a real LLM.

- It receives only eligible policy passages.
- It never receives caller-controlled tenant/role claims.
- It can be configured to simulate `timeout`, `unavailable`, or `malformed` output for tests.
- Production integration can replace this provider without changing the public API contract.

## Configuration

Spring:
- `PYTHON_SERVICE_URL` (default `http://localhost:8001`)
- `PYTHON_TIMEOUT_MS` (default `5000`)

Python:
- `MODEL_MODE=offline|timeout|unavailable|malformed`
- `MODEL_TIMEOUT_MS` (default `1000`)

## Design note

See `DECISION_NOTE.md`.

## Production design note

See `PRODUCTION_DESIGN_NOTE.md`.

## AI assistance

This repository was generated with AI assistance. The implementation, tests, behavior, and design choices remain the candidate's responsibility and should be reviewed and understood before submission.

## Known limitation / uncovered behavior

The test suite does not attempt OCR or image-only PDF extraction because the assessment only requires text-based PDFs. It also does not simulate a real external approval system; the production note describes how that would be isolated.

## Important submission reminder

The assessment asks for a public GitHub repository and final commit SHA. Do not commit real employee data, credentials, or API keys.
