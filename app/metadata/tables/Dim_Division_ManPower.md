## Dimension Table: `BFL.Dim_Division_ManPower`
---
**Column Profiles:**

*   `DivisionKey` (int)
*   `DivisionID` (int)
*   `Division` (varchar(200))
    *   **Mode 5 values (most frequent):** `MCD-IV`, `MCD-I`, `MCD-II`, `General Engineering`, `Die Shop`
*   `SubDivisionName` (varchar(200))
    *   **Mode 5 values (most frequent):** `ED(O) Office`, `HFD-II QA`, `MCD (Common)`, `MCD Maintenance BRM`, `8000 Ton Press Line`

---

**Referenced Dimensions:**
- Dim_Division_Sales (via `DivisionKey` -> `DivisionKey`)