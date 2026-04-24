## Flat Table: `BFL.FT_AssetMonitoring`
---
This is a self-contained table.
**Column Profiles:**

*   `CompanyCode` (varchar(10))
    *   **All Values:** `BFIL`, `BFIN`, `BFIS`, `BFIT`, `BFL`
*   `AssetID` (varchar(50))
    *   **Mode 5 values (most frequent):** `000027000046`, `000086000002`, `000027000049`, `000027000105`, `000027000027`
*   `AssetDescription` (nvarchar(200))
    *   **Mode 5 values (most frequent):** `Trim Support plate D Set No 010`, `R Roll Low IInd pass Set No 010`, `R Roll Low Ist pass  Set No 010`, `R Roll Upp IInd pass Set No 010`, `R Roll Upp Ist pass  Set No 010`
*   `AssetClass` (nvarchar(50))
    *   **Mode 5 values (most frequent):** `52000`, `52001`, `10403`, `30109`, `30104`
*   `AssetClassDescription` (nvarchar(200))
    *   **Mode 5 values (most frequent):** `FA - Fabricated Die Stock`, `WIP - Fabricated Die Stock`, `Plant & Machinery Tripple Shift`, `Asset Under Construction - Others`, `Asset Under Construction - Plant & Machinery`
*   `Availability` (varchar(20))
    *   **All Values:** `Available`, `Deactivated`
*   `CapitalizationDate` (varchar(10))
    *   **Mode 5 values (most frequent):** `2019-10-31`, `N/A`, `2018-03-31`, `2018-06-30`, `2018-11-30`
*   `DeactivationDate` (varchar(10))
    *   **Mode 5 values (most frequent):** `N/A`, `2020-11-28`, `2019-10-31`, `2020-08-17`, `2024-08-31`
*   `PlantID` (nvarchar(50))
    *   **All Values:** ``, `1000`, `5100`, `6100`, `6200`, `6500`, `7100`, `7200`, `7205`, `7300`, `7310`, `7500`, `8200`, `8201`, `8202`, `9501`, `9502`, `9504`, `9506`
*   `PlantName` (nvarchar(200))
    *   **All Values:** `BFITSL Plant- Waghodia`, `BHARAT FORGE INTERNATIONAL LTD`, `Branch Office - Banglore`, `Branch Office - Chennai`, `Branch Office - Delhi`, `Branch Office- Mumbai`, `Close Die Forge - BFL Baramati`, `Close Die Forge - BFL Mundhwa`, `CLWT-CASTING`, `CLWT-MACHINING`, `General Engg.Division`, `Heavy Forge Plant- Mundhwa`, `ISD BFL Mundhwa`, `KCMI-Bharat Forge Limited`, `Machining Division - Chakan`, `Machining Plant - Baramati`, `Machining Plant - BFIN`, `Machining Plant - Mundhwa`, `N/A`
*   `Location` (nvarchar(100))
    *   **Mode 5 values (most frequent):** `N/A`, `4001`, `2001`, `2002`, `BFUNIT2`
*   `CostCenter` (nvarchar(50))
    *   **Mode 5 values (most frequent):** `0000110999`, `0000107200`, `0000510500`, `0000523201`, `0200100001`
*   `CreatedOn` (datetime)
    *   **All Values:** `2025-11-11 16:48:57.977000`
*   `BusinessArea` (varchar(50))
    *   **All Values:** `1201`, `BARM`, `BFIN`, `BFIT`, `BRAN`, `CHAK`, `CLWT`, `KCMI`, `MNWA`, `SATA`, `WIND`
*   `AssetProcurementCost` (decimal)
    *   **Range:** 0.00 – 1634245649.26
    *   **Median:** 129134.9
*   `DepreciationValue` (decimal)
    *   **Range:** 0.00 – 817787627.89
    *   **Median:** 71140.82
*   `NetBookValue` (decimal)
    *   **Range:** 0.00 – 1403322649.77
    *   **Median:** 0.0
*   `Currency` (varchar(10))
    *   **All Values:** `INR`, `USD`
*   `Quantity` (decimal)
    *   **Range:** 0.000 – 2500001.000
    *   **Median:** 2.0
*   `UnitOfMeasure` (varchar(10))
    *   **All Values:** ``, `EA`, `NOS`, `PC`, `SET`