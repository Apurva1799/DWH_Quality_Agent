## Fact Table: `BFL.Fact_ForgingPlan_Daily`
---
**Columns:**
- `DateKey` (int)
- `LineKey` (int)
- `DieKey` (int)
- `PlannedQuantity` (decimal)

---

**Related Dimensions:**
- Dim_Date (join over `DateKey`)
- Dim_Die (join over `DieKey`)
- Dim_Line (join over `LineKey`)