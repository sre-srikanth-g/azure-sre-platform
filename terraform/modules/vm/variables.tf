# =============================================================================
# modules/vm/variables.tf
# Author: Srikanth Gandikota
# Description: Input variables for the VM module
# These are the settings you pass in when calling this module from main.tf
# =============================================================================

variable "vm_name" {
  description = "Name of the virtual machine"
  type        = string
}

variable "resource_group_name" {
  description = "Resource group to deploy the VM into"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "subnet_id" {
  description = "ID of the subnet to attach the VM network card to"
  type        = string
}

variable "vm_size" {
  description = "VM size — Standard_B1s is free tier eligible"
  type        = string
  default     = "Standard_B1s"
}

variable "admin_username" {
  description = "Admin username to log into the VM"
  type        = string
}

variable "admin_password" {
  description = "Admin password — marked sensitive so it never appears in logs"
  type        = string
  sensitive   = true
}

variable "tags" {
  description = "Tags to apply to all resources in this module"
  type        = map(string)
  default     = {}
}
