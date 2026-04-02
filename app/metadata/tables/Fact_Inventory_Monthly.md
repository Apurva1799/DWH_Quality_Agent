## Fact Table: `BFL.Fact_Inventory_Monthly`
---
**Columns:**
- `InventoryFactKey` (bigint)
- `MaterialKey` (int)
- `StorageLocationKey` (int)
- `DieKey` (int)
- `LineKey` (int)
- `DateKey` (int)
- `MRPController` (nvarchar)
- `ProfitCenter` (nvarchar)
- `UnrestrictedStock` (decimal)
- `InQualityStock` (decimal)
- `RestrictedStock` (decimal)
- `BlockedStock` (decimal)
- `ReturnsStock` (decimal)
- `InTransitStock` (decimal)
- `VendorStock` (decimal)
- `TotalStock` (decimal)
- `TotalValue` (decimal)
- `UnitOfMeasurement` (nvarchar)
- `LoadDate` (datetime2)

---

**Related Dimensions:**
- Dim_Date (join over `DateKey`)
- Dim_Die (join over `DieKey`)
- Dim_Line (join over `LineKey`)
- Dim_Material (join over `MaterialKey`)
- Dim_StorageLocation (join over `StorageLocationKey`) joins with Dim_Plant (join over `PlantKey`)