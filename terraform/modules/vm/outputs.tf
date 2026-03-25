# =============================================================================
# modules/vm/outputs.tf
# Author: Srikanth Gandikota
# Description: Values this module exposes to main.tf after creation
# =============================================================================

output "vm_id" {
  description = "Resource ID of the VM — used to connect monitoring to it"
  value       = azurerm_linux_virtual_machine.vm.id
}

output "vm_name" {
  description = "Name of the VM"
  value       = azurerm_linux_virtual_machine.vm.name
}

output "public_ip" {
  description = "Public IP address — use this to SSH into the VM"
  value       = azurerm_public_ip.vm.ip_address
}

output "private_ip" {
  description = "Private IP address inside the VNet"
  value       = azurerm_network_interface.vm.private_ip_address
}
