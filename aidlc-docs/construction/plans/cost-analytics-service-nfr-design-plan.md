# NFR Design Plan - Cost Analytics Service

**Unit**: Cost Analytics Service  
**Phase**: NFR Design (CONSTRUCTION)  
**Date**: 2026-06-19  
**Status**: Planning

---

## Plan Overview

This plan outlines the NFR Design for the Cost Analytics Service, focusing on design patterns, logical components, and architecture decisions to meet non-functional requirements.

---

## Steps to Execute

### Step 1: Security Patterns
- [ ] Design input validation pattern (middleware vs. endpoint level)
- [ ] Design error handling pattern (exception mapping, response format)
- [ ] Design logging pattern (what to log, what to redact)
- [ ] Design security headers approach

**Questions for Step 1**:

**Q1.1**: Where should input validation happen?
- A) FastAPI middleware (global, all endpoints)
- B) Endpoint-level (using Pydantic models)
- C) Both (middleware for structural, Pydantic for business rules) 
[Answer]: **C) Both. Pydantic models for structural validation (type, required fields), middleware for business rules (positive amounts, future date checks).** This showcases layered validation: framework handles types, custom middleware handles business logic.

**Q1.2**: How should errors be logged?
- A) Log all errors with full context (params, state)
- B) Log errors but redact sensitive data (amounts, service names)
- C) Log only error type and message (minimal logging) 
[Answer]: **B) Log errors with redaction.** Include context (endpoint, status code) but not full cost amounts or internal database details. Security Baseline requirement.

**Q1.3**: Should API responses include error codes (e.g., "ERR_INVALID_AMOUNT")?
- A) Yes (helps clients parse errors programmatically)
- B) No (only HTTP status + human message) 
[Answer]: **B) No error codes.** HTTP status + human message only (Security Baseline: don't expose internal error codes). Clients use HTTP status codes for logic.

**Q1.4**: Which security headers should be enforced?
- A) Minimal (Content-Type only)
- B) Standard (Content-Type, X-Frame-Options, X-Content-Type-Options)
- C) Comprehensive (add CSP, STS, etc.) 
[Answer]: **B) Standard headers.** X-Frame-Options: DENY, X-Content-Type-Options: nosniff, Content-Type: application/json. Sufficient for demo; CSP is overkill (no HTML responses). 

---

### Step 2: Performance Patterns
- [ ] Design query optimization strategy (caching, indexing)
- [ ] Design aggregation pattern (database-level vs. application-level)
- [ ] Design pagination cursor mechanism
- [ ] Design response serialization (minimize payload size)

**Questions for Step 2**:

**Q2.1**: Should we cache frequently-accessed data?
- A) No caching (SQLite is fast enough for demo)
- B) In-memory cache (Python dict or cachetools)
- C) Redis (external cache) 
[Answer]: **A) No caching for demo.** SQLite + demo scale = fast enough. Caching adds complexity and eviction logic. Add caching (via cachetools) only if profiling shows bottleneck. Future enhancement: Redis for production scale.

**Q2.2**: For daily aggregations, should we pre-compute and store, or compute on-demand?
- A) On-demand (materialized view query, no pre-computation)
- B) Pre-compute at midnight daily (background job)
- C) Hybrid (cache for 1 hour, then recompute) 
[Answer]: **A) On-demand.** Keeps implementation simple (no background jobs). Database indexes on timestamp + service make queries fast. Materialized views (pre-computed tables) are future optimization if queries slow down.

**Q2.3**: How should pagination cursors work?
- A) Opaque base64-encoded (client can't inspect)
- B) Transparent JSON (client can see structure)
- C) Simple offset-based (not date-based) 
[Answer]: **A) Opaque base64-encoded.** Chosen in functional design. Encode the next start date, decode to find offset. Clients don't depend on format; we can change algorithm later.

**Q2.4**: Should responses include nested data (e.g., recommendation details in list), or IDs only?
- A) Full nested data (rich responses)
- B) IDs only, clients fetch details separately (lean responses)
- C) Configurable via query param 
[Answer]: **A) Full nested data for demo.** Keep it simple (single query returns full recommendation objects). Production could add sparse fieldsets if response size becomes issue. For now, clarity over optimization. 

---

