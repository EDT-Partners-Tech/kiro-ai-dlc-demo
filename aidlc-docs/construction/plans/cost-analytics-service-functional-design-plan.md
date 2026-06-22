# Functional Design Plan - Cost Analytics Service

**Unit**: Cost Analytics Service  
**Phase**: Functional Design (CONSTRUCTION)  
**Date**: 2026-06-19  
**Status**: Planning

---

## Plan Overview

This plan outlines the functional design for the Cost Analytics Service, focusing on business logic, domain models, business rules, and data transformations — all technology-agnostic.

---

## Steps to Execute

### Step 1: Domain Model Definition
- [ ] Define CostEntry entity structure and attributes
- [ ] Define Recommendation entity structure and attributes  
- [ ] Define Tag entity and many-to-many relationships
- [ ] Model daily cost aggregation entity
- [ ] Model anomaly detection result structure

**Questions for Step 1**:

**Q1.1**: For the CostEntry entity, should the `timestamp` represent when the cost was **incurred** (actual AWS usage time) or when the cost was **ingested** into our system? 
[Answer]: **Cost incurred time (AWS usage time).** This is the business-relevant timestamp for trend analysis and anomaly detection. Ingestion time is tracked separately via `created_at`.

**Q1.2**: Should we track the **currency** for cost amounts (USD, EUR, etc.) or assume all costs are in a single currency? 
[Answer]: **Assume USD only** for this demo. Multi-currency support can be added in v2 if needed. Simpler now, extensible later.

**Q1.3**: For tags, should we support:
- A) Hierarchical tags (e.g., "team:web", "env:prod") with special parsing?
- B) Flat tags (simple strings)?
- C) Both? 
[Answer]: **B) Flat tags (simple strings).** Keep parsing simple — colons are allowed in tag names but not special syntax. Users can adopt conventions (e.g., "team-web", "env-prod").

**Q1.4**: Should cost entries support partial creation? For example, can a cost be created with just service + amount, and timestamp default to "now"? Or is timestamp always explicitly required? 
[Answer]: **Timestamp is always explicitly required.** This ensures cost data is auditable and matches AWS billing reality. Defaulting to "now" could mask import timing issues. 

---

### Step 2: Business Logic - Cost Data Ingestion
- [ ] Define validation rules for cost amount (positive, decimal precision, range limits)
- [ ] Define validation rules for service name (alphanumeric + hyphens, length limits)
- [ ] Define validation rules for timestamp (ISO 8601, no future dates, optional date range constraints)
- [ ] Define tag creation/association logic
- [ ] Define error scenarios and handling

**Questions for Step 2**:

**Q2.1**: What is the maximum cost amount that should be accepted? Should we reject costs > $1M per entry as potentially erroneous? 
[Answer]: **No hard maximum limit.** Accept any positive amount up to decimal precision (2 decimal places). Large amounts are valid (cloud bills can be substantial). Validation is input sanity checks, not business rule enforcement.

**Q2.2**: Should we maintain a **whitelist of valid service names** (e.g., only EC2, S3, Lambda, etc.) or accept any alphanumeric+hyphen string? 
[Answer]: **Accept any alphanumeric+hyphen string.** This allows flexibility (custom services, future AWS services) without tight coupling. Tag-like filtering handles user queries.

**Q2.3**: For timestamp validation, what is the acceptable **historical date range**? Should we reject costs older than, say, 90 days, 1 year, or accept any past date? 
[Answer]: **Accept any past date (no historical limit).** Users may backfill historical cost data from Cloud Cost Explorer. Reject only future dates (no pre-dated costs).

**Q2.4**: Should duplicate cost entries be **rejected** (if same service, amount, timestamp already exists within X minutes) or **allowed** (same cost can be ingested multiple times)? 
[Answer]: **Allow duplicates.** Different ingestion runs may report the same cost. Deduplication is the responsibility of the ingestion layer. API accepts all valid entries. 

---

