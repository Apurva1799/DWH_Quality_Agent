## Fact Table: `BFL.Fact_BOM`
---
**Columns:**
- `ParentMaterialKey` (int)
- `ComponentMaterialKey` (int)
- `PlantKey` (int)
- `StorageLocationKey` (int)
- `ValidFromDateKey` (int)
- `ValidToDateKey` (int)
- `BOMNumber` (varchar)
- `BOMAlternative` (varchar)
- `BOMItemNodeNumber` (varchar)
- `ItemNumber` (varchar)
- `ItemCategory` (varchar)
- `BOMTypeCode` (varchar)
- `BOMTypeDescription` (varchar)
- `BOMUsageCode` (varchar)
- `BOMUsageDescription` (varchar)
- `MaterialQuantity` (decimal)
- `MaterialUnitOfMeasure` (varchar)
- `ComponentQuantity` (decimal)
- `ComponentUnitOfMeasure` (varchar)
- `IsActive` (bit)
- `LoadDate` (datetime2)

---

**Related Dimensions:**
- Dim_Plant (join over `PlantKey`) joins with Dim_StorageLocation (join over `PlantKey`), Dim_EquipmentMaintenance (join over `PlantID`)
- Dim_StorageLocation (join over `PlantKey`) joins with Dim_Plant (join over `PlantKey`)
- Dim_StorageLocation (join over `StorageLocationKey`) joins with Dim_Plant (join over `PlantKey`)