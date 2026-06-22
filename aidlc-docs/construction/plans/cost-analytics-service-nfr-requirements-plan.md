# NFR Requirements Plan - Cost Analytics Service

**Unit**: Cost Analytics Service  
**Phase**: NFR Requirements (CONSTRUCTION)  
**Date**: 2026-06-19  
**Status**: Planning

---

## Plan Overview

This plan outlines the non-functional requirements assessment for the Cost Analytics Service, focusing on scalability, performance, security, tech stack decisions, and operational requirements.

---

## Steps to Execute

### Step 1: Scalability & Performance Requirements
- [ ] Define expected concurrent users/API calls
- [ ] Define expected data volume (costs per day/month)
- [ ] Define performance targets (response time SLAs)
- [ ] Define scaling strategy (vertical, horizontal)

**Questions for Step 1**:

**Q1.1**: How many concurrent API users/requests should the system handle? (e.g., 10 users, 100/sec) 
[Answer]: **Demo scale: ~10-20 concurrent users, ~5-10 requests/sec.** This is a teaching demo, not production. SQLite handles this easily.

**Q1.2**: What is the expected daily cost entry volume? (e.g., 1K entries/day, 1M entries/day) 
[Answer]: **~100-1K entries/day.** Typical FinOps team ingests costs once daily or per billing hour. Demo data will be modest (seed with ~1 year of sample data).

**Q1.3**: What response time target? (e.g., <100ms, <500ms, <1s for typical queries) 
[Answer]: **<500ms for 90th percentile.** Standard FinOps dashboard expectations. SQLite queries easily meet this for demo scale.

**Q1.4**: Should the system scale horizontally (multiple servers) or is vertical scaling (larger single server) sufficient? 
[Answer]: **Vertical scaling sufficient for demo.** Single SQLite instance. Horizontal scaling is an upgrade path (note in future work: migrate to RDS for multi-instance). 

---

### Step 2: Availability & Reliability Requirements
- [ ] Define uptime expectations (SLA %)
- [ ] Define data backup/recovery strategy
- [ ] Define failover/disaster recovery needs
- [ ] Define monitoring and alerting requirements

**Questions for Step 2**:

**Q2.1**: What is the required uptime SLA? (e.g., 99%, 99.9%, or just "best effort" for demo) 
[Answer]: **Best effort (demo scope).** No formal SLA. Single instance is acceptable for teaching purposes.

**Q2.2**: How often should backups be performed? (e.g., hourly, daily, or just at deployment) 
[Answer]: **Manual backups only (no automation for demo).** User can `cp cloudspend.db cloudspend.db.bak` if needed. Add automated backups as future enhancement.

**Q2.3**: Is high availability (replicated database) required, or is single-instance acceptable for demo? 
[Answer]: **Single-instance acceptable.** High availability is out of scope for demo. Note: migration to RDS enables replication if needed.

**Q2.4**: Should the API emit metrics/logs for monitoring? (e.g., via CloudWatch, DataDog, or just stdout) 
[Answer]: **Structured JSON logs to stdout.** Tools like CloudWatch can ingest from stdout. No fancy monitoring infrastructure needed for demo. 

---

### Step 3: Security Requirements
- [ ] Define authentication/authorization model
- [ ] Define data encryption requirements (in transit, at rest)
- [ ] Define compliance requirements (SOC2, HIPAA, PCI-DSS, or none)
- [ ] Define security headers and input sanitization

**Questions for Step 3**:

**Q3.1**: Should the API require authentication? (e.g., API keys, OAuth, or public/unauthenticated) 
[Answer]: **Public/unauthenticated for demo.** No auth system in scope. All endpoints are public. Note: Add API key authentication in v2 if needed (Security Baseline extension covers this pattern).

**Q3.2**: Should cost data be encrypted at rest in the database? 
[Answer]: **No encryption at rest for demo.** SQLite file is unencrypted. For production: enable SQLite encryption extensions or migrate to RDS with encryption.

