## Fact Table: `BFL.Fact_DieCasting`
---
**Columns:**
- `ShiftKey` (int)
- `CastingDateKey` (int)
- `LineKey` (int)
- `OrderID` (varchar)
- `DieKey` (int)
- `CastingQuantity` (decimal)
- `CastingInTons` (decimal)

---

**Related Dimensions:**
- Dim_Date (join over `CastingDateKey -> DateKey`)
- Dim_Die (join over `DieKey`)
- Dim_Line (join over `LineKey`)
- Dim_Shift (join over `ShiftKey`)