# =============================================================================
# outputs.tf
# Author: Srikanth Gandikota
# Description: Values shown after terraform apply completes
# Think of these like the receipt after you create infrastructure
# =============================================================================

output "resource_group_name" {
  description = "Name of the resource group created"
  value       = azurerm_resource_group.main.name
}

output "resource_group_location" {
  description = "Azure region where resources were deployed"
  value       = azurerm_resource_group.main.location
}

output "vnet_name" {
  description = "Name of the Virtual Network"
  value       = azurerm_virtual_network.main.name
}

output "vnet_id" {
  description = "Unique ID of the Virtual Network — used when connecting other resources"
  value       = azurerm_virtual_network.main.id
}

output "subnet_id" {
  description = "Unique ID of the subnet — used when creating VMs or AKS clusters"
  value       = azurerm_subnet.main.id
}

output "nsg_name" {
  description = "Name of the Network Security Group"
  value       = azurerm_network_security_group.main.name
}

output "environment" {
  description = "Which environment was deployed"
  value       = var.environment
}
