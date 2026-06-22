# Tech Stack Decisions - Cost Analytics Service

**Unit**: Cost Analytics Service  
**Phase**: NFR Requirements  
**Date**: 2026-06-19

---

## Overview

This document captures technology stack decisions, evaluates AWS services (per AWS Services Priority steering), and documents rationale for each choice.

---

## Confirmed Tech Stack

| Layer | Technology | Version | Rationale |
|-------|-----------|---------|-----------|
| **Language** | Python | 3.11 | Already chosen; widely used for FinOps scripting |
| **Web Framework** | FastAPI | Latest | Already chosen; async, fast, auto-docs |
| **ORM** | SQLModel | Latest | Already chosen; combines SQLAlchemy + Pydantic |
| **Database** | SQLite | (bundled) | File-based, ACID, zero-config (ideal for demo) |
| **Testing** | pytest | Latest | Python standard; excellent for unit + integration tests |
| **Property-Based Testing** | Hypothesis | Latest | Python gold standard for PBT |
| **Async Runtime** | asyncio | (built-in) | FastAPI native; sufficient for demo |
| **Package Manager** | pip | Latest | Standard Python; requirements.txt for reproducibility |

---

## AWS Services Evaluation (Per Steering Rules)

**Steering Rule**: "When designing new features, prioritize AWS services as the primary solution before considering third-party libraries or custom implementations."

### Decision: Database Storage

**Requirement**: Store cost entries, recommendations, and tags persistently

**AWS Services Evaluated**:

1. **Amazon RDS (PostgreSQL/MySQL)** ✅ Candidate
   - Fit: Excellent (relational, ACID, managed)
   - Cost: ~$10-50/month (small instances)
   - Scalability: Yes (read replicas, vertical scaling)
   - Operational Overhead: Moderate (AWS manages patches, backups)
   - **Verdict**: Ideal for production; requires demo to use local RDS or skip for now

2. **Amazon DynamoDB** ❌ Rejected
   - Fit: Poor (eventual consistency, key-value focus)
   - Rationale: Anomaly detection requires complex queries (7-day rolling average calculation). DynamoDB excels at KV lookups, struggles with aggregations. Would require application-level aggregation (defeats purpose).
   - **Better For**: Real-time event streams, simple lookups (not financial aggregation)

3. **Amazon Redshift** ❌ Rejected
   - Fit: Overkill (OLAP data warehouse, not OLTP API)
   - Rationale: Designed for analytical queries on historical data, not transactional API serving. Massive overkill for demo scale.
   - **Better For**: Enterprise data warehouses with petabyte-scale data

4. **Amazon ElastiCache** ❌ Rejected (Cache Only)
   - Fit: Partial (great for caching, not persistence)
   - Rationale: Redis/Memcached are caches. Could cache daily trends, but don't solve persistence. Would need RDS anyway.
   - **Better For**: Caching layer on top of RDS (future optimization)

**Decision**: 
- **Demo**: Use **SQLite** (local file, zero AWS infrastructure)
- **Production Upgrade Path**: Migrate to **Amazon RDS PostgreSQL** (ACID, scales to millions of records)
- **Rationale**: Keeps demo simple and free; RDS is documented as v2 migration target (follow AWS Services Priority)

**AWS Services Priority Compliance**: ✅ Evaluated RDS, DynamoDB, Redshift, ElastiCache; chose SQLite for demo with clear RDS migration path documented

---

### Decision: Monitoring & Logging

**Requirement**: Emit logs and metrics for operational visibility

**AWS Services Evaluated**:

1. **Amazon CloudWatch** ✅ Candidate
   - Fit: Excellent (log ingestion, metrics, dashboards)
   - Integration: Simple (send JSON logs to stdout, CloudWatch agent can tail)
   - Cost: ~$0.50/month for demo volume
   - **Verdict**: Perfect for production; for demo, just use stdout (compatible with CloudWatch)

2. **Amazon X-Ray** ❌ Rejected
   - Fit: Overkill (distributed tracing for microservices)
   - Rationale: Demo has single service; X-Ray is for tracing across multiple services. Unnecessary overhead.
   - **Better For**: Multi-service architectures

3. **Amazon Managed Prometheus** ❌ Rejected
   - Fit: Possible (metrics collection)
   - Rationale: Requires Prometheus client library + additional infrastructure. CloudWatch is simpler and native to AWS.
   - **Better For**: Multi-region observability or open-source preference

**Decision**:
- **Demo**: Use **structured JSON logs to stdout** (CloudWatch-compatible, no AWS infrastructure)
- **Production**: Integrate with **Amazon CloudWatch** (native AWS service)
- **Rationale**: Demo remains simple; production logging is one environment variable away

