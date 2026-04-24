## Dimension Table: `BFL.Dim_Division_Sales`
---
**Column Profiles:**

*   `DivisionKey` (int)
*   `DivisionID` (varchar(50))
    *   **All Values:** `00`, `CD`, `HF`, `MM`
*   `DivisionName` (varchar(100))
    *   **All Values:** `Close Die`, `Open Die`, `Ring Rolling`
*   `NewDivision` (varchar(100))
    *   **All Values:** `Aerospace`, `Close Die`, `Defence`, `Open Die`, `Ring Rolling`
*   `DivisionDescription` (varchar(200))
    *   **Values:** *No data found.*

---

**Referenced Dimensions:**
- Dim_Division_ManPower (via `DivisionKey` -> `DivisionKey`)