### Step 3: Resilience Patterns
- [ ] Design retry strategy (for failed queries, API calls)
- [ ] Design timeout handling
- [ ] Design circuit breaker pattern (if any external APIs used)
- [ ] Design graceful degradation (what happens on partial failure)

**Questions for Step 3**:

**Q3.1**: If a database query fails, should we:
- A) Retry immediately (up to 3 times)
- B) Fail immediately (return 500)
- C) Implement exponential backoff retry 
[Answer]: **B) Fail immediately for demo.** SQLite is on same host; if it fails, retries won't help. Production (with RDS): implement exponential backoff (1s, 2s, 4s). Simple + clear for demo.

**Q3.2**: What timeout should apply to queries?
- A) No timeout (let queries run as long as needed)
- B) 5-second timeout (fail if query takes too long)
- C) 30-second timeout (generous for anomaly detection) 
[Answer]: **C) 30-second timeout.** Anomaly detection queries (especially with bootstrap data) need time. 5s is too aggressive. 30s is generous for demo scale. Production: adjust based on profiling.

**Q3.3**: For anomaly detection (complex query), if it times out, should we:
- A) Return error (no partial results)
- B) Return cached results from yesterday (graceful degradation)
- C) Return limited results (e.g., last 30 days instead of full range) 
[Answer]: **A) Return error.** Keep it simple. Timeouts are exceptional (shouldn't happen at demo scale). Graceful degradation adds complexity. If this becomes an issue in production, we add caching then.

**Q3.4**: Should the API be circuit-breaker-protected? (Cut off traffic if too many errors)
- A) No (not needed for single instance)
- B) Yes (protect against cascade failures) 
[Answer]: **A) No circuit breaker for demo.** Single instance, no cascading failures possible. If we had multiple services talking to each other, circuit breaker would be essential. Future: add if needed. 

---

### Step 4: Scalability Patterns
- [ ] Design horizontal scaling pattern (if needed)
- [ ] Design state management (shared vs. local)
- [ ] Design connection pooling strategy
- [ ] Design data consistency under concurrent load

**Questions for Step 4**:

**Q4.1**: If we scale to multiple API instances (future), how should we handle state?
- A) Stateless (each instance can serve any request)
- B) Sticky sessions (each client connects to same instance)
- C) No scaling considered yet 
[Answer]: **A) Stateless design.** Even though we're not scaling now, design APIs to be stateless (no in-memory state). This enables horizontal scaling later without code changes. Best practice: keep now, scales for free later.

**Q4.2**: Should database connection pooling be used?
- A) No (simple one connection per request)
- B) Yes (connection pool with min/max limits)
- C) Future enhancement (start without) 
[Answer]: **B) Yes, use connection pooling.** SQLModel/SQLAlchemy supports it natively. Connection pool (min=5, max=20) is simple and best practice. No performance overhead; reduces connection creation cost. Demo scale won't need this, but production does.

**Q4.3**: If multiple API instances write to the same SQLite database, should we:
- A) Accept potential conflicts (SQLite handles via WAL)
- B) Implement write coordination (one instance writes)
- C) Not consider (scaling out only after RDS migration) 
[Answer]: **C) Not consider yet.** SQLite can handle multiple writers via WAL mode, but it's not recommended for horizontally scaled systems. Cross that bridge after RDS migration. For demo: single instance, no coordination needed.

**Q4.4**: Should we design for database read replicas (future)?
- A) No (single database only)
- B) Yes (design with read/write split in mind)
- C) Future consideration 
[Answer]: **B) Yes (minimal effort). Use SQLAlchemy sessions/engines that can be configured for read replicas later.** Even if we don't implement replicas now, design APIs to route read queries separately (future: replicas, current: same connection). Zero cost now, valuable later. 

---

### Step 5: Observability & Monitoring Patterns
- [ ] Design metrics collection (what to measure)
- [ ] Design structured logging (fields, format)
- [ ] Design trace/request ID propagation
- [ ] Design health check endpoint design

**Questions for Step 5**:

**Q5.1**: What metrics should the API emit?
- A) Basic (request count, latency, errors)
- B) Detailed (per-endpoint, per-service-name, per-operation)
- C) Comprehensive (include cache hits, DB pool stats) 
[Answer]: **A) Basic metrics.** Track total request count, latency histogram (p50, p90, p99), error count. Detailed per-endpoint breakdowns are future enhancement (add if performance analysis needed). Simple metrics: 3 to 5 number, easy to reason about.

