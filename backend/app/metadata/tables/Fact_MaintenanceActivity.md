## Fact Table: `BFL.Fact_MaintenanceActivity`
---
**Columns:**
- `Fact_ID` (bigint)
- `DateKey` (date)
- `EquipmentKey` (varchar)
- `PersonnelKey` (varchar)
- `PlanKey` (varchar)
- `ClassificationKey` (varchar)
- `TaskKey` (varchar)
- `StatusKey` (varchar)
- `PlanTimeHours` (decimal)
- `ActualTimeHours` (decimal)
- `ManHours` (decimal)
- `UnitWork` (varchar)
- `UnitDuration` (varchar)
- `PersonCount` (int)
- `FrequencyWeeks` (decimal)
- `OverdueDays` (int)
- `IsOverdue` (int)
- `IsBreakdown` (bit)
- `IsMachineDown` (bit)
- `IsCompleted` (bit)
- `ETLLoadDate` (datetime)

---

**Related Dimensions:**
- Dim_ClassificationMaintenance (join over `ClassificationKey`)
- Dim_EquipmentMaintenance (join over `EquipmentKey`) joins with Dim_Plant (join over `PlantID`)
- Dim_PersonnelMaintenance (join over `PersonnelKey`)
- Dim_PlanMaintenance (join over `PlanKey`)
- Dim_StatusMaintenance (join over `StatusKey`)
- Dim_TaskDetailMaintenance (join over `TaskKey`)