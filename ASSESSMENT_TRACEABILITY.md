# Assessment Traceability

| Assessment requirement | Implementation |
|---|---|
| Spring Boot public API | `spring-api` |
| Python extraction/retrieval/generation | `python-service` |
| `/answer` | `ApiController` -> `AssessmentService` -> `PythonClient` |
| `/batches` | `ApiController` -> manifest validation -> per-item processing |
| caller validation | `CallerDirectory` |
| tenant/role from caller lookup | `CallerDirectory`, never from document |
| effective date rule | `PolicyStore.eligible()` |
| Approved-only policy evidence | `PolicyStore.eligible()` |
| conflict without invented precedence | `PolicyStore.answer()` |
| submitted text not a policy source | Python only loads `data/policies/policies.json` as policy corpus |
| prompt injection handling | eligibility boundary + no caller-context changes from document |
| UTF-8 TXT | `extract_text()` |
| text PDF | `pypdf` |
| missing/ambiguous fields visible | `extract_fields()` + batch issues |
| exact duplicates | SHA-256 of uploaded bytes |
| zero-byte item failure | extractor `EMPTY_FILE` |
| one item failure does not stop batch | per-item try/catch |
| model double | `OfflineModelDouble` |
| timeout/unavailable/malformed doubles | `MODEL_MODE` and tests |
| no automatic retries | one client call per stage, bounded public client behavior |
| traceability | batch ID + document ID in response; safe errors |
| sample requests/responses | `scripts/`, `examples/responses/` |
| production note | `PRODUCTION_DESIGN_NOTE.md` |
