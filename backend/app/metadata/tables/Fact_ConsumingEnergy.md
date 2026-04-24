## Fact Table: `BFL.Fact_ConsumingEnergy`
---
**Columns:**
- `LineKey` (int)
- `ElectricityInINR` (decimal)
- `OilInINR` (decimal)
- `LPGInINR` (decimal)
- `PNGInINR` (decimal)
- `TotalEnergyInINR` (decimal)
- `DateKey` (int)

---

**Related Dimensions:**
- Dim_Date (join over `DateKey`)
- Dim_Line (join over `LineKey`)