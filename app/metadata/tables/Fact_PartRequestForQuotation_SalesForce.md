## Fact Table: `BFL.Fact_PartRequestForQuotation_SalesForce`
---
**Columns:**
- `RequestForQuotationNumberKey` (int)
- `PartKey` (int)
- `ProductHierarchyKey` (int)
- `RawMaterialCost` (decimal)
- `VolumnAnnum` (decimal)
- `UnitPrice` (decimal)
- `EstimatedPerPartPrice` (decimal)
- `EstimatedAmount` (decimal)
- `PartAmountGuesstimate` (decimal)
- `QuotedPerPartPrice` (decimal)
- `QuotedAmount` (decimal)
- `CreatedDateKey` (int)

---

**Related Dimensions:**
- Dim_PartName_SalesForce (join over `PartKey`)
- Dim_ProductHierarchy_SalesForce (join over `ProductHierarchyKey`)
- Dim_RequestForQuotationDetails_SalesForce (join over `RequestForQuotationNumberKey`)