## Fact Table: `BFL.Fact_HeatedQuantyAndTons`
---
**Columns:**
- `DateKey` (int)
- `PlantKey` (int)
- `ShiftKey` (int)
- `LineKey` (int)
- `DieKey` (int)
- `OrderNo` (nvarchar)
- `BilletHeated` (decimal)
- `HeatedTons` (decimal)
- `ProcessedTimestamp` (datetime)

---

**Related Dimensions:**
- Dim_Date (join over `DateKey`)
- Dim_Die (join over `DieKey`)
- Dim_Line (join over `LineKey`)
- Dim_Plant (join over `PlantKey`) joins with Dim_StorageLocation (join over `PlantKey`), Dim_EquipmentMaintenance (join over `PlantID`)
- Dim_Shift (join over `ShiftKey`)
- Dim_StorageLocation (join over `PlantKey`) joins with Dim_Plant (join over `PlantKey`)