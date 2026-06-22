# Business Logic Model - Cost Analytics Service

**Unit**: Cost Analytics Service  
**Phase**: Functional Design  
**Date**: 2026-06-19

---

## Overview

This document describes the business logic flows, algorithms, and transformations for the Cost Analytics Service. All logic is technology-agnostic.

---

## Flow 1: Cost Data Ingestion

**Trigger**: POST /cost-data  
**Input**: { service, amount, timestamp, tags (optional) }

**Process**:
1. Validate service (alphanumeric+hyphen, non-empty)
2. Validate amount (positive decimal, 2 places)
3. Validate timestamp (ISO 8601, UTC, not future)
4. Validate tags (each non-empty string, deduplicate)
5. **Create CostEntry** in database:
   - Generate id (UUID)
   - Set created_at = now (server time)
   - Set updated_at = created_at (immutable)
6. **Create/Reference Tags**: For each tag, ensure Tag entity exists (create if not), associate with CostEntry
7. **Return**: Created CostEntry with 201 Created

**Business Logic**:
- Costs are immutable (created_at == updated_at always, never change)
- Tags are created implicitly on first reference (no explicit tag creation endpoint)
- Duplicates are allowed (same service, amount, timestamp can be ingested multiple times)

**Error Cases**:
- Invalid amount → 400 Bad Request
- Invalid service → 400 Bad Request
- Invalid timestamp → 400 Bad Request
- Invalid tag → 400 Bad Request
- Server error → 500

---

## Flow 2: Daily Spending Trends Query

**Trigger**: GET /cost-data/daily?service={optional}&cursor={optional}&limit={optional}

**Input**: 
- service (optional): Filter by service name
- cursor (optional): Pagination cursor
- limit (optional): Page size (default 20, max 100)

**Process**:
1. **Determine Date Range**: 
   - If no historical query params: Fetch all dates with data
   - Cursor determines start date; fetch limit rows from that date forward

2. **Query Daily Aggregates**:
   - SELECT DATE(timestamp), SUM(amount) as total_cost
   - FROM CostEntry
   - WHERE (service = ? OR service is any) [if service filter]
   - GROUP BY DATE(timestamp)
   - ORDER BY DATE(timestamp) DESC (most recent first)

3. **Apply Pagination**:
   - Skip to cursor position (if provided)
   - Limit to limit rows
   - Compute next_cursor (date of last row returned)
   - Set has_more = (more rows exist beyond limit)

4. **Format Response**:
   - Return array of { date, total_cost, cost_count }
   - Include pagination metadata: next_cursor, has_more, items_count

**Business Logic**:
- Sparse response (only dates with data, no zero-fill)
- UTC timezone (all dates in UTC)
- Aggregation at database level (not in-memory)
- Service filter is optional; if provided, only that service's costs

**Error Cases**:
- Invalid cursor → 400 Bad Request
- Invalid limit (< 1 or > 100) → 400 Bad Request
- Invalid service format → 400 Bad Request

---

## Flow 3: Anomaly Detection Query

**Trigger**: GET /cost-data/anomalies?service={optional}

**Input**:
- service (optional): Filter by service name

**Process**:
1. **For Each Service** (or specified service):
   - Fetch all distinct dates with costs (ordered DESC)
   
2. **For Each Date**:
   - Compute baseline_average:
     - Get the 7 calendar days **prior** to this date
     - Fetch all costs for those 7 days
     - Average = SUM(costs) / count(days with data)
     - If <7 days available: use available days only (bootstrap)
   
   - Compute spike:
     - spike_cost = SUM(all costs on this date)
     - spike_percentage = (spike_cost - baseline_average) / baseline_average * 100
   
   - Check threshold:
     - If spike_percentage >= 25: **Anomaly detected**
     - Create anomaly record: { date, service, baseline_average, spike_cost, spike_percentage }

3. **Compile Results**:
   - Sort by spike_percentage DESC (highest impact first)
   - Apply service filter if provided
   - Return all anomalies (no pagination for this demo)

4. **Format Response**:
   - Return array of anomaly records

