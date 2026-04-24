## Fact Table: `BFL.Fact_TotalProductiveMaintenance`
---
**Columns:**
- `StrategicBusinessUnitKey` (int)
- `PM ` (decimal)
- `SHE ` (decimal)
- `5S` (decimal)
- `JH ` (decimal)
- `KK ` (decimal)
- `QM ` (decimal)
- `OverallTPMScore` (decimal)
- `ET ` (decimal)
- `DateKey` (int)

---

**Related Dimensions:**
- Dim_Date (join over `DateKey`)
- Dim_StrategicBusinessUnit (join over `StrategicBusinessUnitKey`)