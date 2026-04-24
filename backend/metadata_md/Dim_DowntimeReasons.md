## Dimension Table: `BFL.Dim_DowntimeReasons`
---
**Column Profiles:**

*   `DowntimeDescriptionKey` (int)
*   `DowntimeDescriptionID` (int)
*   `DowntimeDescription` (nvarchar)
    *   **Mode 5 values (most frequent):** ` FMD-3 CMM BREAKDOWN`, ` DRAG CHAIN DAMAGED`, ` CONVEYOR NOT WORKING`, ` COMMON CASSETTE`, ` BOT SIDE WADGE HYD.NOT WORKING.`
*   `DowntimeDescriptionCategory` (nvarchar)
    *   **All Values:** `DEFECT LOSS`, `Die / Jig / Tool Loss`, `ELECTRICAL`, `ELECTRONICS`, `Energy Loss`, `EQUIPMENT FAILURE LOSS`, `HYDRAULIC`, `LINE ORGANIZATION LOSS`, `LOGISTIC LOSS`, `MANAGEMENT LOSS`, `MEASURE & ADJUSTMENT LOSS`, `MECHANICAL`, `MINOR STOPPAGES`, `MOTION LOSS`, `OTHERS`, `Planned Loss`, `SET UP & ADJUSTMENT LOSS`, `SHUTDOWN LOSS`, `SPEED LOSS`, `START UP LOSS`, `TOOL CHANGE LOSS`
*   `DowntimeDescriptionCode` (nvarchar)
    *   **Mode 5 values (most frequent):** ``, `M`, `E`, `H`, `07`