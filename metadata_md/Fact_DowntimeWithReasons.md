## Fact Table: `BFL.Fact_DowntimeWithReasons`
---
**Columns:**
- `LineKey` (int)
- `ShiftKey` (int)
- `DowntimeCategoryKey` (int)
- `DowntimeDescriptionKey` (int)
- `DowntimeInHours` (decimal)
- `DateKey` (int)

---

**Related Dimensions:**
- Dim_Date (join over `DateKey`)
- Dim_DowntimeCategory (join over `DowntimeCategoryKey`)
- Dim_DowntimeCategory (join over `DowntimeCategoryKey`)
- Dim_DowntimeReasons (join over `DowntimeDescriptionKey`)
- Dim_Line (join over `LineKey`)
- Dim_Shift (join over `ShiftKey`)