output "project_id" {
  value = module.platform.project_id
}

output "vpc_id" {
  value = module.platform.vpc_id
}

output "doks_cluster_id" {
  value = module.platform.doks_cluster_id
}

output "doks_cluster_name" {
  value = module.platform.doks_cluster_name
}

output "postgres_host" {
  value = module.platform.postgres_host
}

output "postgres_uri" {
  value     = module.platform.postgres_uri
  sensitive = true
}

output "container_registry_endpoint" {
  value = module.platform.container_registry_endpoint
}

output "training_bucket" {
  value = module.platform.training_bucket
}

output "requirements_bucket" {
  value = module.platform.requirements_bucket
}

output "exports_bucket" {
  value = module.platform.exports_bucket
}

output "llama_private_ip" {
  value = module.platform.llama_private_ip
}
