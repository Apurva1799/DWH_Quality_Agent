## Dimension Table: `BFL.Dim_BusinessUnit_ManPower`
---
**Column Profiles:**

*   `BusinessUnitKey` (int)
*   `BusinessUnitID` (int)
*   `BusinessUnit` (varchar(200))
    *   **All Values:** `Aerospace Business`, `CLWT`, `Component Business`, `Defense Business`, `Enterprise Function`, `Industrial Business`, `KCTI & KCMI ( Engineering )`, `Light Weighting Technology Bus`, `Technology`

---

**Referenced Dimensions:**
- Dim_BusinessUnit_SalesForce (via `BusinessUnitKey` -> `BusinessUnitKey`)