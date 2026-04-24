## Fact Table: `BFL.Fact_AssetMonitoring`
---
**Columns:**
- `CompanyCodeKey` (int)
- `AssetKey` (int)
- `AssetClassKey` (int)
- `AvailabilityKey` (int)
- `CapitalizationDateKey` (int)
- `DeactivationDateKey` (int)
- `PlantKey` (int)
- `AssetMonitoringLocationKey` (int)
- `CostCenter` (varchar)
- `BusinessAreaKey` (int)
- `AssetProcurementCost` (decimal)
- `DepreciationValue` (decimal)
- `NetBookValue` (decimal)
- `CurrencyCodeKey` (int)
- `Quantity` (decimal)
- `BusinessQuantityUnitKey` (int)

---

**Related Dimensions:**
- Dim_AssetMonitoringAvailability (join over `AvailabilityKey`)
- Dim_AssetMonitoringBusinessArea (join over `BusinessAreaKey`)
- Dim_AssetMonitoringClassDescription (join over `AssetClassKey`)
- Dim_AssetMonitoringDescription (join over `AssetKey`)
- Dim_AssetMonitoringLocation (join over `AssetMonitoringLocationKey`)
- Dim_BusinessQuantityUnit_sales (join over `BusinessQuantityUnitKey`)
- Dim_CompanyCode_Sales (join over `CompanyCodeKey`)
- Dim_CurrencyCode_Sales (join over `CurrencyCodeKey`)
- Dim_Plant (join over `PlantKey`) joins with Dim_StorageLocation (join over `PlantKey`), Dim_EquipmentMaintenance (join over `PlantID`)
- Dim_StorageLocation (join over `PlantKey`) joins with Dim_Plant (join over `PlantKey`)