## Dimension Table: `BFL.Dim_Plant`
---
**Column Profiles:**

*   `PlantKey` (int)
*   `PlantID` (nvarchar(10))
    *   **Mode 5 values (most frequent):** `1102`, `1101`, `1100`, `1001`, `1000`
*   `PlantName` (nvarchar(100))
    *   **Mode 5 values (most frequent):** `BHARAT FORGE LIMITED`, `Industrial Inspection Company`, `DROMADER USA, LLC`, `Industrial Inspection Co`, `Industrial Inspn.Com(US MFG)`
*   `StartDate` (datetime2)
    *   **All Values:** `2025-08-27 08:50:22.943000`, `2025-11-17 07:13:51.083000`, `2026-01-05 09:13:49.484000`
*   `EndDate` (datetime2)
    *   **Values:** *No data found.*
*   `IsActiveFlag` (bit)
    *   **All Values:** `True`

---

**Referenced Dimensions:**
- Dim_StorageLocation (via `PlantKey` -> `PlantKey`)
- Dim_EquipmentMaintenance (via `PlantID` -> `PlantID`)