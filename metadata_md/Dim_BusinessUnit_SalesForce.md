## Dimension Table: `BFL.Dim_BusinessUnit_SalesForce`
---
**Column Profiles:**

*   `BusinessUnitKey` (int)
*   `BusinessUnit` (nvarchar(100))
    *   **All Values:** `Aerospace`, `Component`, `Defence`, `Industrial`, `IT`
*   `StartDate` (datetime)
    *   **All Values:** `2025-12-25 16:30:00.760000`
*   `EndDate` (datetime)
    *   **All Values:** `9999-12-31 00:00:00`
*   `IsActiveFlag` (bit)
    *   **All Values:** `True`

---

**Referenced Dimensions:**
- Dim_BusinessUnit_ManPower (via `BusinessUnitKey` -> `BusinessUnitKey`)