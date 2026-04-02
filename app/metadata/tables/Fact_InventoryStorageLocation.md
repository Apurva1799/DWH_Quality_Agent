## Fact Table: `BFL.Fact_InventoryStorageLocation`
---
**Columns:**
- `InventoryFactKey` (bigint)
- `StorageLocationKey` (int)
- `DieKey` (int)
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
- `LoadDate` (datetime2)
- `UnitOfMeasurement` (nvarchar)
- `MaterialKey` (int)

---

**Related Dimensions:**
- Dim_Date (join over `DateKey`)
- Dim_Die (join over `DieKey`)
- Dim_Location_manpower (join over `StorageLocationKey -> LocationKey`)
- Dim_Material (join over `MaterialKey`) joins with Dim_MaterialGold (join over `MaterialKey`)
- Dim_MaterialGold (join over `MaterialKey`) joins with Dim_Material (join over `MaterialKey`)
- Dim_StorageLocation (join over `StorageLocationKey`) joins with Dim_Plant (join over `PlantKey`)