**Q5.2**: Should each request have a unique request ID for tracing?
- A) No (not needed for demo)
- B) Yes (generate UUID per request, include in logs)
- C) Optional (log correlation ID if provided by client) 
[Answer]: **B) Yes, use request IDs.** Generate UUID per request; include in all logs for correlation. Simple to implement (middleware), invaluable for debugging. Best practice: cost is negligible.

**Q5.3**: For the health check endpoint, what should it verify?
- A) Just return 200 OK (simple liveness)
- B) Verify database connectivity (readiness check)
- C) Both liveness and readiness 
[Answer]: **C) Both.** GET /health → quick 200 OK (liveness). GET /health/ready → verify database connection (readiness). Common Kubernetes pattern; good practice even for demo (enables smart load balancing later).

**Q5.4**: Should we expose Prometheus metrics endpoint (for scraping)?
- A) No (not needed for demo)
- B) Yes (provide /metrics for Prometheus integration)
- C) Future enhancement 
[Answer]: **C) Future enhancement.** Not needed for demo. If deployed to Kubernetes (future), add Prometheus exporter via library. For now: emit metrics via structured logs only. 

---

### Step 6: Reliability & Data Integrity Patterns
- [ ] Design transaction boundaries (ACID guarantees)
- [ ] Design data validation strategy (when to validate)
- [ ] Design consistency checking (detect data anomalies)
- [ ] Design audit/compliance logging

**Questions for Step 6**:

**Q6.1**: Should cost ingestion be wrapped in a database transaction?
- A) Yes (atomic: validate + insert all at once)
- B) No (simpler, but risky if validation passes and insert fails)
- C) Depends on data (simple costs: no transaction, complex: transaction) 
[Answer]: **A) Yes, wrap in transaction.** SQLAlchemy handles this automatically (POST endpoint = one transaction). Even at demo scale, ACID guarantees for financial data are non-negotiable. Simple to implement, essential for compliance.

**Q6.2**: For anomaly detection, if baseline calculation fails (e.g., insufficient data), should we:
- A) Return error (fail the request)
- B) Return empty results (no anomalies detected)
- C) Return partial results (anomalies without confidence scores) 
[Answer]: **B) Return empty results.** If <7 days of data (bootstrap mode), no anomalies to report. Returning error confuses users ("why is the endpoint broken?"). Empty results are semantically clear: "no anomalies found (insufficient history)".

**Q6.3**: Should we periodically check data integrity (e.g., detect orphaned tags)?
- A) No (trust data model, no checks)
- B) Yes (daily integrity check job)
- C) On-demand (check only if user requests) 
[Answer]: **A) No integrity check for demo.** Foreign key constraints enforce data integrity at database level. SQLModel validates on write. Manual checks are future operation if we detect corruption (unlikely with ACID guarantees).

**Q6.4**: Should we keep an immutable audit log of all changes?
- A) No (rely on database transaction logs)
- B) Yes (custom audit table tracking all updates)
- C) Partial (audit only status changes, not all changes) 
[Answer]: **C) Partial audit log.** Track recommendation status changes (who→what→when) in an audit table. Cost entries are immutable (no updates needed). Balances compliance + simplicity: audit important decisions, trust database for durability. 

---

## Checkboxes Summary

**Questions Requiring User Input**: 23 questions (all answered)
**All marked with [Answer]: ✅ ANSWERED**

---

## Plan Execution Complete

✅ **All NFR design areas addressed:**
1. ✅ Security Patterns (4 decisions: layered validation, error redaction, no error codes, standard security headers)
2. ✅ Performance Patterns (4 decisions: no caching, on-demand aggregation, opaque cursors, full nested data)
3. ✅ Resilience Patterns (4 decisions: fail fast, 30s timeout, error responses, no circuit breaker)
4. ✅ Scalability Patterns (4 decisions: stateless design, connection pooling, no write coordination, read replica ready)
5. ✅ Observability Patterns (4 decisions: basic metrics, request IDs, liveness+readiness checks, Prometheus future)
6. ✅ Reliability Patterns (3 decisions: transactional writes, empty results on bootstrap, partial audit log)
