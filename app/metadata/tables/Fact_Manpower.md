## Fact Table: `BFL.Fact_Manpower`
---
**Columns:**
- `EmployeeKey` (int)
- `CompanyLegalEntityID` (int)
- `CompanyName` (varchar)
- `BusinessUnitKey` (int)
- `DivisionKey` (int)
- `CostCenterKey` (int)
- `LocationKey` (int)
- `JoiningDateKey` (int)
- `LastWorkingDateKey` (int)
- `PositionKey` (int)
- `GradeKey` (int)
- `VendorKey` (int)

---

**Related Dimensions:**
- Dim_BusinessUnit_ManPower (join over `BusinessUnitKey`) joins with Dim_BusinessUnit_SalesForce (join over `BusinessUnitKey`)
- Dim_BusinessUnit_SalesForce (join over `BusinessUnitKey`) joins with Dim_BusinessUnit_ManPower (join over `BusinessUnitKey`)
- Dim_CostCenter_manpower (join over `CostCenterKey`)
- Dim_Division_ManPower (join over `DivisionKey`) joins with Dim_Division_Sales (join over `DivisionKey`)
- Dim_Division_Sales (join over `DivisionKey`) joins with Dim_Division_ManPower (join over `DivisionKey`)
- Dim_Employee_ManPower (join over `EmployeeKey`)
- Dim_Grade_ManPower (join over `GradeKey`)
- Dim_Location_ManPower (join over `LocationKey`)
- Dim_Position_ManPower (join over `PositionKey`)
- Dim_Vendor_ManPower (join over `VendorKey`)