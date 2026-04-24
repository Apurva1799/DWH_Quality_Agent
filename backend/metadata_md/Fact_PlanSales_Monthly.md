## Fact Table: `BFL.Fact_PlanSales_Monthly`
---
**Columns:**
- `PlantKey` (int)
- `ProductKey` (int)
- `CustomerKey` (int)
- `PlanVersionNumber` (varchar)
- `PlanName` (varchar)
- `PlanDateKey` (int)
- `Year` (int)
- `Month` (int)
- `ProfitCenter` (varchar)
- `PlannedOnDateKey` (int)
- `SalesOrganisationKey` (int)
- `DistributionChannelKey` (int)
- `CurrencyCodeKey` (int)
- `CurrencyFactorToUSD` (decimal)
- `CurrencyFactorToINR` (decimal)
- `DivisionKey` (int)
- `PlannedQuantity` (decimal)
- `Tonnage` (decimal)
- `SellingPrice` (decimal)
- `PlannedSalesAmountUSD` (decimal)
- `PlannedSalesAmountINR` (decimal)
- `BusinessDivisionKey` (int)

---

**Related Dimensions:**
- Dim_BusinessDivision_Sales (join over `BusinessDivisionKey`)
- Dim_CurrencyCode_Sales (join over `CurrencyCodeKey`)
- Dim_Customer_Sales (join over `CustomerKey`)
- Dim_DistributionChannel_Sales (join over `DistributionChannelKey`)
- Dim_Division_ManPower (join over `DivisionKey`) joins with Dim_Division_Sales (join over `DivisionKey`)
- Dim_Division_Sales (join over `DivisionKey`) joins with Dim_Division_ManPower (join over `DivisionKey`)
- Dim_Product_Sales (join over `ProductKey`)
- Dim_SalesOrganisation_Sales (join over `SalesOrganisationKey`)