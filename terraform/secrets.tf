# ==============================================
# NEURO-SENTINEL Secrets Configuration
# GCP Secret Manager
# ==============================================

# NOTE: This file provides a TEMPLATE for secrets.
# Actual secret values should NEVER be stored in Terraform.
# Use `gcloud secrets create` or the GCP Console to add secret values.

# Example secret placeholders - these create the secret "containers"
# but do NOT populate the actual values.

resource "google_secret_manager_secret" "app_secrets" {
  for_each = toset([
    "DATABASE_URL",
    "API_KEY",
    "JWT_SECRET",
  ])
  
  secret_id = "${var.service_name}-${lower(each.key)}"
  
  replication {
    auto {}
  }
  
  labels = {
    app         = var.service_name
    managed_by  = "neuro-sentinel"
    environment = "production"
  }
  
  depends_on = [google_project_service.required_apis]
}

# Grant the app service account access to read these secrets
resource "google_secret_manager_secret_iam_member" "app_secret_access" {
  for_each = google_secret_manager_secret.app_secrets
  
  secret_id = each.value.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.app_service_account.email}"
}

# ==============================================
# NEURO-SENTINEL Agent API Key
# ==============================================

# This secret stores the Gemini API key for NEURO-SENTINEL
resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "neuro-sentinel-gemini-api-key"
  
  replication {
    auto {}
  }
  
  labels = {
    app         = "neuro-sentinel"
    component   = "agent"
    managed_by  = "terraform"
  }
  
  depends_on = [google_project_service.required_apis]
}

# Grant NEURO-SENTINEL agent access to read the API key
resource "google_secret_manager_secret_iam_member" "sentinel_gemini_access" {
  secret_id = google_secret_manager_secret.gemini_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.sentinel_service_account.email}"
}

# ==============================================
# Outputs
# ==============================================
output "secret_ids" {
  description = "Map of environment variable names to Secret Manager secret IDs"
  value = {
    for k, v in google_secret_manager_secret.app_secrets : 
    k => v.secret_id
  }
}

output "gemini_api_key_secret_id" {
  description = "Secret ID for the Gemini API key"
  value       = google_secret_manager_secret.gemini_api_key.secret_id
}

# ==============================================
# Instructions for Setting Secret Values
# ==============================================
#
# After applying this Terraform, set secret values using:
#
# gcloud secrets versions add <SECRET_ID> --data-file=/path/to/secret.txt
#
# Or for inline values:
#
# echo -n "your-secret-value" | gcloud secrets versions add <SECRET_ID> --data-file=-
#
# Example:
# echo -n "postgresql://user:pass@host:5432/db" | \
#   gcloud secrets versions add neuro-sentinel-app-database_url --data-file=-
#
