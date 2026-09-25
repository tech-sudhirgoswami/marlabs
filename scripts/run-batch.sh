#!/usr/bin/env bash
set -euo pipefail
curl -X POST http://localhost:8080/batches \
  -H "X-Caller-Id: atlas-employee-01" \
  -F 'metadata={"batch_id":"demo-01","as_of":"2026-09-21","documents":[{"document_id":"request-01","filename":"request-01.txt"},{"document_id":"request-02","filename":"request-02.pdf"},{"document_id":"request-03","filename":"request-03.txt"},{"document_id":"request-04","filename":"request-04.txt"},{"document_id":"request-05","filename":"request-05.txt"},{"document_id":"request-06","filename":"request-06.txt"},{"document_id":"request-07","filename":"request-07.txt"},{"document_id":"request-08","filename":"request-08.txt"}]}' \
  -F 'files=@data/requests/request-01.txt' \
  -F 'files=@data/requests/request-02.pdf' \
  -F 'files=@data/requests/request-03.txt' \
  -F 'files=@data/requests/request-04.txt' \
  -F 'files=@data/requests/request-05.txt' \
  -F 'files=@data/requests/request-06.txt' \
  -F 'files=@data/requests/request-07.txt' \
  -F 'files=@data/requests/request-08.txt'
