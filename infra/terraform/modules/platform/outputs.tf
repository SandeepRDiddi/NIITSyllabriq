output "project_id" {
  value = digitalocean_project.this.id
}

output "vpc_id" {
  value = digitalocean_vpc.this.id
}

output "doks_cluster_id" {
  value = digitalocean_kubernetes_cluster.this.id
}

output "doks_cluster_name" {
  value = digitalocean_kubernetes_cluster.this.name
}

output "postgres_host" {
  value = digitalocean_database_cluster.postgres.host
}

output "postgres_uri" {
  value     = digitalocean_database_cluster.postgres.uri
  sensitive = true
}

output "container_registry_endpoint" {
  value = digitalocean_container_registry.this.endpoint
}

output "training_bucket" {
  value = digitalocean_spaces_bucket.training.name
}

output "requirements_bucket" {
  value = digitalocean_spaces_bucket.requirements.name
}

output "exports_bucket" {
  value = digitalocean_spaces_bucket.exports.name
}

output "llama_private_ip" {
  value = var.enable_llama_gpu ? digitalocean_droplet.llama[0].ipv4_address_private : null
}
