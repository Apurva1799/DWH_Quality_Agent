## Dimension Table: `BFL.Dim_ProductHierarchy_SalesForce`
---
**Column Profiles:**

*   `ProductHierarchyKey` (int)
*   `ProductHierarchyLevel1` (nvarchar(100))
    *   **All Values:** `Aerospace Products`, `Axle Component`, `Block`, `Chassis Component`, `Engine Component`, `Gear Blank`, `Heavy Engg components`, `Other`, `Plain Shaft`, `Ring`, `Ring Rolling`, `Steering Component`, `Stepped Shaft`, `Transmission Component`, `Under Carriage Component`, `Undercarriage Component`
*   `ProductHierarchyLevel2` (nvarchar(100))
    *   **Mode 5 values (most frequent):** `Gears`, `Construction & Mining Component`, `Shafts`, `Steering Knuckle`, `751 < OD <1250`
*   `ProductHierarchyLevel3` (nvarchar(100))
    *   **Mode 5 values (most frequent):** `Others`, `2001< LENGTH< 4000`, `151<FW<300`, `401<FW<600`, `LENGTH < 2000`
*   `StartDate` (datetime)
    *   **All Values:** `2025-10-28 00:00:00`, `2025-10-31 00:00:00`, `2025-11-07 00:00:00`, `2025-11-24 00:00:00`, `2025-12-03 00:00:00`
*   `EndDate` (datetime)
    *   **All Values:** `9999-12-31 00:00:00`
*   `IsActiveFlag` (bit)
    *   **All Values:** `True`