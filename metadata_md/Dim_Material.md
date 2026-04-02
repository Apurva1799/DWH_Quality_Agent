## Dimension Table: `BFL.Dim_Material`
---
**Column Profiles:**

*   `MaterialKey` (int)
*   `MaterialNumber` (nvarchar(50))
    *   **Mode 5 values (most frequent):** `000000506901001154`, `BORINGDIE`, `C010190023510420`, `BLOCK`, `000000309308001023`
*   `MaterialNumberDescription` (nvarchar(200))
    *   **Mode 5 values (most frequent):** `INSPECTION`, `FORGING`, `NORMALISE`, `ITEM DELETED NOT TO BE USED`, `P/M SHAFT`
*   `MaterialType` (nvarchar(10))
    *   **All Values:** `NLAG`, `VKHM`, `ZBAU`, `ZCAP`, `ZDIB`, `ZDIE`, `ZFIN`, `ZNSK`, `ZOPM`, `ZOPS`, `ZPKG`, `ZPRT`, `ZRAW`, `ZRFS`, `ZSCR`, `ZSEM`, `ZSER`, `ZSPR`, `ZTDS`, `ZTRD`, `ZUNB`
*   `MaterialTypeDescription` (nvarchar(200))
    *   **All Values:** `Additionals`, `Capital Goods`, `Customer Supplied Matl.`, `Die Blocks Ready to Sink`, `Die Tool Steel-BFL`, `Dies - Finished`, `Finished products-BFL`, `Maintenance assemblies`, `Non-Stock Materials`, `Operating supplies - BFL`, `OPS-mfg`, `Packaging-BFL`, `Prod. resources/tools`, `Raw materials-BFL`, `Rejected Forging Scrap`, `Scrap Material-BFL`, `Semifinished products-BFL`, `Services -BFL`, `Spare parts-BFL`, `Trading goods-BFL`
*   `ValuationClass` (nvarchar(4))
    *   **Mode 5 values (most frequent):** `3300`, `7900`, `3311`, `7920`, `8800`
*   `ValuationClassDescription` (nvarchar(200))
    *   **Mode 5 values (most frequent):** `Nonvaluated material`, `Semifinished products`, `Stores Non Stock Repairs`, `Finished products`, `Die Blocks -Ready to Sink`
*   `MaterialGroup` (nvarchar(20))
    *   **Mode 5 values (most frequent):** `FOR`, `12503`, `HFD`, `OTH`, `09303`
*   `MaterialGroupDescription` (nvarchar(200))
    *   **Mode 5 values (most frequent):** `FORGING`, `MACHINING ITEM`, `HEAVY FORGE`, `OTHER MCD M/C SPARES`, `GRINDING MACHINE SPA`
*   `StartDate` (datetime2)
    *   **Mode 5 values (most frequent):** `2025-10-12 07:59:31.812000`, `2025-11-18 04:55:14.914000`, `2025-12-04 22:38:38.682000`, `2025-12-02 04:26:41.926000`, `2026-01-01 22:44:33.380000`
*   `EndDate` (datetime2)
    *   **Values:** *No data found.*
*   `IsActiveFlag` (bit)
    *   **All Values:** `True`