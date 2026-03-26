# Incident Response Runbook
## azure-sre-platform | Author: Srikanth Gandikota
## Last Updated: March 2026

---

## Purpose

This runbook defines the step-by-step process for responding to
production incidents on the azure-sre-platform.

Every on-call engineer must follow this process to ensure:
- Consistent and fast incident response
- Clear communication to stakeholders
- Proper documentation for postmortems
- Continuous improvement after every incident

**Core SRE principle:**
The goal is not just to fix the immediate problem.
It is to fix it fast, communicate clearly, and make
sure it never happens the same way again.

---

## Severity Levels

| Level | Name | Description | Response Time | Example |
|-------|------|-------------|---------------|---------|
| P1 | Critical | Full outage — all users affected | 15 minutes | VM down, no access |
| P2 | High | Partial outage — some users affected | 30 minutes | CPU 100%, slow responses |
| P3 | Medium | Degraded performance — workaround exists | 2 hours | Disk 85%, non-urgent |
| P4 | Low | No user impact — informational | Next business day | Log warning |

---

## P1 / P2 Response — Step by Step

### Step 1 — Acknowledge (within 15 minutes for P1)

1. Acknowledge the alert in Azure Monitor or PagerDuty
2. Post in the incident channel immediately:
```
INCIDENT DECLARED — P1
Time declared : [timestamp UTC]
Incident Commander : [your name]
Symptom : [what the alert says]
Status : Investigating
Next update : [time — 15 minutes from now]
```

3. You are now the **Incident Commander**
   You own all communication until the incident is resolved

---

### Step 2 — Triage (first 5 minutes)

Run the automated health check first — gives you a quick overview:
```bash
python3 scripts/health_check.py
```

Check VM status directly via Azure CLI:
```bash
az vm get-instance-view \
  --resource-group sre-demo-dev-rg \
  --name sre-demo-dev-vm \
  --query "instanceView.statuses[*].displayStatus" \
  --output table
```

Check what changed recently — was there a deployment?
```bash
az deployment group list \
  --resource-group sre-demo-dev-rg \
  --query "[?properties.timestamp > '2026-01-01'].{name:name, time:properties.timestamp}" \
  --output table
```

Check Azure Monitor for recent alerts:
```bash
az monitor activity-log list \
  --resource-group sre-demo-dev-rg \
  --start-time $(date -d '2 hours ago' -u +%Y-%m-%dT%H:%M:%SZ) \
  --output table
```

---

### Step 3 — Diagnose and Fix

**If VM is stopped or unavailable:**
```bash
# Try automated restart first
python3 scripts/alert_handler.py \
  --action restart-vm \
  --rg sre-demo-dev-rg \
  --vm sre-demo-dev-vm
```

**If disk is full (over 85%):**
```bash
# Run automated disk cleanup
python3 scripts/alert_handler.py \
  --action disk-cleanup \
  --rg sre-demo-dev-rg \
  --vm sre-demo-dev-vm
```

**If CPU is high — investigate what process is causing it:**
```bash
# Run a command on the VM without SSH using Azure Run Command
az vm run-command invoke \
  --resource-group sre-demo-dev-rg \
  --name sre-demo-dev-vm \
  --command-id RunShellScript \
  --scripts "ps aux --sort=-%cpu | head -10"
```

**Use KQL in Azure Log Analytics to find errors:**
```kusto
-- Find all failures in the last 2 hours
AzureActivity
| where TimeGenerated > ago(2h)
| where ActivityStatusValue == "Failure"
| project TimeGenerated, OperationName, Caller, ResourceGroup
| order by TimeGenerated desc
| take 50
```
```kusto
-- Correlate deployment timing with error spikes
AzureActivity
| where TimeGenerated > ago(6h)
| where OperationName contains "deployments"
| project TimeGenerated, OperationName, ActivityStatusValue, Caller
| order by TimeGenerated desc
```

---

### Step 4 — Communicate (every 15 minutes during P1)

Post an update every 15 minutes — even if nothing has changed:
```
INCIDENT UPDATE — P1
Time : [timestamp UTC]
Status : [Investigating / Mitigating / Resolved]
Finding : [what you found so far]
Action taken : [what you did]
Service impact : [who is affected and how]
Next update : [15 minutes from now]
```

**Golden rule: communicate more than you think you need to.**
Stakeholders would rather have too many updates than silence.
Never go quiet for more than 15 minutes during a P1.

---

### Step 5 — Resolve

Once the issue is fixed:

1. Confirm recovery with health check:
```bash
python3 scripts/health_check.py
```

2. Verify metrics have recovered in Azure Monitor

3. Post resolution message:
```
INCIDENT RESOLVED — P1
Time resolved : [timestamp UTC]
Total duration : [X minutes]
Root cause : [one sentence summary]
Users affected : [description]
Full postmortem : [due within 24 hours]
```

4. Schedule postmortem within 24 hours — non-negotiable

---

## Postmortem Template

Every P1 and P2 requires a postmortem.
The goal is **learning and improvement** — never blame.
```markdown
# Incident Postmortem — [Date]
**Severity:** P1 / P2
**Duration:** X minutes
**Incident Commander:** Srikanth Gandikota

## Summary
[2-3 sentence summary of what happened and the business impact]

## Timeline (all times in UTC)
| Time  | Event |
|-------|-------|
| HH:MM | Alert fired |
| HH:MM | On-call acknowledged |
| HH:MM | Triage started |
| HH:MM | Root cause identified |
| HH:MM | Fix applied |
| HH:MM | Service restored |
| HH:MM | Incident closed |

## Root Cause
[Detailed explanation of WHY this happened]

## Impact
- Duration: X minutes
- Users affected: [describe]
- SLO impact: X minutes of 216 minute monthly error budget consumed

## What Went Well
- [List things that worked — detection, response time, communication]

## What Went Poorly
- [List things that did not work — alert too slow, runbook missing, etc]

## Action Items
| Action | Owner | Due Date | Status |
|--------|-------|----------|--------|
| [Fix the root cause] | [Name] | [Date] | Open |
| [Add missing alert] | [Name] | [Date] | Open |
| [Update this runbook] | [Name] | [Date] | Open |
```

---

## Escalation Path

| When to escalate | Who to contact |
|-----------------|----------------|
| P1 not resolved in 30 minutes | SRE Lead |
| Customer-facing impact confirmed | Engineering Manager |
| Security breach suspected | Security Team immediately |
| Azure platform issue suspected | Open Azure support ticket |

---
