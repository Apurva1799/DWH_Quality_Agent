## Fact Table: `BFL.Fact_RequestForQuotation_SalesForce`
---
**Columns:**
- `RequestForQuotationNumberKey` (int)
- `AccountKey` (int)
- `SectorKey` (int)
- `BusinessUnitKey` (int)
- `LeaderKey` (int)
- `CurrencyKey` (int)
- `RegionKey` (int)
- `WinLossReasonKey` (int)
- `AmountGuesstimate` (decimal)
- `EstimatedRequestForQuotationAmount` (decimal)
- `QuotedRequestForQuotationAmount` (decimal)
- `IsStrategic` (bit)
- `CloseDateKey` (int)
- `CreatedDateKey` (int)
- `RequestForQuotationReceivedDateKey` (int)

---

**Related Dimensions:**
- Dim_Account_SalesForce (join over `AccountKey`)
- Dim_BusinessUnit_ManPower (join over `BusinessUnitKey`) joins with Dim_BusinessUnit_SalesForce (join over `BusinessUnitKey`)
- Dim_BusinessUnit_SalesForce (join over `BusinessUnitKey`) joins with Dim_BusinessUnit_ManPower (join over `BusinessUnitKey`)
- Dim_Currency_SalesForce (join over `CurrencyKey`)
- Dim_Leader_SalesForce (join over `LeaderKey`)
- Dim_Region_SalesForce (join over `RegionKey`)
- Dim_RequestForQuotationDetails_SalesForce (join over `RequestForQuotationNumberKey`)
- Dim_Sector_SalesForce (join over `SectorKey`)
- Dim_WinLoss_SalesForce (join over `WinLossReasonKey`)