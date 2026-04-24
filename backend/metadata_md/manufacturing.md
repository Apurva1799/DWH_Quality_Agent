# Schema: manufacturing
 
## Table: fact_BasicContribution
 
- **Column(CAREFUL DATEID IS AN INT COLUMN)**: DateID
  - **Example  Values**: 20240305, 20240313
 
- **Column**: LineSBU
  - **Example Values**: COLD FORGE, FMD1, FMD2, FMD3, FMD4, Hammer Baramati, Hammer Mundhwa, MCD B, MCD Chakan, MCD Indapur, MCD1, MCD2
 
- **Column**: LineID
  - **Example  Values**: 59, 168
 
- **Column**: BasicContribution
  - **Example  Values**: 0.000000, 1.077349
 
## Table: fact_DowntimeLossReasons
 
- **Column**: LineID
  - **Example  Values**: 5, 1

- **Column**: ShiftID
  - **Example Values**: 01, 02, 03
 
- **Column**: DowntimeCategory
  - **Example Values**: PLANNED, UNPLANNED
 
- **Column**: DowntimeInHours
  - **Example  Values**: 0.500000, 0.166666
 
- **Column**: Description
  - **Example  Values**: PLANNED SHUTDOWN, QUALITY CHECKING, Planned Shutdown, LUNCH / DINNER BREAK, SETUP ACTUAL
 
- **Column(CAREFUL DATEID IS AN INT COLUMN)**: DateID
  - **Example  Values**: 20180606, 20180524, 20180514
 
 
## Table: fact_Production
 
- **Column**: ShiftID
  - **Example Values**: 01, 02, 03, 04, 09
- **Column(CAREFUL DATEID IS AN INT COLUMN)**: DateID
  - **Example  Values**: 20190207, 20190306
 
- **Column**: LineID
  - **Example  Values**: 149, 122
 
- **Column**: DieNo
  - **Example  Values**: 04134, 08027
 
- **Column**: MaterialCode
  - **Example  Values**: WMFIN08027, WMFIN04181, WMFIN04134
 
- **Column**: ProductionQuantity
  - **Example  Values**: 0.000, 40.000, 50.000
 
- **Column**: ProductionTon
  - **Example  Values**: 0.25920000000, 8.47200000000
 
- **Column**: MachiningContribution
  - **Example  Values**: 0.000000, 0.038000
 
## Table: dim_PlannedCycleTime
 
- **Column**: LineID
  - **Example  Values**: 1, 5, 11, 12, 2
 
- **Column**: DieNo
  - **Example  Values**: 09015, 03587
 
- **Column**: MaterialCode
  - **Example  Values**: WFFOR03587, WFFOR02650, WFFOR03222
 
  - **Column**: PlannedCycleTimeInSec
  - **Example  Values**: 40, 45
 
## Table: fact_UptimeHoursPlanned
 
- **Column(CAREFUL DATEID IS AN INT COLUMN)**: DateID
  - **Example  Values**: 20230703, 20230614
 
- **Column**: LineID
  - **Example  Values**: 1, 18, 5
 
- **Column**: ShiftID
  - **Example Values**: 01, 02, 03
 
- **Column**: UptimeHoursPlanned
  - **Example  Values**: 0.000000, 5.000000, 6.000000
 
## Table: fact_IdleTime
 
- **Column**: ID
  - **Example  Values**: 1, 2, 3
 
- **Column**: WeekNumber
  - **Example  Values**: 1, 3, 4, 2
 
- **Column**: YearNumber
  - **Example Values**: 2024, 2025
 
- **Column**: LineID
  - **Example Values**: 1, 10, 11, 12, 13
 
- **Column**: IdleTime
  - **Example  Values**: 100.000, 31.200, 38.600
 
- **Column**: Utilization
  - **Example  Values**: 0.000, 0.011

## Table: dim_line
 
- **Column**: LineID
- **Example  Values**: FPSH4560, FLKM4000

- **Column**: AlternateLineName
- **Example  Values**: EUMUCO 5000, KURIMOTO, PZS-1, PZS-2, MAXI 2500

- **Column**: LineSBU
- **Example  Values**: COLD FORGE, FMD1, FMD2, FMD3, FMD4, Hammer Baramati, Hammer Mundhwa, MCD B, MCD Chakan, MCD Indapur, MCD1, MCD2

- **Column**: AlternateLineName
- **Example  Values**: EUMUCO 5000, KURIMOTO, PZS-1, PZS-2, MAXI 2500

 
## Table: fact_EnergyINR
 
- **Column(CAREFUL DATEID IS AN INT COLUMN)**: DateID
  - **Example  Values**: 20241212, 20241231

  - **Column**: LineID
  - **Example  Values**: None, 13, 12

- **Column**: EnergyINR
  - **Example  Values**: 0.00000, 5950.00000, 2439.50000
 
## Table: dim_Sbu
 
- **Column**: SbuID
  - **Example Values**: 1, 10, 11

- **Column**: SbuName
  - **Example Values**: COLD FORGE, FMD1, FMD2, FMD3, FMD4, Hammer Baramati, Hammer Mundhwa, MCD Indapur, MCD1, MCD2, MCD3, MCD4

- **Column**: SbuPlantName
  - **Example Values**: Baramati, Chakan, Indapur, Mundhwa
 
 