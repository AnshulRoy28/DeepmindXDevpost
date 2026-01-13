# ==============================================
# NEURO-SENTINEL Cloud Run Configuration
# Serverless Container Hosting with Autoscaling
# ==============================================

# Artifact Registry for Docker images
resource "google_artifact_registry_repository" "app_registry" {
  location      = var.region
  repository_id = "${var.service_name}-repo"
  description   = "Docker repository for ${var.service_name}"
  format        = "DOCKER"
  
  depends_on = [google_project_service.required_apis]
}

# Cloud Run Service
resource "google_cloud_run_v2_service" "app" {
  name     = var.service_name
  location = var.region
  
  # Allow unauthenticated access (public API)
  # Change to false for private services
  ingress = "INGRESS_TRAFFIC_ALL"
  
  template {
    # Service Account
    service_account = google_service_account.app_service_account.email
    
    # Autoscaling configuration
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }
    
    # Container configuration
    containers {
      image = var.container_image
      
      # Resource limits
      resources {
        limits = {
          memory = var.memory_limit
          cpu    = var.cpu_limit
        }
        cpu_idle = true  # Scale to zero when idle
      }
      
      # Port configuration
      ports {
        container_port = var.port
      }
      
      # Health check
      startup_probe {
        http_get {
          path = "/health"
          port = var.port
        }
        initial_delay_seconds = 5
        timeout_seconds       = 3
        period_seconds        = 10
        failure_threshold     = 3
      }
      
      liveness_probe {
        http_get {
          path = "/health"
          port = var.port
        }
        initial_delay_seconds = 10
        timeout_seconds       = 3
        period_seconds        = 30
      }
      
      # Environment variables from Secret Manager
      dynamic "env" {
        for_each = var.secrets
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value
              version = "latest"
            }
          }
        }
      }
      
      # Static environment variables
      env {
        name  = "PORT"
        value = tostring(var.port)
      }
      
      env {
        name  = "ENVIRONMENT"
        value = "production"
      }
      
      env {
        name  = "GCP_PROJECT"
        value = var.project_id
      }
    }
    
    # Execution environment
    execution_environment = "EXECUTION_ENVIRONMENT_GEN2"
    
    # Timeout for requests
    timeout = "300s"
    
    # Max concurrent requests per container
    max_instance_request_concurrency = 80
  }
  
  # Traffic configuration (100% to latest revision)
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
  
  depends_on = [
    google_project_service.required_apis,
    google_artifact_registry_repository.app_registry,
  ]
}

# Allow unauthenticated access (public endpoint)
resource "google_cloud_run_service_iam_member" "public_access" {
  location = google_cloud_run_v2_service.app.location
  service  = google_cloud_run_v2_service.app.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ==============================================
# Outputs
# ==============================================
output "service_url" {
  description = "URL of the deployed Cloud Run service"
  value       = google_cloud_run_v2_service.app.uri
}

output "service_name" {
  description = "Name of the Cloud Run service"
  value       = google_cloud_run_v2_service.app.name
}

output "artifact_registry_url" {
  description = "URL for pushing Docker images"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.app_registry.repository_id}"
}
