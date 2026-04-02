## Fact Table: `BFL.Fact_ForgingScrap`
---
**Columns:**
- `DieKey` (int)
- `LineKey` (int)
- `ScrapedDateKey` (int)
- `ForgingScrapQuantity` (float)
- `ForgingScrapInTons` (float)

---

**Related Dimensions:**
- Dim_Date (join over `ScrapedDateKey -> DateKey`)
- Dim_Die (join over `DieKey`)
- Dim_Line (join over `LineKey`)