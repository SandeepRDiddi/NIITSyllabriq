# Terraform for DigitalOcean

This folder provisions the recommended DigitalOcean foundation for NIITSyllabriq:

- project
- VPC
- DOKS cluster
- managed PostgreSQL
- container registry
- Spaces buckets
- optional Llama GPU Droplet
- production-grade tagging and network isolation

## Files

- `main.tf`: root module wiring
- `variables.tf`: configurable inputs
- `outputs.tf`: useful outputs
- `terraform.tfvars.example`: example values
- `modules/platform/`: infrastructure module

## Usage

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
terraform apply
```

Required environment variables:

```bash
export DIGITALOCEAN_TOKEN=your_do_pat
```

Optional:

```bash
export SPACES_ACCESS_KEY_ID=your_spaces_key
export SPACES_SECRET_ACCESS_KEY=your_spaces_secret
```

## Notes

- The Llama GPU host is optional and controlled by `enable_llama_gpu`.
- The default Llama host image is `ubuntu-24-04-x64` so you can install Ollama or vLLM in a supported base OS after provisioning.
- DOKS worker nodes are billed at Droplet rates.
- You should review sizing before production apply.
- Keep `terraform.tfvars` and any generated state out of Git.
