## Dimension Table: `BFL.Dim_MaterialGold`
---
**Column Profiles:**

*   `MaterialKey` (int)
*   `MaterialNumber` (nvarchar(50))
    *   **Mode 5 values (most frequent):** `000000104104003972`, `000000112503028592`, `000000204104002882`, `000000304104042334`, `000000304108041280`
*   `MaterialNumberDescription` (nvarchar(200))
    *   **Mode 5 values (most frequent):** `INSPECTION`, `FORGING`, `NORMALISE`, `ITEM DELETED NOT TO BE USED`, `P/M SHAFT`
*   `MaterialType` (nvarchar(20))
    *   **All Values:** `NLAG`, `VKHM`, `ZBAU`, `ZCAP`, `ZDIB`, `ZDIE`, `ZFIN`, `ZNSK`, `ZOPM`, `ZOPS`, `ZPKG`, `ZPRT`, `ZRAW`, `ZRFS`, `ZSCR`, `ZSEM`, `ZSER`, `ZSPR`, `ZTDS`, `ZTRD`, `ZUNB`
*   `MaterialTypeDescription` (nvarchar(200))
    *   **All Values:** `Additionals`, `Capital Goods`, `Customer Supplied Matl.`, `Die Blocks Ready to Sink`, `Die Tool Steel-BFL`, `Dies - Finished`, `Finished products-BFL`, `Maintenance assemblies`, `Non-Stock Materials`, `Operating supplies - BFL`, `OPS-mfg`, `Packaging-BFL`, `Prod. resources/tools`, `Raw materials-BFL`, `Rejected Forging Scrap`, `Scrap Material-BFL`, `Semifinished products-BFL`, `Services -BFL`, `Spare parts-BFL`, `Trading goods-BFL`
*   `ValuationClass` (nvarchar(20))
    *   **Mode 5 values (most frequent):** `3300`, `7900`, `3311`, `7920`, `8800`
*   `ValuationClassDescription` (nvarchar(200))
    *   **Mode 5 values (most frequent):** `Nonvaluated material`, `Semifinished products`, `Stores Non Stock Repairs`, `Finished products`, `Die Blocks -Ready to Sink`
*   `MaterialGroup` (nvarchar(20))
    *   **Mode 5 values (most frequent):** `FOR`, `12503`, `HFD`, `OTH`, `09303`
*   `MaterialGroupDescription` (nvarchar(200))
    *   **Mode 5 values (most frequent):** `FORGING`, `MACHINING ITEM`, `HEAVY FORGE`, `OTHER MCD M/C SPARES`, `GRINDING MACHINE SPA`
*   `StartDate` (datetime2)
    *   **All Values:** `2025-10-12 07:59:31.812000`, `2025-11-18 04:55:14.914000`
*   `EndDate` (datetime2)
    *   **Values:** *No data found.*
*   `IsActiveFlag` (bit)
    *   **All Values:** `True`

---

**Referenced Dimensions:**
- Dim_Material (via `MaterialKey` -> `MaterialKey`)