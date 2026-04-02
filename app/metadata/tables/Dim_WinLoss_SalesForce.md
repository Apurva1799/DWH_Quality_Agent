## Dimension Table: `BFL.Dim_WinLoss_SalesForce`
---
**Column Profiles:**

*   `WinLossReasonKey` (int)
*   `RFQOutcomeReason` (nvarchar(255))
    *   **Mode 5 values (most frequent):** `Unknown`, `Lost to Competitor`, `Price`, `Lost to Competitor - Price`, `Other`
*   `RequestForQuotationOutcome` (nvarchar(100))
    *   **All Values:** `Budgetory`, `Cancelled`, `Closed Awarded`, `Closed Lost`, `Closed Won`, `Diverted`, `Estimation`, `Needs Analysis`, `Negotiation`, `Proposal`, `Qualification`, `Regretted`, `Regretted tech`
*   `CompetitorName` (nvarchar(100))
    *   **All Values:** `ALKA FORG.`, `BAY FORGE`, `CFFP (BHEL) HARIDWAR`, `CHINA`, `CHW FORGE`, `GOODLUCK FORGE`, `HINDUSTAN FORGE`, `ITALY`, `MACKEIL / ISPAT`, `Other / Chinese Player`, `OTHERS`, `RAJKUMAR FORGE / WESTERN INDIA`, `STARWIRE`, `SUNIL FORGE`, `VIKRANT FORGE / ARCWAC`, `WESTERN INDIA FORG.`
*   `StartDate` (datetime)
    *   **All Values:** `2025-10-28 00:00:00`, `2025-11-07 00:00:00`, `2026-01-13 00:00:00`, `2026-01-15 00:00:00`, `2026-01-21 00:00:00`
*   `EndDate` (datetime)
    *   **All Values:** `9999-12-31 00:00:00`
*   `IsActiveFlag` (bit)
    *   **All Values:** `True`