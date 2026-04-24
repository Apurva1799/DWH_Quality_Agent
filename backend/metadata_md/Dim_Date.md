## Dimension Table: `BFL.Dim_Date`
---
**Column Profiles:**

*   `DateKey` (int)
*   `FullDate` (date)
    *   **Mode 5 values (most frequent):** `2022-05-24`, `2021-06-26`, `2020-07-29`, `2019-09-01`, `2018-10-04`
*   `DayOfWeek` (int)
    *   **Range:** 1.0 – 7.0
    *   **Median:** 4.0
*   `DayName` (varchar(10))
    *   **All Values:** `Friday`, `Monday`, `Saturday`, `Sunday`, `Thursday`, `Tuesday`, `Wednesday`
*   `DayOfMonth` (int)
    *   **Range:** 1.0 – 31.0
    *   **Median:** 16.0
*   `DayOfYear` (int)
    *   **Range:** 1.0 – 366.0
    *   **Median:** 183.0
*   `IsWeekend` (bit)
    *   **All Values:** `False`, `True`
*   `WeekOfYear` (int)
    *   **Range:** 1.0 – 53.0
    *   **Median:** 27.0
*   `WeekStartDate` (date)
    *   **Mode 5 values (most frequent):** `2025-03-31`, `2018-11-19`, `2025-11-24`, `2020-07-06`, `2022-03-14`
*   `WeekEndDate` (date)
    *   **Mode 5 values (most frequent):** `2025-01-19`, `2020-09-13`, `2024-01-07`, `2019-09-01`, `2023-05-14`
*   `Month` (int)
    *   **Range:** 1.0 – 12.0
    *   **Median:** 7.0
*   `MonthName` (varchar(10))
    *   **All Values:** `April`, `August`, `December`, `February`, `January`, `July`, `June`, `March`, `May`, `November`, `October`, `September`
*   `MonthYear` (varchar(20))
    *   **Mode 5 values (most frequent):** `Mar 2024`, `Dec 2018`, `Oct 2022`, `Aug 2021`, `May 2022`
*   `IsLastDayOfMonth` (bit)
    *   **All Values:** `False`, `True`
*   `FirstDayOfMonth` (date)
    *   **Mode 5 values (most frequent):** `2021-03-01`, `2022-08-01`, `2017-01-01`, `2025-08-01`, `2026-12-01`
*   `LastDayOfMonth` (date)
    *   **Mode 5 values (most frequent):** `2021-01-31`, `2025-03-31`, `2022-12-31`, `2026-08-31`, `2020-12-31`
*   `Quarter` (int)
    *   **Range:** 1.0 – 4.0
    *   **Median:** 3.0
*   `QuarterName` (varchar(5))
    *   **All Values:** `Q1`, `Q2`, `Q3`, `Q4`
*   `IsFirstDayOfQuarter` (bit)
    *   **All Values:** `False`, `True`
*   `IsLastDayOfQuarter` (bit)
    *   **All Values:** `False`, `True`
*   `Year` (int)
    *   **Range:** 2017.0 – 2026.0
    *   **Median:** 2021.5
*   `IsLeapYear` (bit)
    *   **All Values:** `False`, `True`
*   `IsLastDayOfYear` (bit)
    *   **All Values:** `False`, `True`
*   `FirstDayOfYear` (date)
    *   **All Values:** `2017-01-01`, `2018-01-01`, `2019-01-01`, `2020-01-01`, `2021-01-01`, `2022-01-01`, `2023-01-01`, `2024-01-01`, `2025-01-01`, `2026-01-01`
*   `LastDayOfYear` (date)
    *   **All Values:** `2017-12-31`, `2018-12-31`, `2019-12-31`, `2020-12-31`, `2021-12-31`, `2022-12-31`, `2023-12-31`, `2024-12-31`, `2025-12-31`, `2026-12-31`
*   `FiscalYear` (int)
    *   **Range:** 2017.0 – 2027.0
    *   **Median:** 2022.0
*   `FiscalQuarter` (int)
    *   **Range:** 1.0 – 4.0
    *   **Median:** 2.0
*   `FiscalMonth` (int)
    *   **Range:** 1.0 – 12.0
    *   **Median:** 6.0
*   `FiscalMonthName` (varchar(10))
    *   **All Values:** `April`, `August`, `December`, `February`, `January`, `July`, `June`, `March`, `May`, `November`, `October`, `September`
*   `FiscalYearMonth` (varchar(20))
    *   **Mode 5 values (most frequent):** `FY2018-Mar`, `FY2026-May`, `FY2020-Jan`, `FY2025-Jul`, `FY2026-Aug`
*   `IsFirstDayOfFiscalYear` (bit)
    *   **All Values:** `False`, `True`
*   `IsLastDayOfFiscalYear` (bit)
    *   **All Values:** `False`, `True`
*   `IsFirstDayOfFiscalMonth` (bit)
    *   **All Values:** `False`, `True`
*   `IsLastDayOfFiscalMonth` (bit)
    *   **All Values:** `False`, `True`
*   `WeekdayIndexInMonth` (int)
    *   **Range:** 1.0 – 6.0
    *   **Median:** 3.0
*   `WeekendIndexInMonth` (int)
    *   **Range:** 0.0 – 6.0
    *   **Median:** 0.0
*   `Season` (varchar(10))
    *   **All Values:** `Autumn`, `Spring`, `Summer`, `Winter`
*   `JulianDate` (int)
    *   **Range:** 1.0 – 366.0
    *   **Median:** 183.0