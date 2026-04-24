## Dimension Table: `BFL.Dim_EquipmentMaintenance`
---
**Column Profiles:**

*   `EquipmentKey` (varchar(18))
    *   **Mode 5 values (most frequent):** `010000000000023726`, `010000000000023683`, `010000000000023597`, `010000000000023557`, `010000000000023552`
*   `EquipmentName` (nvarchar(100))
    *   **Mode 5 values (most frequent):** `MK Angular Grinding Machine`, `CNC MILLING MACHINE, NDS`, `AXIS TO AXIS TURNING`, `VMC MACHINE, LMW, MCD CHAKAN`, `MICROMER-3`
*   `PlantID` (varchar(4))
    *   **All Values:** ``, `6100`, `6200`, `7100`, `7200`, `7300`, `7310`, `8200`, `8201`
*   `FunctionalLocation` (varchar(40))
    *   **Mode 5 values (most frequent):** `BFL-MU-CDFD-FMD02`, `BFL-MU-CDFD-FMD01`, ``, `BFL-MU-CDFD-FMD03`, `BFL-MU-CDFD-FMD02-JAEWO`
*   `WorkCenterID` (varchar(8))
    *   **Values:** *No data found.*
*   `WorkCenterName` (nvarchar(40))
    *   **Mode 5 values (most frequent):** `EUTILITY`, `MHT`, `EA2SKSF`, `MUTILITY`, `XMCD1`
*   `EquipmentLocation` (varchar(10))
    *   **Mode 5 values (most frequent):** `A2LINE`, `FMD2`, ``, `PZS1`, `FMD1`

---

**Referenced Dimensions:**
- Dim_Plant (via `PlantID` -> `PlantID`)