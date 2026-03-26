# KQL Query Reference
## azure-sre-platform | Author: Srikanth Gandikota
## KQL = Kusto Query Language — used in Azure Log Analytics

---

## What is KQL and why do SRE teams use it?

KQL is the query language for searching and analysing logs in Azure.
You run KQL queries in Azure Log Analytics, Azure Monitor, and
Application Insights.

**Why SREs need KQL:**
When a P1 incident fires at 2am, you need to search through millions
of log lines in seconds to find the root cause.
KQL lets you filter, aggregate, and visualise that data instantly.

**Where to run these queries:**
1. Go to portal.azure.com
2. Search for "Log Analytics workspaces"
3. Click your workspace
4. Click "Logs" in the left menu
5. Paste any query below and click "Run"

---

## Quick Reference Card

| What you want to do | KQL keyword | Example |
|---------------------|-------------|---------|
| Filter rows | `where` | `where TimeGenerated > ago(1h)` |
| Select columns | `project` | `project Name, Value, Time` |
| Count rows | `count()` | `summarize count()` |
| Average a number | `avg()` | `summarize avg(CPU)` |
| Group by time | `bin()` | `by bin(TimeGenerated, 5m)` |
| Sort results | `order by` | `order by TimeGenerated desc` |
| Limit rows returned | `take` | `take 100` |
| Draw a chart | `render` | `render timechart` |
| Text contains | `contains` | `where Name contains "error"` |
| Count per group | `summarize count() by` | `summarize count() by OperationName` |

---

## Essential SRE Queries

### Query 1 — Find all failures in the last hour
**Use this during incident triage — run this first**
```kusto
AzureActivity
| where TimeGenerated > ago(1h)
| where ActivityStatusValue == "Failure"
| project TimeGenerated, OperationName, Caller, ResourceGroup
| order by TimeGenerated desc
| take 50
```

**What each line does:**
- `AzureActivity` — the table that holds all Azure operations
- `where TimeGenerated > ago(1h)` — only show last 1 hour
- `where ActivityStatusValue == "Failure"` — only show failures
- `project` — choose which columns to show
- `order by TimeGenerated desc` — newest first
- `take 50` — show only 50 rows

---

### Query 2 — CPU usage trend over 24 hours
**Use this to investigate high CPU alerts**
```kusto
AzureMetrics
| where MetricName == "Percentage CPU"
| where TimeGenerated > ago(24h)
| summarize AvgCPU = avg(Average) by bin(TimeGenerated, 5m)
| render timechart
```

**What each line does:**
- `AzureMetrics` — table that holds all Azure metrics
- `where MetricName == "Percentage CPU"` — filter to CPU only
- `summarize AvgCPU = avg(Average) by bin(TimeGenerated, 5m)` — average CPU per 5 minute window
- `render timechart` — draw a line chart automatically

---

### Query 3 — VM availability SLO measurement
**Use this to measure your 99.5% uptime SLO**
```kusto
AzureMetrics
| where MetricName == "VmAvailabilityMetric"
| where TimeGenerated > ago(30d)
| summarize
    TotalMinutes     = count(),
    AvailableMinutes = countif(Average >= 1)
| extend AvailabilityPercent = round(
    (AvailableMinutes * 100.0) / TotalMinutes, 2
  )
| extend ErrorBudgetUsedMin = TotalMinutes - AvailableMinutes
| extend SLOTarget           = 99.5
| extend SLOMet              = AvailabilityPercent >= SLOTarget
| project
    AvailabilityPercent,
    ErrorBudgetUsedMin,
    SLOTarget,
    SLOMet
```

**What this tells you:**
- Your actual availability % over the last 30 days
- How many minutes of error budget you have used
- Whether you are meeting your 99.5% SLO target

---

### Query 4 — Detect CPU anomalies automatically (AIOps)
**This is AI-powered anomaly detection — no threshold needed**
```kusto
AzureMetrics
| where MetricName == "Percentage CPU"
| where TimeGenerated > ago(7d)
| summarize AvgCPU = avg(Average) by bin(TimeGenerated, 1h)
| render anomalychart
```

---

### Query 5 — Find recent deployments
**Use this to correlate incidents with deployments**
```kusto
AzureActivity
| where TimeGenerated > ago(24h)
| where OperationName contains "deployments"
| where ActivityStatusValue == "Success"
| project TimeGenerated, Caller, ResourceGroup, OperationName
| order by TimeGenerated desc
| take 20
```

**SRE tip:**
When an incident starts, always run this query first.
If a deployment happened 5-10 minutes before the incident started
that deployment is almost always the root cause.
This is how I identified root cause in the P1 incident —
I correlated the failure timestamp with the deployment timestamp.

---

### Query 6 — Count errors by type
**Use this to find the most common failure patterns**
```kusto
AzureActivity
| where TimeGenerated > ago(7d)
| where ActivityStatusValue == "Failure"
| summarize FailureCount = count() by OperationName
| order by FailureCount desc
| take 10
```

**What this tells you:**
The top 10 most common failure types in the last 7 days.
Use this in postmortems to prioritise what to fix first.

---

### Query 7 — Disk usage over time
**Use this after a disk-full alert**
```kusto
AzureMetrics
| where MetricName == "OS Disk Used Bytes"
| where TimeGenerated > ago(24h)
| summarize AvgDiskBytes = avg(Average) by bin(TimeGenerated, 1h)
| extend DiskGB = round(AvgDiskBytes / 1073741824, 2)
| project TimeGenerated, DiskGB
| render timechart
```

**What each part does:**
- `1073741824` = number of bytes in 1 GB
- `extend DiskGB` = converts bytes to GB for readability
- Result shows disk usage growing over time so you can predict
  when it will fill completely

---

### Query 8 — Error budget burn rate
**Use this to track how fast you are using your monthly SLO budget**
```kusto
AzureMetrics
| where MetricName == "VmAvailabilityMetric"
| where TimeGenerated > ago(30d)
| summarize MinutesDown = countif(Average < 1) by bin(TimeGenerated, 1d)
| extend MonthlyBudgetMinutes = 216
| extend BudgetRemainingPercent = round(
    (MonthlyBudgetMinutes - MinutesDown) * 100.0 / MonthlyBudgetMinutes,
    1
  )
| project TimeGenerated, MinutesDown, BudgetRemainingPercent
| render timechart
```

**What this tells you:**
How much of your 216-minute monthly error budget remains each day.
If the line is dropping fast early in the month you need to act
before the budget runs out and the SLO is breached.

---
