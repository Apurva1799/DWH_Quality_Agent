## Fact Table: `BFL.Fact_MachiningScrap`
---
**Columns:**
- `DieKey` (int)
- `LineKey` (int)
- `ScrapedDateKey` (int)
- `MachiningScrapQuantity` (float)
- `MachiningScrapInTons` (float)

---

**Related Dimensions:**
- Dim_Date (join over `ScrapedDateKey -> DateKey`)
- Dim_Die (join over `DieKey`)
- Dim_Line (join over `LineKey`)