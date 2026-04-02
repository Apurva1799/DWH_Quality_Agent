# BFL Facts 

---

## 1. `Fact_Forging_DieLevel_PeriodicSnapshot`

**Grain:** Periodic snapshot at **shift × die** level after removing scrap (shippable pieces only).

---

## 2. `Fact_Forging_DieSpareLevel_AccumulatingSnapshot`

**Grain:** Accumulating snapshot at **die-spare × run** level from start date to end date (includes bad pieces).

---

## 3. `Fact_DowntimeWithReasons`

**Grain:** One row per **breakdown reason × line × shift**.

---

## 4. `Fact_ForgingScrap`

**Grain:** Daily scrap snapshot at **line × die × date** level.

---

## 5. `Fact_Machining`

**Grain:** Periodic snapshot at **shift × line × die × day** level.

---

## 6. `Fact_MachiningScrap`

**Grain:** Daily machining scrap snapshot at **line × die × date** level.

---

## 7. `Fact_MachiningPlan_Monthly`

**Grain:** Planned machining at **die × line × day × plan version** level.

---

## 8. `Fact_ForgingPlan_Monthly`

**Grain:** Monthly forging plan at **die × line × month × plan version** level.

---

## 9. `Fact_ForgingPlan_Daily`

**Grain:** Daily forging plan at **line × die × day** level.

---

## 10. `Fact_TotalProductiveMaintenance`

**Grain:** Monthly snapshot at **Strategic Business Unit (SBU) × month** level.

---

## 11. `Fact_ConsumingEnergy`

**Grain:** Daily energy consumption at **line × date** level.

---

## 12. `Fact_OEE`

**Grain:** Daily OEE calculation at **line × date** level.

---

## 13. `Fact_Inventory_Monthly`

**Grain:** Monthly inventory snapshot at **material × die × storage location × plant × date** level.

---

## 14. `Fact_RequestForQuotation_SalesForce`

**Grain:** One row per **RFQ document × customer account**.

---

## 15. `Fact_PartRequestForQuotation_SalesForce`

**Grain:** One row per **part × RFQ document**.

---

## 16. `Fact_ActualSales`

**Grain:** One row per **product × customer × invoice × plant × date**.

---

## 17. `Fact_PlanSales_Monthly`

**Grain:** One row per **product × customer × plant × plan month × plan version**.

---

## 18. `Fact_AssetMonitoring`

**Grain:** One row per **asset × plant/location × snapshot date**.

---

## 19. `Fact_Manpower`

**Grain:** One row per **employee × company × organization assignment × snapshot date**.

---

## 20. `Fact_BOM`

**Grain:** One active BOM component line for one parent material × one component material × one plant × one storage location × one BOM version (number + alternative) × one BOM item node × one item number × one validity period (valid-from to valid-to), including material and component quantities with their respective units of measure.

---

## 21. `Fact_MaintenanceActivity`

**Grain:** One record per maintenance activity execution at date × equipment × personnel × task × plan × status level, capturing planned vs actual time, manpower, completion, breakdown, and machine-down indicators.
---

## 22. `Fact_Procurement`

**Grain:** One record per purchase order line item at purchase order × item × material × vendor × plant × company level, tracking the full procurement lifecycle from PR to PO to GR to Invoice, including quantities, cycle times, and spend values.

---