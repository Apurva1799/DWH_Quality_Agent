## Fact Table: `BFL.Fact_Forging_DieSpareLevel_AccumulatingSnapshot`
---
**Columns:**
- `StartDateKey` (int)
- `EndDateKey` (int)
- `LineKey` (int)
- `DieKey` (int)
- `RunID` (varchar)
- `DieSpareChangeID` (varchar)
- `OrderID` (varchar)
- `ForgedQuantity` (decimal)

---

**Related Dimensions:**
- Dim_Date (join over `StartDateKey -> DateKey`)
- Dim_Date (join over `EndDateKey -> DateKey`)
- Dim_Die (join over `DieKey`)
- Dim_Line (join over `LineKey`)