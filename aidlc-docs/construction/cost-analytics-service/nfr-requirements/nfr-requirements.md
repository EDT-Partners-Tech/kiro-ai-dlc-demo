# NFR Requirements - Cost Analytics Service

**Unit**: Cost Analytics Service  
**Phase**: NFR Requirements  
**Date**: 2026-06-19

---

## Overview

This document specifies the non-functional requirements for the Cost Analytics Service, including performance, availability, security, scalability, and operational requirements.

---

## Section 1: Performance Requirements

### NFR-PERF-1: Response Time SLA
- **Requirement**: 90th percentile response time must be ≤ 500ms
- **Scope**: Typical queries (GET /cost-data/daily, GET /cost-data/anomalies)
- **Baseline**: SQLite on single server, demo scale (~10-20 concurrent users)
- **Rationale**: Standard FinOps dashboard expectations; <500ms feels responsive to users
- **Testing**: Include performance smoke test (verify 10K costs loaded, queries < 500ms)

### NFR-PERF-2: Query Optimization
- **Requirement**: Aggregation queries (daily trends, anomalies) must use database-level grouping (not in-memory)
- **Indexes**: Create indexes on timestamp, service, status fields
- **N+1 Prevention**: Use single queries with JOINs (no lazy loading)
- **Rationale**: Prevents performance degradation as data grows; aligns with SQLite optimization patterns

### NFR-PERF-3: Concurrent Request Handling
- **Requirement**: Support 10-20 concurrent API users (demo scale)
- **Concurrency Model**: SQLite with WAL (write-ahead logging) mode
- **Implication**: Multiple readers + 1 writer safely handled by SQLite
- **Limitation**: Not suitable for >100 concurrent users (upgrade to RDS then)

---

## Section 2: Availability & Reliability Requirements

### NFR-AVAIL-1: Uptime SLA
- **Requirement**: Best effort (no formal SLA for demo)
- **Rationale**: Single instance, no failover; acceptable for teaching purposes
- **Operational**: Manual restart required if process crashes
- **Note**: Production upgrade path includes RDS replication (99.95% SLA)

### NFR-AVAIL-2: Data Backups
- **Requirement**: Manual backups only (no automated backup infrastructure)
- **Process**: Users can manually copy `cloudspend.db` for backup
- **Example**: `cp cloudspend.db cloudspend.db.bak` before major operations
- **Rationale**: Keeps deployment simple for demo; automated backups are future enhancement

### NFR-AVAIL-3: Database Consistency
- **Requirement**: Strict ACID semantics enforced by SQLite
- **Guarantee**: All writes are durable; no partial updates
- **Concurrency**: SQLite handles concurrent reads + writes safely (via WAL)
- **Implication**: Financial data is always consistent (no eventual consistency issues)

### NFR-AVAIL-4: Error Handling & Resilience
- **Requirement**: API returns clear error messages (no stack traces)
- **Recovery**: Failed requests return proper HTTP status codes
- **Logging**: Errors logged with context; developers can debug via logs
- **Rationale**: User-friendly and secure (no internal details exposed)

---

## Section 3: Security Requirements

### NFR-SEC-1: Authentication
- **Requirement**: No authentication for demo (all endpoints public)
- **Rationale**: Keeps demo simple; focus on FinOps logic, not auth
- **Production Path**: Add API key or OAuth2 authentication via decorator pattern
- **Security Note**: For real financial data, authentication is mandatory (documented in upgrade path)

### NFR-SEC-2: Authorization
- **Requirement**: No role-based access control (all authenticated users have full access)
- **Implication**: All users can read/write all cost data
- **Rationale**: Demo scope; multi-tenant authorization is future enhancement

### NFR-SEC-3: Input Validation
- **Requirement**: All user input validated server-side (no client-side validation trust)
- **Validation Rules**: Per business-rules.md (service name format, amount range, timestamp constraints)
- **SQL Injection Prevention**: Use parameterized queries (SQLModel + SQLAlchemy enforce this)
- **Enforcement**: Security Baseline extension validates all rules

### NFR-SEC-4: Error Message Safety
- **Requirement**: Error responses never expose internal details (database structure, stack traces, file paths)
- **Example**: Return "Invalid timestamp format" (safe), NOT "SQLAlchemy ValueError: DateTimeField parsing failed" (unsafe)
- **Implementation**: Use try-catch with custom error messages in FastAPI exception handlers
- **Enforcement**: Security Baseline extension validates error responses

