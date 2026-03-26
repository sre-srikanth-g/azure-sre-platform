# SLI / SLO / Error Budget Definitions
## azure-sre-platform | Author: Srikanth Gandikota

---

## What are SLIs, SLOs, and Error Budgets?

These three concepts are the foundation of Site Reliability Engineering (SRE).
They turn vague goals like "the system should be reliable" into
measurable, actionable targets.

---

### SLI — Service Level Indicator
A **measurement** of how your service is actually performing right now.
Think of it as the speedometer in your car.

| Example SLI | What it measures |
|-------------|-----------------|
| 99.3% of requests succeeded in the last 30 days | Success rate |
| Average response time was 187ms | Performance |
| VM was running 99.7% of minutes this month | Availability |

---

### SLO — Service Level Objective
The **target** you set for your SLI.
Think of it as the speed limit — the line between acceptable and not.

| Example SLO | What it means |
|-------------|--------------|
| 99.5% of requests must succeed per month | Reliability target |
| Response time must be under 500ms for 95% of requests | Performance target |
| VM must be available 99.5% of minutes per month | Uptime target |

---

### Error Budget
How much failure you are **allowed** before breaching your SLO.

**Example calculation:**
- SLO target = 99.5% availability per month
- Month = 30 days × 24 hours × 60 minutes = 43,200 minutes
- Error budget = 0.5% of 43,200 = **216 minutes** of allowed downtime

When the error budget is gone:
- **Stop shipping new features**
- All engineering effort goes to reliability
- Resume normal work only after a postmortem and fixes are in place

---

## SLOs for azure-sre-platform

### SLO 1 — VM Availability

| Field | Value |
|-------|-------|
| **SLI** | % of minutes the VM is in "VM running" state |
| **SLO target** | 99.5% per calendar month |
| **Error budget** | 216 minutes (3.6 hours) downtime allowed |
| **How measured** | Azure Monitor — VmAvailabilityMetric |
| **Check frequency** | Every 1 minute |
| **Alert threshold** | Page on-call if availability drops below 99% |
| **Breach action** | Freeze deployments, investigate root cause |

**KQL query to measure this SLI in Azure Log Analytics:**
```kusto
AzureMetrics
| where MetricName == "VmAvailabilityMetric"
| where TimeGenerated > ago(30d)
| summarize
    TotalMinutes     = count(),
    AvailableMinutes = countif(Average >= 1)
| extend AvailabilityPercent  = round((AvailableMinutes * 100.0) / TotalMinutes, 2)
| extend ErrorBudgetUsedMin   = TotalMinutes - AvailableMinutes
| extend SLOTarget             = 99.5
| extend SLOMet                = AvailabilityPercent >= SLOTarget
| project
    AvailabilityPercent,
    ErrorBudgetUsedMin,
    SLOTarget,
    SLOMet
```

---

### SLO 2 — Health Check Pass Rate

| Field | Value |
|-------|-------|
| **SLI** | % of hourly health checks that return healthy |
| **SLO target** | 99% per calendar month |
| **Error budget** | ~7 failed checks allowed per month |
| **How measured** | health_check.py results via GitHub Actions |
| **Check frequency** | Every 1 hour |
| **Alert threshold** | Create GitHub issue if 2 consecutive checks fail |
| **Breach action** | Run alert_handler.py auto-remediation |

---

### SLO 3 — CI/CD Pipeline Reliability

| Field | Value |
|-------|-------|
| **SLI** | % of CI/CD pipeline runs that succeed |
| **SLO target** | 95% per calendar month |
| **Error budget** | 5% of runs may fail |
| **How measured** | GitHub Actions workflow metrics |
| **Alert threshold** | Investigate if 3 consecutive pipelines fail |

---

## Error Budget Policy

### Budget remaining > 50% — normal operations
- Ship new features at normal pace 
- Continue infrastructure improvements
- Tech debt work allowed

### Budget remaining < 50% — caution zone
- Review all planned deployments for risk 
- Increase monitoring sensitivity
- Consider rolling back recent changes

### Budget exhausted — freeze 
- Stop all new feature deployments immediately
- 100% of engineering effort on reliability
- Mandatory postmortem before resuming normal work
- Root cause must be fixed and verified

---
