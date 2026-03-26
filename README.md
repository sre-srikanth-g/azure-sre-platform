# azure-sre-platform

**Author:** Srikanth Gandikota
**Contact:** sre.srikanthg@gmail.com
**Role:** Senior DevOps / SRE Engineer

---

## What This Project Is

A production-grade Azure SRE platform built entirely with free tools.
It demonstrates every skill required for a Senior SRE / Cloud Engineer role —
Terraform, Python automation, CI/CD pipelines, Azure Monitor, KQL queries,
SLI/SLO definitions, incident response runbooks, and auto-remediation.

This project was built to demonstrate real SRE practices — not just
list tools on a resume but show how they work together in a
production-grade platform.

---

## Skills Demonstrated

| Skill | How it is demonstrated |
|-------|----------------------|
| Azure cloud infrastructure | Terraform-managed VMs, VNets, NSGs, Azure Monitor |
| Infrastructure as Code | Modular Terraform with reusable modules |
| Python scripting | health_check.py, alert_handler.py |
| Bash scripting | deploy.sh with safety checks |
| CI/CD pipelines | GitHub Actions — validate, scan, deploy, health check |
| Azure Monitor & alerting | 3 alert rules — CPU, availability, disk |
| Log Analytics & KQL | 8 production queries with explanations |
| SLIs / SLOs / Error budgets | Formally defined with KQL measurement queries |
| Auto-remediation | alert_handler.py — VM restart, disk cleanup, audit trail |
| Incident response | Full P1 runbook with postmortem template |
| DevSecOps | tfsec and Checkov security scanning in CI/CD |
| Documentation | Architecture docs, runbooks, KQL reference |

---

## Architecture
```
GitHub Actions CI/CD
        |
        | deploys via Terraform
        v
Azure Resource Group
        |
        |---- Virtual Network (10.0.0.0/16)
        |         |
        |         |---- Subnet (10.0.1.0/24)
        |         |---- NSG (SSH only inbound)
        |
        |---- Linux VM (Ubuntu 18.04, Standard_B1s)
        |         |
        |         |---- Azure Monitor Diagnostics
        |
        |---- Log Analytics Workspace
        |         |
        |         |---- KQL queries for incident investigation
        |         |---- SLO measurement queries
        |
        |---- Azure Monitor Alert Rules
                  |
                  |---- CPU > 80% for 5 minutes  (Severity 2)
                  |---- VM unavailable            (Severity 0 - Critical)
                  |---- Disk > 85%               (Severity 2)
                  |
                  v
             Action Group
             (email alert to on-call engineer)
```

---

## Project Structure
```
azure-sre-platform/
├── .github/
│   └── workflows/
│       └── ci-cd.yml            # Full CI/CD pipeline
├── terraform/
│   ├── main.tf                  # Core infrastructure
│   ├── variables.tf             # All input variables
│   ├── outputs.tf               # Output values
│   ├── terraform.tfvars.example # Config template
│   └── modules/
│       ├── vm/                  # Reusable VM module
│       │   ├── main.tf
│       │   ├── variables.tf
│       │   └── outputs.tf
│       └── monitoring/          # Azure Monitor module
│           ├── main.tf
│           ├── variables.tf
│           └── outputs.tf
├── scripts/
│   ├── health_check.py          # VM health check — Python
│   └── alert_handler.py         # Auto-remediation — Python
├── slo/
│   └── slo_definition.md        # SLI/SLO/Error budget definitions
├── runbooks/
│   └── incident_response.md     # P1 response process and postmortem
├── docs/
│   └── kql_queries.md           # 8 KQL queries with explanations
└── README.md                    # This file
```

---

## CI/CD Pipeline

Every push triggers this pipeline automatically:
```
Pull Request opened
      |
      |---- Terraform Validate -----> catches syntax errors
      |---- tfsec Security Scan ----> catches insecure configs
      |---- Python Lint ------------> catches code quality issues
      |
      | (all three must pass)
      v
Merge to main
      |
      |---- Deploy to dev ----------> terraform apply
      |---- Post-deploy health check> python3 health_check.py
      |---- Upload health report ---> downloadable artifact

Every hour (scheduled):
      |
      |---- Health Check -----------> python3 health_check.py
      |---- If FAIL ----------------> create GitHub issue automatically
```

---

## Key Files Explained