**AWS Services Priority Compliance**: ✅ Evaluated CloudWatch, X-Ray, Prometheus; chose stdout logs with CloudWatch integration path

---

### Decision: Cost Data Integration

**Requirement**: Ingest cloud cost data from AWS

**AWS Services Evaluated**:

1. **AWS Cost Explorer API** ✅ Candidate
   - Fit: Perfect (native AWS cost data)
   - Complexity: High (authentication, pagination, format mapping, historical backfill)
   - Timeline: Requires boto3 setup, testing with real AWS account
   - **Verdict**: Ideal for production; too complex for demo

2. **AWS Billing API** ❌ Rejected
   - Fit: Excellent (detailed billing data)
   - Complexity: Very high (requires bill ingestion, parsing, aggregation)
   - **Better For**: Enterprise billing analytics

3. **Third-Party: DataDog/New Relic Cost Monitoring** ❌ Out of Scope
   - Outside AWS, requires external account
   - **Note**: Document as alternative if multi-cloud needed

**Decision**:
- **Demo**: Use **mock seed data** (SQL INSERT statements with sample costs)
- **Production**: Implement **AWS Cost Explorer API integration** (documented in code + upgrade plan)
- **Rationale**: Keeps demo focused on FinOps logic, not AWS API integration. Integration pattern can be added after core API is stable.

**AWS Services Priority Compliance**: ✅ Evaluated Cost Explorer, Billing API; chose mock data with Cost Explorer integration path

---

### Decision: Secrets Management

**Requirement**: Manage configuration and sensitive data

**AWS Services Evaluated**:

1. **AWS Secrets Manager** ✅ Candidate
   - Fit: Excellent (key-value pairs, rotation, audit logs)
   - Cost: ~$0.40/secret/month
   - Complexity: Low (simple boto3 calls)
   - **Verdict**: Best for production; overkill for demo (no secrets yet)

2. **AWS Parameter Store (Systems Manager)** ✅ Candidate
   - Fit: Good (configuration management)
   - Cost: Free tier (first 10 parameters)
   - Complexity: Low
   - **Verdict**: Alternative to Secrets Manager; comparable

3. **Environment Variables** ✅ Candidate (Non-AWS)
   - Fit: Adequate (for demo and local dev)
   - Security: Acceptable (no sensitive data yet)
   - **Verdict**: Sufficient for demo

**Decision**:
- **Demo**: Use **environment variables** (DATABASE_URL, LOG_LEVEL)
- **Production**: Migrate to **AWS Secrets Manager** (audit trail, encryption, rotation)
- **Rationale**: Demo has no secrets; environment variables are sufficient. Secrets Manager is documented as production enhancement.

**AWS Services Priority Compliance**: ✅ Evaluated Secrets Manager, Parameter Store; chose environment variables with Secrets Manager migration path

---

### Decision: Deployment & Container Orchestration

**Requirement**: Deploy and run the API service

**AWS Services Evaluated**:

1. **AWS Lambda + API Gateway** ✅ Candidate
   - Fit: Good (serverless, auto-scaling)
   - Complexity: High (FastAPI → Lambda adapter, cold start issues, DynamoDB for state)
   - **Verdict**: Possible for demo but adds complexity; saves for v2

2. **Amazon ECS/Fargate** ✅ Candidate
   - Fit: Excellent (containerized, managed scaling)
   - Complexity: Moderate (Docker image + ECS task definition)
   - **Verdict**: Production-ready; overkill for demo

3. **Amazon EC2** ✅ Candidate
   - Fit: Good (full control, simple for demo)
   - Complexity: Low (just run uvicorn)
   - **Verdict**: Good for small demo deployment

4. **Local Development** ✅ Candidate
   - Fit: Perfect for teaching (no AWS infrastructure)
   - Complexity: Minimal
   - **Verdict**: Recommended for demo

**Decision**:
- **Demo**: Run **locally** (`.venv/bin/python -m uvicorn main:app --reload`)
- **Optional Docker**: Provide Dockerfile (for future ECS deployment)
- **Production Options**: EC2, ECS/Fargate, or Lambda (document all patterns)
- **Rationale**: Local deployment keeps demo simple and free. Dockerfile enables future AWS deployment without code changes.

**AWS Services Priority Compliance**: ✅ Evaluated Lambda, ECS/Fargate, EC2, local; chose local for demo with clear upgrade paths

---

### Decision: Testing Framework

**Requirement**: Write and run tests

**AWS Services Evaluated**:

1. **AWS CodeBuild** ✅ Candidate
   - Fit: Good (CI/CD pipeline execution)
   - Complexity: Moderate (buildspec.yml)
   - **Verdict**: Good for production CI/CD; overkill for demo

