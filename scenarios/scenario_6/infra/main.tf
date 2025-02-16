provider "azurerm" {
  features {}
  tenant_id = var.tenantid
  subscription_id = var.subid  
}

data "azurerm_client_config" "current" {}

resource "azurerm_resource_group" "rg" {
  name     = "demo-vm-rg"
  location = "East US"
}

resource "azurerm_virtual_network" "vnet" {
  name                = "demo-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
}

resource "azurerm_subnet" "subnet" {
  name                 = "demo-subnet"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.1.0/24"]
}

# Create a Public IP
resource "azurerm_public_ip" "public_ip" {
  name                = "demo-public-ip"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  allocation_method   = "Static"
}

# Create Network Security Group
resource "azurerm_network_security_group" "nsg" {
  name                = "demo-nsg"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name


# NSG Rule to allow SSH (port 22)
 security_rule  {
  name                        = "allow-ssh"
  priority                    = 1000
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  destination_port_range      = "22"
  source_address_prefix       = "*"
  destination_address_prefix  = "*"
 }

# NSG Rule to allow HTTP on port 8081
 security_rule {
  name                        = "allow-5000"
  priority                    = 1010
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  destination_port_range      = "5000"
  source_address_prefix       = "*"
  destination_address_prefix  = "*"
 }
}

resource "azurerm_network_interface" "nic" {
  name                = "demo-nic"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  ip_configuration {
    name                          = "demo-ip-configuration"
    subnet_id                     = azurerm_subnet.subnet.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.public_ip.id  # Associate Public IP
  }
}
resource "azurerm_network_interface_security_group_association" "my-nsg-assoc" {
  network_interface_id      = azurerm_network_interface.nic.id
  network_security_group_id = azurerm_network_security_group.nsg.id
}

resource "tls_private_key" "ssh_key" {
  algorithm = "RSA"
  rsa_bits  = 2048
}

resource "local_file" "private_key" {
  filename = "${path.module}/id_rsa"
  content  = tls_private_key.ssh_key.private_key_pem
}

resource "local_file" "public_key" {
  filename = "${path.module}/id_rsa.pub"
  content  = tls_private_key.ssh_key.public_key_openssh
}

resource "azurerm_linux_virtual_machine" "linux_vm" {
  name                  = "demo-linux-vm"
  resource_group_name   = azurerm_resource_group.rg.name
  location              = azurerm_resource_group.rg.location
  size                  = "Standard_B1s"
  admin_username        = "azureuser"
  disable_password_authentication = true

  network_interface_ids = [
    azurerm_network_interface.nic.id,
  ]

  admin_ssh_key {
    username   = "azureuser"
    public_key = tls_private_key.ssh_key.public_key_openssh
  }

  custom_data = base64encode(<<EOT
#!/bin/bash
sudo apt update -y
sudo apt install python3-pip -y
sudo apt install python3-flask -y
sudo apt install unzip -y
sudo apt install jq -y
cd /home/azureuser/ && wget -P /home/azureuser/ https://cloudlabsdemo99.s3.amazonaws.com/flask-rce.zip 
cd /home/azureuser/ && unzip flask-rce.zip 
cd /home/azureuser/ && sudo pip3 install -r requirements.txt
cd /home/azureuser/ && sudo chown azureuser:azureuser Dockerfile app.py requirements.txt
cd /home/azureuser/ && sudo chown -R azureuser:azureuser templates/
cd /home/azureuser/ && export FLASK_APP="app.py"
cd /home/azureuser/ && flask run --host=0.0.0.0 &
EOT
  )

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
    disk_size_gb         = 30
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "UbuntuServer"
    sku       = "18.04-LTS"
    version   = "latest"
  }

  identity {
    type = "SystemAssigned"
  }
}

resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

resource "azurerm_key_vault" "key_vault" {
  name                = "demo-key-vault-${random_string.suffix.result}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"
}

# Access policy for yourself (the admin)
resource "azurerm_key_vault_access_policy" "key_vault_policy_admin" {
  key_vault_id = azurerm_key_vault.key_vault.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = data.azurerm_client_config.current.object_id  # Admin's object ID

  secret_permissions = [
    "Get",
    "List",
    "Set",
    "Delete",
    "Purge"
  ]
}

resource "azurerm_key_vault_access_policy" "key_vault_policy" {
  key_vault_id = azurerm_key_vault.key_vault.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_linux_virtual_machine.linux_vm.identity[0].principal_id

  secret_permissions = [
    "Get",
    "List",
    "Set",
  ]
}

resource "azurerm_key_vault_secret" "example_secret" {
  name         = "DatabasePassword"
  value        = "SuperSecurePassword123!"
  key_vault_id = azurerm_key_vault.key_vault.id
  depends_on = [
    azurerm_key_vault_access_policy.key_vault_policy_admin,
    azurerm_key_vault_access_policy.key_vault_policy
  ]
}

output "ssh_private_key_path" {
  value = local_file.private_key.filename
}

output "ssh_public_key_path" {
  value = local_file.public_key.filename
}

output "vm_public_ip" {
  value = azurerm_public_ip.public_ip.ip_address
}

output "vault_name"{
    value = azurerm_key_vault.key_vault.name
}