### terraform/main.tf
Core infrastructure — resource group, VNet, subnet, NSG.
Calls the VM module and monitoring module with environment-specific settings.

### terraform/modules/vm/
Reusable VM module. Called from main.tf with different parameters
for dev, qa, and prod — same code, different settings.
This is modular Terraform as used at Intact Insurance across 70+ repositories.

### terraform/modules/monitoring/
Azure Monitor alert rules and Log Analytics Workspace.
Three alert rules: CPU threshold, VM availability, disk space.
Action group sends email to on-call engineer when any alert fires.

### scripts/health_check.py
Checks VM health every hour via GitHub Actions scheduled pipeline.
Logs results to health_check.log and health_report.json.
Exits with code 1 if any VM is unhealthy — causes pipeline to fail
and triggers automatic GitHub issue creation.

### scripts/alert_handler.py
Auto-remediation script. Performs safe fixes automatically:
- `restart-vm` — restarts a stopped or unresponsive VM
- `disk-cleanup` — runs cleanup script on VM via Azure Run Command

Every action is logged to audit_trail.jsonl — full audit trail
for compliance in regulated environments (healthcare, financial services).

### slo/slo_definition.md
Formal SLI/SLO definitions with KQL queries to measure them.
Based on the 99.5% uptime SLA maintained at AXIS Specialty Canada.

### runbooks/incident_response.md
Full P1 incident response process — from alert acknowledgement
through triage, diagnosis, resolution, and postmortem.
Includes postmortem template and escalation path.

### docs/kql_queries.md
8 production KQL queries with line-by-line explanations.
Covers incident triage, SLO measurement, anomaly detection,
and error budget burn rate.

---

## Getting Started

### Prerequisites
```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Install Terraform
wget https://releases.hashicorp.com/terraform/1.5.0/terraform_1.5.0_linux_amd64.zip
unzip terraform_1.5.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# Verify
az --version
terraform --version
python3 --version
```

### Deploy infrastructure
```bash
# Clone the repo
git clone https://github.com/sre-srikanth-g/azure-sre-platform.git
cd azure-sre-platform

# Log in to Azure
az login

# Set up config
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
# Edit terraform.tfvars with your values

# Deploy
cd terraform
terraform init
terraform plan
terraform apply
```

### Run health check
```bash
python3 scripts/health_check.py
```

### Test auto-remediation
```bash
# Stop the VM to simulate a failure
az vm deallocate \
  --resource-group sre-demo-dev-rg \
  --name sre-demo-dev-vm

# Health check should now report unhealthy
python3 scripts/health_check.py

# Auto-remediation restarts it
python3 scripts/alert_handler.py \
  --action restart-vm \
  --rg sre-demo-dev-rg \
  --vm sre-demo-dev-vm

# Check the audit trail
cat audit_trail.jsonl
```

---

## SLO Summary

| SLO | Target | Error Budget |
|-----|--------|-------------|
| VM Availability | 99.5% / month | 216 min downtime allowed |
| Health Check Pass Rate | 99% / month | ~7 failed checks allowed |
| Pipeline Success Rate | 95% / month | 5% failures allowed |

Full definitions with KQL measurement queries:
[slo/slo_definition.md](slo/slo_definition.md)

---

## Technologies Used

| Tool | Purpose |
|------|---------|
| Terraform 1.5 | Infrastructure as Code |
| Azure CLI | Azure resource management |
| Python 3.11 | Health checks and auto-remediation |
| Bash | Deployment automation |
| GitHub Actions | CI/CD pipeline |
| tfsec | Terraform security scanning |
| Checkov | IaC policy compliance |
| Azure Monitor | Alerting and metrics |
| Log Analytics | KQL log queries |
| Application Insights | Application telemetry |

---

## Background

This project was built based on real production experience:

****
Primary on-call engineer for Duck Creek insurance SaaS platform.
Owned 24x7 P1 incident response, application incident management,
PowerShell automation, and the full cloud migration from on-premise
to Azure and then to Duck Creek Cloud (DCOD).
The runbooks, SLO definitions, and incident response process in
this project are based directly on that production experience.

****
Senior Azure DevOps Engineer managing cloud platform for 70+
repositories. Terraform IaC, AKS operations, Azure Monitor
observability, CI/CD pipeline standardisation, Entra ID governance.
The Terraform modules and GitHub Actions pipeline in this project
reflect the patterns used at scale.
