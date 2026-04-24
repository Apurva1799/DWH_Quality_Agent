## Fact Table: `BFL.Fact_OEE`
---
**Columns:**
- `DateKey` (int)
- `LineKey` (int)
- `AvailabilityPercent` (decimal)
- `PerformancePercent` (decimal)
- `QualityPercent` (decimal)
- `OEE` (decimal)

---

**Related Dimensions:**
- Dim_Date (join over `DateKey`)
- Dim_Line (join over `LineKey`)