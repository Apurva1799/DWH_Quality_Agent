## Fact Table: `BFL.Fact_Forging_DieLevel_PeriodicSnapshot`
---
**Columns:**
- `ShiftKey` (int)
- `ForgedDateKey` (int)
- `LineKey` (int)
- `OrderID` (varchar)
- `DieKey` (int)
- `ForgedQuantity` (decimal)
- `ForgedInTons` (decimal)

---

**Related Dimensions:**
- Dim_Date (join over `ForgedDateKey -> DateKey`)
- Dim_Die (join over `DieKey`)
- Dim_Line (join over `LineKey`)
- Dim_Shift (join over `ShiftKey`)