### NFR-SEC-5: Data Encryption
- **At Rest**: No encryption for demo (SQLite file stored unencrypted)
- **In Transit**: Use HTTPS in production (uvicorn can be behind nginx/load balancer with TLS)
- **Rationale**: Demo runs on localhost/trusted network; production must use HTTPS
- **Note**: Document encryption requirements for production deployment

### NFR-SEC-6: Secrets Management
- **Configuration**: Use environment variables for config (DATABASE_URL, LOG_LEVEL)
- **No Hardcoded Secrets**: Never commit credentials, API keys, or database URLs in code
- **Production**: Use AWS Secrets Manager or similar for production secrets
- **Logging**: Ensure logs never contain sensitive data (validate during testing)

### NFR-SEC-7: Rate Limiting
- **Requirement**: No rate limiting for demo (trusted environment)
- **Production**: Implement via API Gateway or reverse proxy (not in API code)
- **Rationale**: Keeps demo simple; production can add as external layer

---

## Section 4: Scalability Requirements

### NFR-SCALE-1: Expected Data Volume
- **Daily Volume**: 100-1K cost entries per day (demo scale)
- **Projected Growth**: Assume ~1 year of data in demo (36.5K-365K entries)
- **SQLite Capacity**: Handles this volume with ease; migrations to RDS only needed for > 10M records
- **Storage**: Demo database expected to be <10MB (very small)

### NFR-SCALE-2: Concurrent Users
- **Expected**: 10-20 concurrent users (demo/small team)
- **SQLite Limit**: Single file supports this; becomes problematic at >100 users
- **Upgrade Path**: Migrate to RDS (PostgreSQL/MySQL) for horizontal scaling

### NFR-SCALE-3: Request Rate
- **Expected**: ~5-10 requests/sec peak (demo)
- **SQLite Throughput**: Handles easily; becomes constraint at >100 req/sec
- **Upgrade**: RDS + read replicas for higher throughput

### NFR-SCALE-4: Vertical vs. Horizontal Scaling
- **Demo Strategy**: Vertical scaling (larger single server)
- **Production Strategy**: Horizontal scaling (multiple API instances + RDS)
- **Technology Choice**: SQLite prevents horizontal API scaling (single file bottleneck); RDS enables it

---

## Section 5: Data Integrity & Consistency Requirements

### NFR-CONS-1: ACID Semantics
- **Guarantee**: Atomicity, Consistency, Isolation, Durability enforced
- **Implication**: No partial updates; all transactions succeed or fail completely
- **Financial Impact**: Critical for cost data accuracy (every transaction is auditable)

### NFR-CONS-2: Data Retention
- **Requirement**: Retain all cost data forever (no deletion by age)
- **Rationale**: FinOps compliance and historical trend analysis
- **Operational**: Manual cleanup only (not automatic)

### NFR-CONS-3: Immutability of Historical Data
- **Requirement**: Cost entries are immutable once created (delete-only, no updates)
- **Exception**: Recommendation status can be updated (one-way transitions)
- **Audit Trail**: All modifications tracked via timestamps (updated_at)
- **Compliance**: Supports financial audit requirements

### NFR-CONS-4: Decimal Precision
- **Requirement**: All monetary amounts use Decimal type (not float)
- **Precision**: Exactly 2 decimal places (cents)
- **Rounding**: ROUND_HALF_UP semantics
- **Rationale**: Prevents floating-point rounding errors in financial calculations

---

## Section 6: Testing & Quality Requirements

### NFR-TEST-1: Code Coverage
- **Target**: >85% line coverage
- **Scope**: Core business logic (ingestion, trends, anomalies, recommendations)
- **Measurement**: Use pytest-cov; report coverage for each module
- **Enforcement**: CI/CD fails if coverage drops below 85%

### NFR-TEST-2: Example-Based Testing
- **Requirement**: Comprehensive example-based tests (test_api.py)
- **Scenarios**: 
  - Happy path (valid inputs)
  - Error cases (invalid inputs, 400/404/500)
  - Edge cases (empty results, pagination boundaries)
  - Security (input validation, error message safety)
