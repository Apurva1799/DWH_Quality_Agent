## Fact Table: `BFL.Fact_PlannedCycleTime`
---
**Columns:**
- `LineKey` (int)
- `DieKey` (int)
- `FromDateKey` (int)
- `ToDateKey` (int)
- `PlannedCycleTimeInSeconds` (decimal)

---

**Related Dimensions:**
- Dim_Die (join over `DieKey`)
- Dim_Line (join over `LineKey`)