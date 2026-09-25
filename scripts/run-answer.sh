#!/usr/bin/env bash
set -euo pipefail
curl -X POST http://localhost:8080/answer \
  -H "Content-Type: application/json" \
  -H "X-Caller-Id: atlas-employee-01" \
  -d '{"question":"What is my annual certification reimbursement limit?","as_of":"2026-09-21"}'
