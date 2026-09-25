# Production Design Note (<=400 words)

For 10,000 requests/day containing personal information, I would keep the public Spring Boot API as the policy/security boundary and deploy it as a containerized service behind an API gateway/WAF. The Python extraction/retrieval service would run separately with bounded resource limits. A managed queue could be introduced for larger or asynchronous batches, while preserving the synchronous contract for the assessment-sized workload.

The first security change would be real authentication and authorization rather than the exercise's `X-Caller-Id` simulation. Tenant and role would come from trusted identity claims or an authorization service. I would encrypt data in transit and at rest, minimize document retention, redact sensitive values from logs, use least-privilege service identities, rotate secrets, and define an explicit audit trail for policy decisions. Submitted documents would remain data, never instructions.

The most important operational risks are slow or unavailable approval dependencies, model/provider latency, extraction failures, policy-version mistakes, and accidental cross-tenant retrieval. I would add request IDs, batch/document trace IDs, metrics for extraction/model/retrieval latency, dependency timeouts, circuit breakers, bounded concurrency, and alerts. Policy records should be versioned and immutable enough to reconstruct which evidence was used for a historical answer.

For the partially documented approval system, I would put an adapter behind a strict interface rather than coupling the application directly to its API. The adapter should return explicit states such as approved, pending, rejected, unavailable, and unknown; “unknown” must not be converted into approval.

Before committing to a delivery date, I would clarify the authoritative policy source, policy precedence/versioning rules, identity/tenant model, retention and deletion requirements, expected document formats and sizes, approval-system SLA/rate limits, privacy/compliance requirements, acceptable model providers, expected latency, and whether the final workflow is allowed to recommend payment amounts or only produce review findings.
