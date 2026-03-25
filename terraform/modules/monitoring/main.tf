# =============================================================================
# modules/monitoring/main.tf
# Author: Srikanth Gandikota
# Description: Azure Monitor alerts and Log Analytics Workspace
#
# This is exactly what SRE teams use to detect incidents before users do.
# The alert rules here are real production patterns — CPU threshold,
# VM availability, disk space. The Log Analytics workspace is where
# KQL queries run during incident investigation.
# =============================================================================

# =============================================================================
# ACTION GROUP
# Defines WHO gets notified when an alert fires
# This is like PagerDuty's notification channel — but native to Azure
# =============================================================================

resource "azurerm_monitor_action_group" "sre_alerts" {
  name                = "${var.project_name}-alerts-ag"
  resource_group_name = var.resource_group_name
  short_name          = "srealerts"

  # Send email to on-call engineer when alert fires
  email_receiver {
    name                    = "SRE On-Call Engineer"
    email_address           = var.alert_email
    use_common_alert_schema = true
  }

  tags = var.tags
}

# =============================================================================
# ALERT RULE 1 — CPU too high
# Fires when CPU stays above 80% for 5 continuous minutes
# Why 5 minutes? A single spike is normal. 5 minutes means something is wrong.
# =============================================================================

resource "azurerm_monitor_metric_alert" "cpu_high" {
  name                = "${var.vm_name}-cpu-high"
  resource_group_name = var.resource_group_name
  scopes              = [var.vm_id]
  description         = "CPU has been above 80% for 5 minutes — investigate for runaway processes"

  # Severity: 0=Critical, 1=Error, 2=Warning, 3=Informational
  severity    = 2
  frequency   = "PT1M"   # Check every 1 minute
  window_size = "PT5M"   # Over a 5 minute window

  criteria {
    metric_namespace = "Microsoft.Compute/virtualMachines"
    metric_name      = "Percentage CPU"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 80
  }

  action {
    action_group_id = azurerm_monitor_action_group.sre_alerts.id
  }

  tags = var.tags
}

# =============================================================================
# ALERT RULE 2 — VM unavailable (most critical SRE alert)
# Fires immediately when VM stops responding
# This is a Severity 0 = Critical — wake someone up NOW
# =============================================================================

resource "azurerm_monitor_metric_alert" "vm_unavailable" {
  name                = "${var.vm_name}-unavailable"
  resource_group_name = var.resource_group_name
  scopes              = [var.vm_id]
  description         = "CRITICAL — VM is not responding. SLA breach risk. Page on-call immediately."
  severity            = 0
  frequency           = "PT1M"
  window_size         = "PT5M"

  criteria {
    metric_namespace = "Microsoft.Compute/virtualMachines"
    metric_name      = "VmAvailabilityMetric"
    aggregation      = "Average"
    operator         = "LessThan"
    threshold        = 1
  }

  action {
    action_group_id = azurerm_monitor_action_group.sre_alerts.id
  }

  tags = var.tags
}

# =============================================================================
# ALERT RULE 3 — Disk space running low
# Fires when OS disk usage exceeds 85%
# Give the team time to clean up before the disk fills completely
# =============================================================================

resource "azurerm_monitor_metric_alert" "disk_low" {
  name                = "${var.vm_name}-disk-low"
  resource_group_name = var.resource_group_name
  scopes              = [var.vm_id]
  description         = "OS disk usage is above 85% — run disk cleanup before it fills completely"
  severity            = 2
  frequency           = "PT5M"
  window_size         = "PT15M"

  criteria {
    metric_namespace = "Microsoft.Compute/virtualMachines"
    metric_name      = "OS Disk Used Bytes"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 85
  }

  action {
    action_group_id = azurerm_monitor_action_group.sre_alerts.id
  }

  tags = var.tags
}

# =============================================================================
# LOG ANALYTICS WORKSPACE
# This is where all Azure logs are stored and queried with KQL
# When you run KQL queries in the Azure portal — this is what you query
# =============================================================================

resource "azurerm_log_analytics_workspace" "main" {
  name                = "${var.project_name}-law"
  resource_group_name = var.resource_group_name
  location            = var.location

  # PerGB2018 = pay per GB of logs — free tier allows 5GB per month
  sku               = "PerGB2018"
  retention_in_days = 30

  tags = var.tags
}

# =============================================================================
# DIAGNOSTIC SETTINGS
# Connects the VM to Log Analytics so its metrics appear in KQL queries
# Without this, the VM metrics stay in Azure Monitor but not in Log Analytics
# =============================================================================

resource "azurerm_monitor_diagnostic_setting" "vm_diagnostics" {
  name               = "${var.vm_name}-diagnostics"
  target_resource_id = var.vm_id

  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  metric {
    category = "AllMetrics"
    enabled  = true
  }
}