**Business Logic**:
- Rolling average calculated per date (not a fixed historical window)
- Bootstrap mode: use available data if <7 days exist (don't wait for 7 days)
- Calendar dates (not "7 most recent data points")
- One anomaly per date per service (separate records for multiple spike days)
- Spike percentage included for transparency (allows clients to set own thresholds)

**Example**:
```
Today: 2026-06-19
Baseline (June 12-18): Average = $100
Spike (June 19): $125
Spike %: 25%
→ Anomaly detected and returned
```

**Error Cases**:
- Invalid service format → 400 Bad Request

---

## Flow 4: List Optimization Recommendations

**Trigger**: GET /optimization/recommendations?service={optional}&status={optional}&cursor={optional}&limit={optional}

**Input**:
- service (optional): Filter by service
- status (optional): Filter by status ("recommended", "implemented", "dismissed")
- cursor (optional): Pagination cursor
- limit (optional): Page size (default 20, max 100)

**Process**:
1. **Build Query**:
   - SELECT * FROM Recommendation
   - WHERE (service = ? OR any service) [if service filter]
   - WHERE (status = ? OR any status) [if status filter]
   - ORDER BY estimated_monthly_savings DESC (highest impact first)

2. **Apply Pagination**:
   - Cursor-based pagination (same as daily trends)
   - Limit to limit rows

3. **Format Response**:
   - Return array of recommendation records
   - Include pagination metadata

**Business Logic**:
- Filtering is optional (both service and status)
- Sorting is always by estimated_monthly_savings (descending)
- Recommendations are pre-populated (not created by this API)

**Error Cases**:
- Invalid status filter (not one of the 3 valid statuses) → 400 Bad Request
- Invalid service format → 400 Bad Request

---

## Flow 5: Update Recommendation Status

**Trigger**: PATCH /optimization/{id}

**Input**: 
- id: Recommendation ID
- status: New status ("implemented" or "dismissed")

**Process**:
1. **Fetch Recommendation**: Query by id
   - If not found → 404 Not Found

2. **Validate Status Change**:
   - New status must be one of: "implemented", "dismissed"
   - Current status must be "recommended" (one-way transition)
   - If already "implemented" or "dismissed" → 400 Bad Request ("Cannot transition from {current} to {new}")

3. **Update**:
   - Set status = new_status
   - Set updated_at = now (server time)
   - Persist to database

4. **Return**: Updated Recommendation record with 200 OK

**Business Logic**:
- One-way transitions only (no reversions)
- Status changes are tracked via updated_at
- Only status field is updatable (title, description, savings are immutable)

**Error Cases**:
- Recommendation not found → 404 Not Found
- Invalid status value → 400 Bad Request
- Invalid transition (not from "recommended") → 400 Bad Request
- PATCH other fields → 400 Bad Request (only status allowed)

---

## Flow 6: Delete Cost Entry

**Trigger**: DELETE /cost-data/{id}

**Input**:
- id: Cost Entry ID

**Process**:
1. **Fetch CostEntry**: Query by id
   - If not found → 404 Not Found

2. **Delete**:
   - Remove CostEntry from database
   - Remove associations from join table (many-to-many with Tag)
   - Tags themselves remain (orphaned tags are allowed)

3. **Return**: 204 No Content (empty response)

**Business Logic**:
- Deletion is explicit and permanent
- Cost entries become invisible to queries (trends, anomalies)
- Tags are not deleted (permanent registry)

**Error Cases**:
- Cost entry not found → 404 Not Found

---

## Algorithm Specifications

### Algorithm: 7-Day Rolling Average (Anomaly Detection)

```
function computeAnomalyBaseline(service, targetDate):
  startDate = targetDate - 7 days
  endDate = targetDate - 1 day  (exclude target date)
  
  costs = QueryCosts(service, startDate, endDate)
  
  if costs.isEmpty():
    return 0  # No baseline data yet
  
  baseline = SUM(costs) / COUNT(distinct dates with costs)
  return baseline

function detectAnomalies(service, targetDate):
  baseline = computeAnomalyBaseline(service, targetDate)
  
  spike = QueryCosts(service, targetDate).sum()
  spikePercentage = ((spike - baseline) / baseline) * 100
  
  if spikePercentage >= 25:
    return Anomaly(date=targetDate, service=service, 
                   baseline=baseline, spike=spike, 
                   spikePercentage=spikePercentage)
  else:
    return null
```

---

## Key Design Principles

1. **Immutability**: Cost entries are create-once, delete-only (no updates)
   - **Why**: Audit compliance and financial accuracy
   
2. **One-Way Status**: Recommendation status transitions are irreversible
   - **Why**: Clear audit trail, prevents confusion
   
3. **Implicit Resource Creation**: Tags are created on first reference
   - **Why**: Simpler API (no tag management endpoint), flexible cost allocation
   
4. **Sparse Responses**: Daily trends return only dates with data
   - **Why**: Clean responses, typical for FinOps dashboards
   
5. **Decimal Precision**: All monetary values use Decimal type
   - **Why**: No floating-point rounding errors in financial calculations
   
6. **Transparent Thresholds**: Anomaly spike_percentage always returned
   - **Why**: Allows clients to adjust detection thresholds later

---

## Summary

The business logic is intentionally straightforward to showcase AI-DLC:
- **Clear decision records** — each rule has documented rationale
- **Auditable flows** — easy to trace from requirement to logic to code
- **Testable algorithms** — anomaly detection and aggregation are deterministic
- **FinOps-aligned** — immutable costs, clear optimization tracking, transparent anomaly scoring
