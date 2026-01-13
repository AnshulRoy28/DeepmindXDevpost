# ==============================================
# NEURO-SENTINEL IAM Configuration
# Least-Privilege Service Account
# ==============================================

# Service Account for the deployed application
resource "google_service_account" "app_service_account" {
  account_id   = "${var.service_name}-sa"
  display_name = "NEURO-SENTINEL App Service Account"
  description  = "Least-privilege service account for the deployed application"
}

# Service Account for NEURO-SENTINEL agent operations
resource "google_service_account" "sentinel_service_account" {
  account_id   = "neuro-sentinel-agent"
  display_name = "NEURO-SENTINEL Agent Service Account"
  description  = "Service account for NEURO-SENTINEL DevOps agent"
}

# ==============================================
# App Service Account Roles (Runtime)
# ==============================================

# Cloud Run Invoker - allow the app to receive requests
resource "google_project_iam_member" "app_run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.app_service_account.email}"
}

# Secret Manager Access - read secrets at runtime
resource "google_project_iam_member" "app_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.app_service_account.email}"
}

# Cloud Logging Writer - write application logs
resource "google_project_iam_member" "app_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.app_service_account.email}"
}

# ==============================================
# NEURO-SENTINEL Agent Roles (Deployment)
# ==============================================

# Cloud Run Admin - deploy and manage Cloud Run services
resource "google_project_iam_member" "sentinel_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.sentinel_service_account.email}"
}

# Artifact Registry Writer - push Docker images
resource "google_project_iam_member" "sentinel_artifact_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.sentinel_service_account.email}"
}

# Secret Manager Accessor - read secrets for deployment
# NOTE: NOT secretAdmin - agent cannot create/modify secrets
resource "google_project_iam_member" "sentinel_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.sentinel_service_account.email}"
}

# Cloud Logging Viewer - read logs for error detection
# NOTE: NOT logging.admin - agent cannot modify log configuration
resource "google_project_iam_member" "sentinel_log_viewer" {
  project = var.project_id
  role    = "roles/logging.viewer"
  member  = "serviceAccount:${google_service_account.sentinel_service_account.email}"
}

# Service Account User - to deploy as the app service account
resource "google_service_account_iam_member" "sentinel_sa_user" {
  service_account_id = google_service_account.app_service_account.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.sentinel_service_account.email}"
}

# ==============================================
# Security Guardrails
# ==============================================

# IMPORTANT: The following roles are EXPLICITLY NOT granted to prevent
# the NEURO-SENTINEL agent from performing dangerous operations:
#
# - roles/owner / roles/editor (full project access)
# - roles/resourcemanager.* (modify project settings)
# - roles/billing.* (access billing information)
# - roles/secretmanager.admin (create/delete secrets)
# - roles/logging.admin (modify log configuration)
# - roles/iam.* (modify IAM policies)
# - roles/run.developer (delete services) - we use run.admin which is scoped
#
# The agent can ONLY:
# 1. Deploy to Cloud Run (run.admin)
# 2. Push images to Artifact Registry (artifactregistry.writer)
# 3. Read secrets (secretmanager.secretAccessor)
# 4. Read logs (logging.viewer)

output "app_service_account_email" {
  description = "Email of the app service account"
  value       = google_service_account.app_service_account.email
}

output "sentinel_service_account_email" {
  description = "Email of the NEURO-SENTINEL agent service account"
  value       = google_service_account.sentinel_service_account.email
}
