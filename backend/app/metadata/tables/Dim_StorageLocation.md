## Dimension Table: `BFL.Dim_StorageLocation`
---
**Column Profiles:**

*   `StorageLocationKey` (int)
*   `PlantKey` (int)
*   `StorageLocationID` (nvarchar(10))
    *   **Mode 5 values (most frequent):** `0001`, `FG01`, `SCRP`, `SF01`, `SCT1`
*   `StartDate` (datetime2)
    *   **All Values:** `2025-09-22 09:39:01.125000`, `2025-11-10 00:00:00`, `2025-11-27 11:51:00.763000`, `2025-12-25 22:49:13.490000`, `2026-01-05 09:34:31.179000`, `2026-01-22 22:48:15.276000`
*   `EndDate` (datetime2)
    *   **Values:** *No data found.*
*   `IsActiveFlag` (bit)
    *   **All Values:** `True`

---

**Referenced Dimensions:**
- Dim_Plant (via `PlantKey` -> `PlantKey`)