### Step 3: Business Logic - Daily Spending Trends
- [ ] Define daily aggregation algorithm (sum all costs per day, group by date)
- [ ] Define date bucketing strategy (UTC timezone, or user timezone?)
- [ ] Define filtering logic by service
- [ ] Define pagination cursor mechanism for daily trends
- [ ] Define response structure (date, total_spend, service breakdown)

**Questions for Step 3**:

**Q3.1**: When aggregating daily costs, should we use **UTC timezone** or allow timezone customization? 
[Answer]: **Use UTC timezone.** This is cloud-standard and removes ambiguity. Single timezone for all users simplifies implementation. Users can interpret results in local time if needed.

**Q3.2**: Should daily trends include **costs per service** (e.g., "date": "2026-06-19", "EC2": 150.00, "S3": 50.00) or just a single total per day? 
[Answer]: **Just a single total per day per query.** If user requests "EC2" trends, return dates with EC2 totals. If no service filter, return all services combined per day. Simpler response, avoids data explosion.

**Q3.3**: If the user requests daily trends with a service filter, should we return:
- A) Only days when that service had costs?
- B) All days in the date range (with 0 for days the service had no costs)?
- C) The user's choice? 
[Answer]: **A) Only days when that service had costs.** Sparse response, cleaner for FinOps dashboards. Users can backfill zeros in their UI if needed.

**Q3.4**: For pagination cursors, should the cursor be **date-based** (next page starts from date X) or **record-based** (next page starts from record ID Y)? 
[Answer]: **Date-based cursor.** More intuitive for time-series data (e.g., "next page from 2026-06-10 onward"). Record-based cursors would leak internal IDs. 

---

### Step 4: Business Logic - Anomaly Detection
- [ ] Define rolling average calculation (7-day window, how to handle edges?)
- [ ] Define spike detection algorithm (25% above average)
- [ ] Define anomaly score/confidence (binary flag vs. percentage above threshold)
- [ ] Define data requirements (minimum historical data needed for detection)
- [ ] Define filtering logic by service

**Questions for Step 4**:

**Q4.1**: For the 7-day rolling average, how should we handle **the first week of data** (when fewer than 7 days exist)? 
- A) Use available data only (e.g., 3-day average if only 3 days exist)?
- B) Don't report anomalies until 7 days of data exist?
- C) Use a configurable minimum (e.g., need at least 3 days)? 
[Answer]: **A) Use available data only.** Start detecting anomalies immediately, even with limited history. Better to flag early spikes than wait 7 days. Confidence will naturally increase as more data accumulates.

**Q4.2**: Should anomaly detection use **calendar dates** (7 calendar days ago) or **7 most recent days of data** (ignoring gaps)? 
[Answer]: **Calendar dates (7 calendar days ago).** Cloud cost data is continuous. Using calendar days aligns with FinOps reporting periods. Simpler for users to reason about ("compare this week to last week").

**Q4.3**: Should we track **anomaly confidence/score** (e.g., "25% spike", "50% spike") or just return a boolean "is anomaly" flag? 
[Answer]: **Return both.** Include the spike percentage (e.g., "baseline": 100.00, "spike": 125.00, "spike_percentage": 25). Allows dashboards to prioritize high-impact anomalies.

**Q4.4**: For a single service over 7 days, if we detect multiple anomalies (e.g., June 15 AND June 18), should we return:
- A) One anomaly record per day (separate records)?
- B) One anomaly record per "spike event" (consecutive spikes = 1 event)?
- C) Aggregated (one record summarizing all anomalies for that service in the period)? 
[Answer]: **A) One anomaly record per day.** Simplest to implement and query. Allows FinOps teams to track individual spike days. Post-processing can group consecutive spikes if needed. 

---

### Step 5: Business Logic - Optimization Recommendations
- [ ] Define recommendation lifecycle (recommended → implemented/dismissed)
- [ ] Define filtering logic by service and status
- [ ] Define sorting by savings (descending)
- [ ] Define pagination for recommendations list
- [ ] Define status transition rules (can dismissed be re-opened?)

