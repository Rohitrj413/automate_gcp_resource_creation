# Configure the Google Cloud provider
provider "google" {
  project = var.project_id
  region  = "us-east4"
}

# Define a variable for the project ID
variable "project_id" {
  description = "cp-sandbox-rohitvyankt-jagt904"
  type        = string
}

# Create a new Google Compute Engine instance
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
}

# Create a Google Cloud Storage bucket
resource "google_storage_bucket" "my_data_bucket" {
  name          = "my-unique-data-bucket-${var.project_id}"
  location      = "US-EAST4"
  storage_class = "STANDARD"
}