**Q3.3**: Are there compliance requirements? (e.g., SOC2, HIPAA, or just general security best practices) 
[Answer]: **No compliance mandates for demo.** Follow general security best practices: input validation, error handling, no secrets in logs. Security Baseline extension enforces these.

**Q3.4**: Should we implement rate limiting to prevent abuse? 
[Answer]: **No rate limiting for demo.** Single-instance, trusted environment. Add at API Gateway or reverse proxy layer if needed in production. 

---

### Step 4: Tech Stack & Infrastructure
- [ ] Confirm web framework (FastAPI — already chosen)
- [ ] Confirm database choice (SQLite — already chosen)
- [ ] Decide on ORM (SQLModel — already chosen)
- [ ] Evaluate AWS services for cost tracking, monitoring, deployment

**Questions for Step 4**:

**Q4.1**: For production deployment, should we consider AWS-managed options?
- A) Stay with SQLite (local file) for simplicity
- B) Migrate to RDS (AWS managed database)
- C) Consider DynamoDB for serverless approach
- D) Keep SQLite for now, make it an upgrade path 
[Answer]: **D) Keep SQLite for now; document RDS migration path.** This aligns with AWS Services Priority steering (evaluate AWS services). Document in tech-stack-decisions.md that RDS is the recommended path for production scale. Keeps demo simple.

**Q4.2**: Should we use AWS cost integration services?
- A) Ingest from AWS Cost Explorer API (real cost data)
- B) Ingest from mock data (for demo)
- C) Both (configurable) 
[Answer]: **B) Mock data for demo.** Real AWS Cost Explorer integration is complex (requires credentials, pagination, format mapping). Use seed data (SQL INSERT). Leave Cost Explorer API integration as future enhancement (document the integration pattern).

**Q4.3**: For monitoring, should we integrate with:
- A) CloudWatch (AWS native)
- B) Prometheus/Grafana
- C) No monitoring (logs to stdout for demo)
- D) Just structured logging (JSON logs) 
[Answer]: **D) Structured JSON logging to stdout.** Simple, AWS-compatible (CloudWatch can tail). Avoid overhead of Prometheus/Grafana for demo. Security Baseline covers logging patterns (no secrets in logs).

**Q4.4**: Should we deploy on:
- A) EC2 instances
- B) ECS/Fargate (containerized)
- C) Lambda + API Gateway (serverless)
- D) Local development only (no production deployment in scope) 
[Answer]: **D) Local development only for this demo.** Deployment instructions will cover running locally with uvicorn. Document Docker containerization and ECS/Fargate as future deployment options (follow AWS Services Priority). 

---

### Step 5: Data Consistency & Integrity
- [ ] Define consistency model (ACID, eventual consistency)
- [ ] Define data retention policies
- [ ] Define validation rigor (strict vs. lenient)

**Questions for Step 5**:

**Q5.1**: Should the system enforce strict ACID semantics (SQLite native) or is eventual consistency acceptable? 
[Answer]: **Strict ACID (SQLite native).** Financial data must be consistent. SQLite provides ACID by default — perfect for this requirement.

**Q5.2**: Should cost data be retained forever, or implement retention policies? (e.g., delete costs older than 7 years) 
[Answer]: **Retained forever for demo.** No retention policies. This aligns with FinOps compliance (keep historical records). Note: Add configurable retention policies as future feature if needed.

**Q5.3**: Should deleted cost entries be soft-deleted (marked deleted) or hard-deleted (removed)? 
[Answer]: **Hard-deleted (removed).** Simpler implementation. Functional design already specifies immutability (delete-only), so hard delete is fine. Soft delete can be added later if audit trail requirement emerges. 

---

### Step 6: Testing & Quality Requirements
- [ ] Define test coverage targets
- [ ] Define types of tests needed (unit, integration, e2e, property-based)
- [ ] Define performance testing needs
- [ ] Define security testing requirements

