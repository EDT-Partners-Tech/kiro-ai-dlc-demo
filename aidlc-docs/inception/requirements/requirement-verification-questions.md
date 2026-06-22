# CloudSpend Analytics API - Requirement Verification Questions

This document captures verification questions asked during Requirements Analysis to ensure requirements completeness and clarity.

---

## Verification Q&A

### Q1: Cost Data Completeness
**Question**: Should cost entries support multiple currencies, or assume all costs are in USD?

**Decision**: Assume all costs are in USD. The demo is scoped to single-currency operations. Multi-currency support can be added in future versions if needed.

---

### Q2: Anomaly Detection Recency
**Question**: How should anomaly detection behave with less than 7 days of historical data?

**Decision**: Use available data (minimum 1 day) to establish rolling average. If fewer than 3 days exist, flag all entries as potential anomalies with a note about insufficient historical data. This allows early detection even with limited data.

---

### Q3: Recommendation Creation
**Question**: Are recommendations created via API or pre-loaded/managed separately?

**Decision**: For this demo, recommendations are pre-loaded or managed separately (not exposed in this API). The API only provides read/update access to recommendations. This keeps the scope focused on cost tracking and analysis rather than recommendation generation logic.

---

### Q4: Historical Cost Data
**Question**: Should the API support backdated cost entries (costs from past timestamps)?

**Decision**: Yes. Accept any valid ISO 8601 timestamp, but not future-dated. This allows importing historical cost data from external sources (e.g., AWS Cost Explorer).

---

### Q5: Tag Filtering Breadth
**Question**: Should tag filtering be exact match or support wildcards/partial matches?

**Decision**: Exact match only. Tags are created implicitly during cost entry creation and are treated as exact identifiers. Wildcards can be added later if filtering complexity increases.

---

### Q6: Cost Modifications
**Question**: Once a cost entry is created, can it be updated or only deleted?

**Decision**: Cost entries cannot be updated (no PATCH endpoint). They can only be deleted if mistakenly created. This enforces immutability of the financial record once ingested, which is important for audit compliance.

---

### Q7: Service Name Standardization
**Question**: Should service names be validated against a predefined AWS service list?

**Decision**: No hard validation against a service list. Accept any alphanumeric + hyphen string. This allows custom service names and avoids tight coupling to AWS service definitions. Validation can be tightened in future versions.

---

### Q8: Decimal Precision
**Question**: How many decimal places should be supported for cost amounts?

**Decision**: 2 decimal places (USD cents). Use Python `Decimal` type with `ROUND_HALF_UP` rounding to ensure accuracy. Costs more granular than cents can be aggregated before submission.

---

### Q9: Pagination Cursor Format
**Question**: Should cursor be opaque (base64-encoded ID) or human-readable (timestamp/ID)?

**Decision**: Opaque base64-encoded format for API stability. Internal cursor format can change without breaking clients.

---

### Q10: Deleted Entry Querying
**Question**: After a cost entry is deleted, should it remain queryable in anomaly detection or trend reports?

**Decision**: Once deleted, the entry is removed from all queries. Deleted costs do not affect anomaly baselines. This ensures deletion is semantically clean.

---

## Summary

All questions have been addressed and incorporated into the requirements document. The requirements are now ready for Implementation Planning phase.
