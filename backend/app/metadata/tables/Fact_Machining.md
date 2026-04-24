## Fact Table: `BFL.Fact_Machining`
---
**Columns:**
- `ShiftKey` (int)
- `MachinedDateKey` (int)
- `LineKey` (int)
- `OrderID` (nvarchar)
- `DieKey` (int)
- `MachinedQuantity` (float)
- `MachinedInTons` (decimal)

---

**Related Dimensions:**
- Dim_Date (join over `MachinedDateKey -> DateKey`)
- Dim_Die (join over `DieKey`)
- Dim_Line (join over `LineKey`)
- Dim_Shift (join over `ShiftKey`)