**Questions for Step 6**:

**Q6.1**: What test coverage target? (e.g., >80%, >90%, or just "comprehensive") 
[Answer]: **>85% line coverage target.** Aim for comprehensive coverage of core logic (ingestion, trends, anomalies). Security Baseline and Property-Based Testing extensions require this level.

**Q6.2**: Is property-based testing required? (Security Baseline extension says yes; confirm?) 
[Answer]: **Yes, property-based testing is mandatory.** PBT extension is enabled. Use Hypothesis for Python. Test round-trip serialization, pagination invariants, anomaly detection edge cases. Showcase AI-DLC by including both example-based and property-based tests.

**Q6.3**: Should we include performance/load testing? (e.g., verify <500ms response times) 
[Answer]: **Smoke test only (not formal load testing).** Create simple stress test: ingest 10K costs, verify trend queries complete in <500ms. Load testing tools (locust, k6) are out of scope for demo.

**Q6.4**: Should we include security testing? (e.g., input validation fuzzing, SQL injection checks) 
[Answer]: **Basic security testing (not fuzzing).** Property-based tests will exercise random inputs. Add explicit SQL injection prevention tests (verify parameterized queries). Security Baseline extension covers this. 

---

### Step 7: Operational Requirements
- [ ] Define deployment process (manual, CI/CD, infrastructure-as-code)
- [ ] Define configuration management (environment vars, secrets)
- [ ] Define logging requirements (level, format, retention)
- [ ] Define documentation requirements

**Questions for Step 7**:

**Q7.1**: Should deployment use CI/CD pipeline? (e.g., GitHub Actions, AWS CodePipeline) 
[Answer]: **GitHub Actions for demo (optional).** Simple CI/CD: lint, test, build. For teaching, keep it minimal. Document as "optional enhancement" — not required for demo to work locally.

**Q7.2**: How should secrets be managed? (e.g., environment vars for demo, Secrets Manager for production) 
[Answer]: **Environment variables for demo.** No secrets needed yet (no auth, no AWS credentials). If AWS Cost Explorer integration added: use `boto3` credential chain (respects AWS CLI config). Document Secrets Manager as production pattern (AWS Services Priority steering).

**Q7.3**: What logging level and format? (e.g., DEBUG, INFO, JSON structured logs) 
[Answer]: **INFO level, JSON structured logs.** Each request logs: timestamp, method, path, status, latency. Errors log: timestamp, error message, context (no stack traces). Structured format is CloudWatch-compatible.

**Q7.4**: Should code be containerized (Docker)? 
[Answer]: **Docker optional (Dockerfile provided, not required to run).** Build image: `docker build -t cloudspend .`. Run locally: `.venv/bin/python -m uvicorn main:app --reload` is simpler. Dockerfile is there for future ECS/Fargate deployment. 

---

## Checkboxes Summary

**Questions Requiring User Input**: 21 questions (all answered)
**All marked with [Answer]: ✅ ANSWERED**

---

## Plan Execution Complete

✅ **All NFR areas assessed:**
1. ✅ Scalability & Performance (4 decisions: demo scale, <500ms SLA, vertical scaling)
2. ✅ Availability & Reliability (4 decisions: best effort SLA, manual backups, single instance, JSON logs)
3. ✅ Security (4 decisions: public/unauthenticated, no encryption at rest, no compliance mandates, no rate limiting)
4. ✅ Tech Stack & Infrastructure (4 decisions: SQLite + RDS migration path, mock data, JSON logging, local deployment)
5. ✅ Data Consistency & Integrity (3 decisions: ACID semantics, forever retention, hard delete)
6. ✅ Testing & Quality (4 decisions: >85% coverage, property-based testing mandatory, smoke tests, security tests)
7. ✅ Operational Requirements (4 decisions: optional CI/CD, env vars for secrets, INFO+JSON logs, Docker optional)
