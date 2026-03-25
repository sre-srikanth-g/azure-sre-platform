# =============================================================================
# modules/monitoring/variables.tf
# Author: Srikanth Gandikota
# =============================================================================

variable "project_name" {
  description = "Project name — used as prefix for monitoring resources"
  type        = string
}

variable "resource_group_name" {
  description = "Resource group to deploy monitoring resources into"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "vm_id" {
  description = "Resource ID of the VM to monitor — from the VM module output"
  type        = string
}

variable "vm_name" {
  description = "Name of the VM — used in alert rule names"
  type        = string
}

variable "alert_email" {
  description = "Email address to send alerts to when rules fire"
  type        = string
}

variable "tags" {
  description = "Tags to apply to all monitoring resources"
  type        = map(string)
  default     = {}
}