2. **GitHub Actions** ✅ Candidate (Non-AWS but GitHub-native)
   - Fit: Excellent (simple YAML workflows)
   - Complexity: Low (basic test steps)
   - **Verdict**: Recommended for demo CI/CD

3. **Local Testing** ✅ Candidate
   - Fit: Perfect (pytest runs locally)
   - Complexity: Minimal
   - **Verdict**: Recommended for development loop

**Decision**:
- **Demo Dev Loop**: Run **pytest locally** (`.venv/bin/python -m pytest`)
- **Optional CI/CD**: Add **GitHub Actions workflow** (lint, test, build; optional enhancement)
- **Production**: Use **AWS CodeBuild** or **GitHub Actions** for pipeline
- **Rationale**: Local testing is fastest for development. GitHub Actions is a free, low-friction enhancement if desired.

**AWS Services Priority Compliance**: ✅ Evaluated CodeBuild, GitHub Actions, local; chose local with optional GitHub Actions

---

## Non-AWS Technology Choices

### Testing Libraries (No AWS Equivalent)

1. **pytest**: Python testing framework
   - **Why pytest**: Gold standard, excellent fixtures, plugin ecosystem
   - **AWS Alternative**: None (AWS doesn't provide testing framework)

2. **Hypothesis**: Property-based testing library
   - **Why Hypothesis**: Best-in-class PBT for Python; catches edge cases
   - **Mandatory**: Part of Property-Based Testing extension
   - **AWS Alternative**: None (AWS doesn't provide PBT framework)

3. **black**: Code formatter
   - **Why black**: Opinionated, zero-config, community standard
   - **AWS Alternative**: None

### Web/Data Libraries (Preferred over AWS)

1. **SQLAlchemy/SQLModel**: ORM
   - **Why SQLModel**: Combines SQLAlchemy (mature) + Pydantic (modern); best of both
   - **AWS Alternative**: None (AWS provides no ORM)

2. **Pydantic**: Data validation
   - **Why Pydantic**: De facto standard for Python; tight FastAPI integration
   - **AWS Alternative**: None

---

## Migration Paths & Upgrade Scenarios

### Scenario 1: Demo → Small Production (Same Architecture, Better Hardware)

```
Local SQLite → RDS PostgreSQL
└─ No code changes needed (SQLModel/SQLAlchemy handles DB abstraction)
```

### Scenario 2: Demo → Containerized Deployment

```
Local uvicorn → Docker image → ECS/Fargate
└─ Dockerfile already provided
└─ No code changes needed (uvicorn is container-friendly)
```

### Scenario 3: Demo → Serverless

```
Local API → Lambda + API Gateway
└─ Requires Mangum adapter for FastAPI
└─ Significant code changes (environment, database connection pooling)
└─ Consider if: Traffic is bursty (save on idle costs)
└─ Not recommended for FinOps (prefer predictable per-second costs)
```

### Scenario 4: Demo → Multi-Region

```
Single instance → RDS Multi-AZ + CloudFront
└─ Requires read replicas for load distribution
└─ Requires CloudFront for edge caching
└─ Not recommended for demo scale
```

---

## Cost Estimates

| Scenario | Monthly Cost | Notes |
|----------|-------------|-------|
| **Demo (Local)** | $0 | Free (your laptop) |
| **Demo (Single EC2)** | $5-10 | t2.micro free tier, or t3.small |
| **Prod (RDS + EC2)** | $30-100 | Small RDS instance + t3.small EC2 |
| **Prod (ECS Fargate)** | $50-200 | Fargate pricing (vCPU hours + GB hours) |
| **Prod (Lambda)** | $10-50 | If traffic is bursty; flat cost if steady |

---

## Summary

**Tech Stack Alignment with AWS Services Priority**:
- ✅ Evaluated AWS services (RDS, DynamoDB, CloudWatch, Cost Explorer, etc.)
- ✅ Chose SQLite + RDS migration path (balances demo simplicity with production capability)
- ✅ Chose stdout logs + CloudWatch integration path (same balance)
- ✅ Chose local deployment + documented ECS/Fargate paths (multiple upgrade routes)
- ✅ Clear rationale for every AWS service decision (accepted or rejected with explanation)

**Key Principle**: Demo prioritizes clarity and simplicity (local, single-file database, minimal infrastructure), while documenting production upgrade paths that leverage AWS services (RDS, CloudWatch, ECS, Secrets Manager).

This approach showcases AI-DLC decision-making: each technology choice has documented tradeoffs and upgrade paths, making the reasoning transparent and auditable.
