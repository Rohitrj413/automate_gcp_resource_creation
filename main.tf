provider "google" {
  project = var.project_id
  region  = "us-east4"
}

variable "project_id" {
  description = "cp-sandbox-rohitvyankt-jagt904"
  type        = string
}

resource "google_compute_instance" "my_web_server" {
  name         = "web-server-instance"
  machine_type = "e2-micro"
  zone         = "us-east4-a"

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
    }
  }

  network_interface {
    network = "default"
    access_config {
      # This block is required to give the instance a public IP address
    }
  }
  
  labels = {
    Environment = "Dev"  # Set to one of the mandatory values (Dev, Stage, Prod)
    Service     = "WebServer" # Set to the required Service tag
  }
}

# Required tags: Environment (must be Dev, Stage, or Prod) and Service
resource "google_storage_bucket" "my_data_bucket" {
  name          = "my-unique-data-bucket-${var.project_id}"
  location      = "US-EAST4"
  storage_class = "STANDARD"

  labels = {
    Environment = "Dev"  # Set to one of the mandatory values (Dev, Stage, Prod)
    Service     = "DataStorage" # Set to the required Service tag
  }
}