**Questions for Step 5**:

**Q5.1**: Should recommendations allow **status transitions** (e.g., dismissed → recommended again), or are they **one-way** (implemented/dismissed is final)? 
[Answer]: **One-way transitions only.** Once "implemented" or "dismissed", a recommendation cannot revert. If a dismissed recommendation becomes relevant again, it's a new recommendation. Preserves audit trail and prevents confusion.

**Q5.2**: Should we track **who made** status updates and **when** (audit trail)? Or just store the current status? 
[Answer]: **Track `updated_at` timestamp only.** No user/actor tracking for this demo (no auth system). `updated_at` field is sufficient for compliance and debugging. Full audit trail can be added in v2.

**Q5.3**: Should recommendations have an **expiration or age limit**? E.g., delete recommendations older than 90 days, or keep them forever? 
[Answer]: **Keep them forever.** Recommendations are immutable once created. Deleting old recommendations loses historical data. Users can filter by status ("dismissed") if they want to archive.

**Q5.4**: Should the API allow **creating or modifying recommendations** (via POST/PATCH), or are recommendations **read-only** (pre-populated externally)? 
[Answer]: **Read-only in this demo.** Recommendations are pre-loaded (external process or database seed). The API only allows status updates. Keeps scope focused on cost tracking + analysis, not recommendation generation. 

---

### Step 6: Business Logic - Error Handling & Edge Cases
- [ ] Define handling of concurrent writes (two simultaneous cost ingestions)
- [ ] Define handling of missing/invalid data
- [ ] Define handling of out-of-order cost ingestions (cost from yesterday arriving today)
- [ ] Define handling of duplicate ingestions
- [ ] Define error response schema (error codes, messages)

**Questions for Step 6**:

**Q6.1**: For **concurrent cost ingestions**, should we:
- A) Accept all (allow duplicates)?
- B) Use database-level locking (slower, no duplicates)?
- C) Accept with idempotency key (same key = same result)? 
[Answer]: **A) Accept all.** SQLite with ACID guarantees handles concurrent writes. Accept all valid entries — duplicates are acceptable. Idempotency keys add complexity; deduplication is for the ingestion pipeline, not the API.

**Q6.2**: Should we expose **internal error codes** (e.g., "ERR_INVALID_AMOUNT") in the API response, or just HTTP status codes + human message? 
[Answer]: **HTTP status codes + human messages only.** Security best practice: don't expose internal error codes to API clients. Detailed errors are for logs (for debugging), not API responses.

**Q6.3**: If a user tries to update a recommendation to an invalid status (e.g., "ready" instead of "implemented"), should we:
- A) Reject with 400 Bad Request?
- B) Silently ignore the invalid status?
- C) Auto-correct to nearest valid status? 
[Answer]: **A) Reject with 400 Bad Request.** Explicit failure is better than silent failure. Clear error message helps clients debug. Security Baseline extension requires proper input validation. 

---

### Step 7: Generate Functional Design Artifacts
- [x] Create `business-logic-model.md` (algorithms, workflows)
- [x] Create `business-rules.md` (validation rules, constraints, transitions)
- [x] Create `domain-entities.md` (entity definitions, relationships, attributes)

---

## Checkboxes Summary

**Questions Requiring User Input**: 13 questions (all answered)
**All marked with [Answer]: ✅ ANSWERED**

---

## Plan Execution Complete

✅ **All steps executed:**
1. ✅ Domain Model Definition (4 decisions made)
2. ✅ Cost Data Ingestion Logic (4 decisions made)
3. ✅ Daily Spending Trends (4 decisions made)
4. ✅ Anomaly Detection (4 decisions made)
5. ✅ Optimization Recommendations (4 decisions made)
6. ✅ Error Handling & Edge Cases (3 decisions made)
7. ✅ Functional Design Artifacts Generated
