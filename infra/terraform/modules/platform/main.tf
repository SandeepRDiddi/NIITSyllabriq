resource "digitalocean_project" "this" {
  name        = var.project_name
  description = "Production infrastructure for NIITSyllabriq"
  purpose     = "Web Application"
  environment = var.environment
}

resource "digitalocean_vpc" "this" {
  name     = "${var.project_name}-${var.environment}-vpc"
  region   = var.region
  ip_range = var.vpc_ip_range
}

resource "digitalocean_container_registry" "this" {
  name                   = var.container_registry_name
  subscription_tier_slug = "basic"
}

resource "digitalocean_spaces_bucket" "training" {
  name   = var.spaces_training_bucket
  region = var.spaces_region
  acl    = "private"
}

resource "digitalocean_spaces_bucket" "requirements" {
  name   = var.spaces_requirements_bucket
  region = var.spaces_region
  acl    = "private"
}

resource "digitalocean_spaces_bucket" "exports" {
  name   = var.spaces_exports_bucket
  region = var.spaces_region
  acl    = "private"
}

resource "digitalocean_kubernetes_cluster" "this" {
  name         = var.doks_cluster_name
  region       = var.region
  version      = var.doks_version
  vpc_uuid     = digitalocean_vpc.this.id
  ha           = var.enable_doks_ha
  auto_upgrade = true
  surge_upgrade = true

  node_pool {
    name       = "app-pool"
    size       = var.app_node_size
    auto_scale = true
    min_nodes  = var.app_node_min_count
    max_nodes  = var.app_node_max_count
    tags       = concat(var.tags, ["app-pool"])
  }
}

resource "digitalocean_kubernetes_node_pool" "workers" {
  cluster_id  = digitalocean_kubernetes_cluster.this.id
  name        = "worker-pool"
  size        = var.worker_node_size
  auto_scale  = true
  min_nodes   = var.worker_node_min_count
  max_nodes   = var.worker_node_max_count
  tags        = concat(var.tags, ["worker-pool"])
}

resource "digitalocean_database_cluster" "postgres" {
  name                 = "${var.project_name}-${var.environment}-pg"
  engine               = "pg"
  version              = var.postgres_engine_version
  size                 = var.postgres_size
  region               = var.region
  node_count           = var.postgres_node_count
  private_network_uuid = digitalocean_vpc.this.id
}

resource "digitalocean_database_db" "app" {
  cluster_id = digitalocean_database_cluster.postgres.id
  name       = var.postgres_database_name
}

resource "digitalocean_database_user" "app" {
  cluster_id = digitalocean_database_cluster.postgres.id
  name       = var.postgres_app_user
}

resource "digitalocean_database_firewall" "postgres" {
  cluster_id = digitalocean_database_cluster.postgres.id

  rule {
    type  = "k8s"
    value = digitalocean_kubernetes_cluster.this.id
  }
}

resource "digitalocean_tag" "default_tags" {
  for_each = toset(var.tags)
  name     = each.value
}

resource "digitalocean_tag" "llama" {
  count = var.enable_llama_gpu ? 1 : 0
  name  = "${var.project_name}-${var.environment}-llama"
}

resource "digitalocean_droplet" "llama" {
  count    = var.enable_llama_gpu ? 1 : 0
  name     = var.llama_gpu_name
  region   = var.region
  size     = var.llama_gpu_size
  image    = var.llama_gpu_image
  ssh_keys = var.admin_ssh_key_ids
  vpc_uuid = digitalocean_vpc.this.id
  tags     = concat(var.tags, ["llama-gpu"])
}

resource "digitalocean_firewall" "llama" {
  count = var.enable_llama_gpu ? 1 : 0
  name  = "${var.project_name}-${var.environment}-llama-fw"

  droplet_ids = [digitalocean_droplet.llama[0].id]

  inbound_rule {
    protocol         = "tcp"
    port_range       = "22"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  inbound_rule {
    protocol         = "tcp"
    port_range       = "8000"
    source_addresses = [var.vpc_ip_range]
  }

  outbound_rule {
    protocol              = "tcp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "udp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
}

resource "digitalocean_project_resources" "this" {
  project = digitalocean_project.this.id
  resources = compact(concat(
    [
      digitalocean_vpc.this.urn,
      digitalocean_container_registry.this.urn,
      digitalocean_kubernetes_cluster.this.urn,
      digitalocean_database_cluster.postgres.urn,
      digitalocean_spaces_bucket.training.urn,
      digitalocean_spaces_bucket.requirements.urn,
      digitalocean_spaces_bucket.exports.urn
    ],
    var.enable_llama_gpu ? [digitalocean_droplet.llama[0].urn] : []
  ))
}
