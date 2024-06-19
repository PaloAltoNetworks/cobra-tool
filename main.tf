# Define variables
variable "project_id" {
  description = "The ID of the GCP project"
}

variable "credentials_path" {
  description = "The path to the GCP service account credentials file"
  default     = "path/to/your/credentials.json"
}

# Define provider
provider "google" {
  # credentials = file(var.credentials_path)
  project     = var.project_id
  region      = "us-central1"
}

provider "random" {
}

# Create GCP Service Account
resource "google_service_account" "panw_service_account" {
  account_id   = "panw-service-account"
  display_name = "Panw Service Account"
}

# Define custom IAM role
resource "google_project_iam_custom_role" "panw_service_account_role" {
  role_id     = "panwServiceAccountRole"
  title       = "Panw Service Account Role"
  description = "Custom IAM role for Panw Service Account"
  permissions = [
    "iam.roles.get",
    "iam.roles.list",
    "iam.serviceAccounts.getIamPolicy",
    "iam.serviceAccounts.list",
    "iam.serviceAccountKeys.create",
    "resourcemanager.projects.getIamPolicy"
  ]
}

resource "google_project_iam_binding" "panw-service-role" {
    project = var.project_id
    role    = "projects/${var.project_id}/roles/panwServiceAccountRole"
     members = [
         "serviceAccount:${google_service_account.panw_service_account.email}"
     ]
 }

 resource "google_project_iam_binding" "sa_impersonation" {
  project = var.project_id
  role    = "roles/iam.serviceAccountTokenCreator"

  members = [
    "serviceAccount:${google_service_account.panw_service_account.email}"
  ]
}

# Create GCP VM
resource "google_compute_instance" "victim_vm" {
  name         = "victim-vm"
  machine_type = "e2-medium"
  zone         = "us-central1-a"  # Specify your desired zone

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2004-lts"  # Ubuntu 20.04 LTS image
      size = "30"
      type = "pd-balanced"
    }
  }

  network_interface {
    network = "default"
    access_config {
      // Allow SSH access
      nat_ip = google_compute_address.external_ip.address
    }
  }

  metadata_startup_script = <<-EOF
    #!/bin/bash
sed 's/PasswordAuthentication no/PasswordAuthentication yes/' -i /etc/ssh/sshd_config
systemctl restart sshd
export labUbuntuUserName=labuser
export labUserPassword=Password!
useradd $labUbuntuUserName
echo -e "$labUserPassword\n$labUserPassword" | passwd $labUbuntuUserName
echo 'labuser ALL=(ALL:ALL) ALL' >> /etc/sudoers
mkdir /home/$labUbuntuUserName
chown -R $labUbuntuUserName:$labUbuntuUserName /home/$labUbuntuUserName
sudo usermod -s /bin/bash $labUbuntuUserName
#sudo apt update -y
sudo apt install python3-pip -y
sudo apt install python3-flask -y
# sudo apt install docker.io -y
#sudo chmod 666 /var/run/docker.sock
#apt install docker-compose -y
sudo apt install unzip -y
#sudo usermod -aG docker $labUbuntuUserName
wget -P /home/$labUbuntuUserName/ https://cloudlabsdemo99.s3.amazonaws.com/flask-rce.zip 
cd /home/$labUbuntuUserName/
unzip /home/$labUbuntuUserName/flask-rce.zip 
pip3 install -r requirements.txt
flask run --host=0.0.0.0
EOF

  # Attach the service account to the VM with specified roles and permissions
  service_account {
    email  = google_service_account.panw_service_account.email
    scopes = ["cloud-platform"]
  }

  metadata = {
    iam-service-account = google_project_iam_custom_role.panw_service_account_role.role_id
  }
}

# External IP for HTTP 5000 access
resource "google_compute_address" "external_ip" {
   name = "external8933"
}

# Create firewall rule to allow HTTP 5000 access
resource "google_compute_firewall" "allow_ssh" {
  name    = "allow-ssh"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["5000"]
  }

  source_ranges = ["0.0.0.0/0"]
}


resource "random_string" "unique_id" {
  special   = false
  length    = 5
  min_lower = 5
}

# Create GCP Storage Bucket
resource "google_storage_bucket" "victim_bucket-38383" {
  name          = "victim-bucket-${random_string.unique_id.result}"
  location      = "US"
}

# Grant permissions to GCP VM service account to access the bucket
resource "google_storage_bucket_iam_binding" "grant_vm_access" {
  bucket = google_storage_bucket.victim_bucket-38383.name
  role   = "roles/storage.objectAdmin"

  members = [
      "serviceAccount:${google_compute_instance.victim_vm.service_account[0].email}"
   ]
}

# Create another GCP Secret Service Account
resource "google_service_account" "secret_manager_service_account" {
  account_id   = "secret-manager-service-account"
  display_name = "Secret Manager Service Account"
}

# Define custom Secret IAM role
resource "google_project_iam_custom_role" "panw_secret_role" {
  role_id     = "panwSecretAccountRole"
  title       = "Panw Secret Account Role"
  description = "Custom IAM role for Panw Secret Account"
  permissions = [
    "resourcemanager.projects.getIamPolicy",
    "resourcemanager.projects.get",
    "secretmanager.locations.get",
    "secretmanager.secrets.list",
    "secretmanager.versions.access",
    "secretmanager.versions.get",
    "secretmanager.versions.list",
    "secretmanager.secrets.get"
  ]
}

# Attach the secret manager admin role to the service account
resource "google_project_iam_binding" "panw-secret-role" {
    project = var.project_id
    role    = "projects/${var.project_id}/roles/panwSecretAccountRole"
    members = [ "serviceAccount:${google_service_account.secret_manager_service_account.email}" ]
 }

# Create secret in Secret Manager
resource "google_secret_manager_secret" "flag_secret" {
  provider = google-beta
  secret_id = "flag-secret"

  replication {
    user_managed {
      replicas {
        location = "us-central1"
      }
      replicas {
        location = "us-east1"
      }
    }
  }
}

resource "google_secret_manager_secret_version" "flag_secret_version" {
  provider = google-beta
  secret = google_secret_manager_secret.flag_secret.name
  secret_data = "7d61f93d434686fde32aad0011b24c13acf65f64"
}

resource "google_service_account_iam_binding" "token_creator_binding" {
  service_account_id = google_service_account.secret_manager_service_account.name
  role               = "roles/iam.serviceAccountTokenCreator"

  members = [
    "serviceAccount:${google_service_account.panw_service_account.email}",
  ]
}

resource "google_service_account_iam_binding" "account_user_binding" {
  service_account_id = google_service_account.secret_manager_service_account.name
  role               = "roles/iam.serviceAccountUser"

  members = [
    "serviceAccount:${google_service_account.panw_service_account.email}",
  ]
}

# Output the public IP address of the VM
output "vm_public_ip" {
  value = google_compute_address.external_ip.address
}
