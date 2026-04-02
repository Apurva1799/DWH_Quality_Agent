## Fact Table: `BFL.Fact_ForgingPlan_Monthly`
---
**Columns:**
- `PlanVersionNumber` (int)
- `DateKey` (int)
- `LineKey` (int)
- `DieKey` (int)
- `PlannedForgingQuantity` (decimal)
- `PlannedForgingInTons` (decimal)

---

**Related Dimensions:**
- Dim_Date (join over `DateKey`)
- Dim_Die (join over `DieKey`)
- Dim_Line (join over `LineKey`)