- **Framework**: pytest
- **Minimum**: 30+ test cases

### NFR-TEST-3: Property-Based Testing (Mandatory Extension)
- **Requirement**: Property-based tests verify invariants across random inputs
- **Properties to Test**:
  - Round-trip serialization (cost data → JSON → cost data)
  - Pagination invariants (cursor ordering, no duplicates across pages)
  - Anomaly detection correctness (baseline calculation, spike detection)
  - Cost aggregation (no rounding loss, commutativity of sums)
- **Framework**: Hypothesis (Python)
- **Minimum**: 10+ property tests
- **Rationale**: Catches edge cases example-based tests miss; critical for financial accuracy

### NFR-TEST-4: Performance Testing
- **Requirement**: Smoke test (not formal load testing)
- **Test Scenario**: Ingest 10K costs, verify queries complete in <500ms
- **Tool**: Simple Python script (no load testing framework)
- **Pass Criteria**: Daily trend query and anomaly detection both < 500ms
- **Rationale**: Verifies performance targets are met at demo scale

### NFR-TEST-5: Security Testing
- **Input Validation**: Test boundary conditions (negative amounts, future timestamps, invalid service names)
- **SQL Injection**: Verify parameterized queries prevent injection
- **Error Messages**: Ensure error responses contain no internal details
- **Framework**: pytest + property-based generators for fuzzing
- **Enforcement**: Security Baseline extension validates all rules

---

## Section 7: Operational Requirements

### NFR-OPS-1: Logging
- **Level**: INFO (production), DEBUG (development)
- **Format**: JSON structured logs (CloudWatch-compatible)
- **Content**: timestamp, request_id, method, path, status, latency, error (if any)
- **Security**: No sensitive data in logs (no passwords, API keys, or raw cost amounts in non-aggregated form)
- **Retention**: Demo stores logs to stdout; production can configure log aggregation

### NFR-OPS-2: Monitoring & Observability
- **Metrics**: Log latency per endpoint, error rates, request counts
- **Alerting**: None required for demo (manual monitoring acceptable)
- **Production**: Integrate with CloudWatch or similar; set up alerts for error spikes
- **Dashboard**: Optional (developers can query logs manually)

### NFR-OPS-3: Configuration Management
- **Environment Variables**:
  - `DATABASE_URL`: SQLite connection string (default: `sqlite:///./cloudspend.db`)
  - `LOG_LEVEL`: INFO or DEBUG (default: INFO)
  - `ENVIRONMENT`: development or production (affects logging verbosity)
- **Secrets**: None required for demo (no AWS credentials, no API keys)
- **Future**: Use AWS Secrets Manager for production secrets

### NFR-OPS-4: Deployment & Packaging
- **Local Development**: `.venv/bin/python -m uvicorn main:app --reload`
- **Production Deployment**: Single Python process or Docker container
- **Docker**: Optional Dockerfile provided; not required to run locally
- **CI/CD**: GitHub Actions optional (simple lint + test pipeline suggested)
- **Deployment Target**: Local dev or single EC2 instance (no orchestration needed for demo)

### NFR-OPS-5: Code Quality
- **Linting**: Use `black` (code formatter) and `flake8` (linter)
- **Type Checking**: `mypy` for optional type annotations
- **Dependency Management**: `pip` + `requirements.txt` (pinned versions)
- **Documentation**: Docstrings for all functions; README for setup/architecture

### NFR-OPS-6: Disaster Recovery
- **RTO (Recovery Time Objective)**: ~5 minutes (manual backup restore)
- **RPO (Recovery Point Objective)**: Data loss since last manual backup
- **Procedure**: Restore from backup file, restart API process
- **Production**: Automated backups via RDS or S3 snapshots

---

## Summary

**NFR Philosophy**: Simple and clear for demo purposes, with documented upgrade paths for production

- **Scalability**: Demo scale (demo-scale users + data volume); RDS migration for production
- **Performance**: <500ms response times (SQLite on local hardware)
- **Availability**: Best effort (single instance); HA available via RDS
- **Security**: Input validation + error message safety (Security Baseline extension)
- **Testing**: >85% coverage + mandatory property-based testing
- **Operations**: Environment variables + JSON logging + optional Docker
