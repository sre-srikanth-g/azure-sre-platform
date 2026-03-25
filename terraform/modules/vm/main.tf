# =============================================================================
# modules/vm/main.tf
# Author: Srikanth Gandikota
# Description: Reusable Azure VM module
#
# WHY A MODULE?
# Instead of writing this VM code in every environment (dev, qa, prod),
# we write it once here and call it from main.tf with different settings.
# This is exactly what "modular Terraform" means.
# =============================================================================

# Public IP address — needed to SSH into the VM and run health checks
resource "azurerm_public_ip" "vm" {
  name                = "${var.vm_name}-pip"
  resource_group_name = var.resource_group_name
  location            = var.location
  allocation_method   = "Static"
  sku                 = "Standard"

  tags = var.tags
}

# Network Interface Card — connects the VM to the subnet
resource "azurerm_network_interface" "vm" {
  name                = "${var.vm_name}-nic"
  location            = var.location
  resource_group_name = var.resource_group_name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = var.subnet_id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.vm.id
  }

  tags = var.tags
}

# The Virtual Machine itself
resource "azurerm_linux_virtual_machine" "vm" {
  name                = var.vm_name
  resource_group_name = var.resource_group_name
  location            = var.location
  size                = var.vm_size

  # Login credentials
  admin_username                  = var.admin_username
  admin_password                  = var.admin_password
  disable_password_authentication = false

  # Connect VM to the network interface above
  network_interface_ids = [azurerm_network_interface.vm.id]

  # OS disk — Standard_LRS is cheapest and free tier eligible
  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
    disk_size_gb         = 30
  }

  # Ubuntu 18.04 LTS — same OS used in production SRE environments
  source_image_reference {
    publisher = "Canonical"
    offer     = "UbuntuServer"
    sku       = "18.04-LTS"
    version   = "latest"
  }

  # Bootstrap script — runs automatically when VM first starts
  # Installs Python3 and Azure CLI so health checks can run
  custom_data = base64encode(<<-EOF
    #!/bin/bash
    apt-get update -y
    apt-get install -y python3 python3-pip curl
    curl -sL https://aka.ms/InstallAzureCLIDeb | bash
    echo "Bootstrap complete" >> /var/log/sre-bootstrap.log
  EOF
  )

  tags = var.tags
}
