# =============================================================================
# variables.tf
# Author: Srikanth Gandikota
# Description: All input variables for the SRE platform
# These are like settings — change the value here, it updates everywhere
# =============================================================================

variable "project_name" {
  description = "Name of the project — used as prefix for all Azure resources"
  type        = string
  default     = "sre-demo"
}

variable "environment" {
  description = "Which environment — dev, qa, or prod"
  type        = string
  default     = "dev"

  # Validation — only allow these values, nothing else
  validation {
    condition     = contains(["dev", "qa", "prod"], var.environment)
    error_message = "Environment must be dev, qa, or prod."
  }
}

variable "location" {
  description = "Azure region to deploy resources into"
  type        = string
  default     = "East US"
}

variable "vm_size" {
  description = "Azure VM size — Standard_B1s is free tier eligible"
  type        = string
  default     = "Standard_B1s"
}

variable "admin_username" {
  description = "Admin username for the VM"
  type        = string
  default     = "sreadmin"
}

variable "admin_password" {
  description = "Admin password for the VM — never hardcode this, always use tfvars"
  type        = string
  sensitive   = true
  # No default — must be provided. sensitive = true means it won't show in logs
}

variable "alert_email" {
  description = "Email address to receive Azure Monitor alerts"
  type        = string
  default     = "sre.srikanthg@gmail.com"
}
