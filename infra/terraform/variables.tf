variable "project_name" {
  type    = string
  default = "niitsyllabriq"
}

variable "environment" {
  type    = string
  default = "production"
}

variable "region" {
  type    = string
  default = "blr1"
}

variable "spaces_region" {
  type    = string
  default = "blr1"
}

variable "vpc_ip_range" {
  type    = string
  default = "10.30.0.0/16"
}

variable "doks_cluster_name" {
  type    = string
  default = "niitsyllabriq-prod"
}

variable "doks_version" {
  type    = string
  default = "1.32.2-do.0"
}

variable "enable_doks_ha" {
  type    = bool
  default = true
}

variable "app_node_size" {
  type    = string
  default = "s-2vcpu-4gb"
}

variable "app_node_min_count" {
  type    = number
  default = 3
}

variable "app_node_max_count" {
  type    = number
  default = 6
}

variable "worker_node_size" {
  type    = string
  default = "s-2vcpu-4gb"
}

variable "worker_node_min_count" {
  type    = number
  default = 1
}

variable "worker_node_max_count" {
  type    = number
  default = 4
}

variable "postgres_engine_version" {
  type    = string
  default = "16"
}

variable "postgres_size" {
  type    = string
  default = "db-s-1vcpu-2gb"
}

variable "postgres_node_count" {
  type    = number
  default = 2
}

variable "postgres_database_name" {
  type    = string
  default = "niit_design_automation"
}

variable "postgres_app_user" {
  type    = string
  default = "niit_app"
}

variable "container_registry_name" {
  type    = string
  default = "niitsyllabriq-registry"
}

variable "spaces_training_bucket" {
  type    = string
  default = "niitsyllabriq-training-prod"
}

variable "spaces_requirements_bucket" {
  type    = string
  default = "niitsyllabriq-requirements-prod"
}

variable "spaces_exports_bucket" {
  type    = string
  default = "niitsyllabriq-exports-prod"
}

variable "enable_llama_gpu" {
  type    = bool
  default = false
}

variable "llama_gpu_name" {
  type    = string
  default = "niitsyllabriq-llama-prod"
}

variable "llama_gpu_size" {
  type    = string
  default = "g-rtx4000-1-16gb"
}

variable "llama_gpu_image" {
  type    = string
  default = "ubuntu-24-04-x64"
}

variable "admin_ssh_key_ids" {
  type    = list(string)
  default = []
}

variable "tags" {
  type    = list(string)
  default = ["niitsyllabriq", "production"]
}
