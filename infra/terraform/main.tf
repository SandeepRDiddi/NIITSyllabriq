terraform {
  required_version = ">= 1.6.0"

  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.46"
    }
  }
}

provider "digitalocean" {}

module "platform" {
  source = "./modules/platform"

  project_name                = var.project_name
  environment                 = var.environment
  region                      = var.region
  vpc_ip_range                = var.vpc_ip_range
  doks_cluster_name           = var.doks_cluster_name
  doks_version                = var.doks_version
  enable_doks_ha              = var.enable_doks_ha
  app_node_size               = var.app_node_size
  app_node_min_count          = var.app_node_min_count
  app_node_max_count          = var.app_node_max_count
  worker_node_size            = var.worker_node_size
  worker_node_min_count       = var.worker_node_min_count
  worker_node_max_count       = var.worker_node_max_count
  postgres_engine_version     = var.postgres_engine_version
  postgres_size               = var.postgres_size
  postgres_node_count         = var.postgres_node_count
  postgres_database_name      = var.postgres_database_name
  postgres_app_user           = var.postgres_app_user
  container_registry_name     = var.container_registry_name
  spaces_region               = var.spaces_region
  spaces_training_bucket      = var.spaces_training_bucket
  spaces_requirements_bucket  = var.spaces_requirements_bucket
  spaces_exports_bucket       = var.spaces_exports_bucket
  enable_llama_gpu            = var.enable_llama_gpu
  llama_gpu_name              = var.llama_gpu_name
  llama_gpu_size              = var.llama_gpu_size
  llama_gpu_image             = var.llama_gpu_image
  admin_ssh_key_ids           = var.admin_ssh_key_ids
  tags                        = var.tags
}
