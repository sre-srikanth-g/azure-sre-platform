# =============================================================================
# modules/monitoring/outputs.tf
# Author: Srikanth Gandikota
# =============================================================================

output "action_group_id" {
  description = "ID of the alert action group — used to connect more alerts later"
  value       = azurerm_monitor_action_group.sre_alerts.id
}

output "log_analytics_workspace_id" {
  description = "ID of the Log Analytics Workspace — used to connect more resources"
  value       = azurerm_log_analytics_workspace.main.id
}

output "log_analytics_workspace_name" {
  description = "Name of the Log Analytics Workspace"
  value       = azurerm_log_analytics_workspace.main.name
}
