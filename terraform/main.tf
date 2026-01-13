# ==============================================
# NEURO-SENTINEL Terraform Configuration
# GCP Cloud Run Infrastructure
# ==============================================

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  
  # Optional: Configure remote backend for state
  # backend "gcs" {
  #   bucket = "neuro-sentinel-terraform-state"
  #   prefix = "terraform/state"
  # }
}

# ==============================================
# Variables
# ==============================================
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region for deployment"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "Name of the Cloud Run service"
  type        = string
  default     = "neuro-sentinel-app"
}

variable "container_image" {
  description = "Docker image URL in Artifact Registry"
  type        = string
}

variable "min_instances" {
  description = "Minimum number of instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 10
}

variable "memory_limit" {
  description = "Memory limit per container"
  type        = string
  default     = "512Mi"
}

variable "cpu_limit" {
  description = "CPU limit per container"
  type        = string
  default     = "1"
}

variable "port" {
  description = "Container port"
  type        = number
  default     = 8080
}

variable "secrets" {
  description = "Map of secret names to their Secret Manager secret IDs"
  type        = map(string)
  default     = {}
}

# ==============================================
# Provider Configuration
# ==============================================
provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "iam.googleapis.com",
  ])
  
  service            = each.key
  disable_on_destroy = false
}
