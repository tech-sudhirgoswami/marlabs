# Decision Note

## Consequential design choice

I kept **policy eligibility deterministic and metadata-driven before generation**. The policy store filters by caller tenant, caller role, approval state, and effective date first. Only those eligible records can reach the deterministic model double. This makes the security boundary explicit and prevents a matching keyword, request document, draft policy, or prompt-injection passage from becoming evidence.

## Alternative rejected

I rejected a pure semantic/vector search implementation for the assessment baseline. A vector index can help recall, but it does not by itself enforce tenant/role/date/approval constraints. For this small supplied corpus, deterministic filtering followed by simple benefit matching is easier to test and explain. A production system could add embeddings/reranking **after** hard eligibility filtering.

## Main limitation

The implementation uses a deterministic offline model double and lightweight extraction rather than a real LLM/OCR stack. This is intentional because the assessment requires an offline path and does not require OCR. The PDF parser handles text-based PDFs only.

## Time / unfinished work

Approximate implementation time: 3–4 hours including service wiring, test coverage, sample data, and documentation.

Unfinished production work: real model/provider integration, authentication, persistent storage, distributed tracing, OCR, durable audit storage, and integration with a real approval system.

## AI assistance

AI assistance was used to generate and structure the initial implementation, tests, and documentation. The code should be reviewed manually and explained by the candidate during the technical follow-up.
