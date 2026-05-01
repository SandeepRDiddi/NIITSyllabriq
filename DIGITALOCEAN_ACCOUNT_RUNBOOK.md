# DigitalOcean Account Runbook

Use this after your DigitalOcean account is ready.

## 1. Prerequisites

You need:

- a DigitalOcean account with billing enabled
- a Personal Access Token
- at least one SSH key uploaded to DigitalOcean
- a domain name you control
- GitHub repository admin access

## 2. Configure local tools

Install:

- `terraform`
- `doctl`
- `kubectl`
- `docker`

Authenticate:

```bash
export DIGITALOCEAN_TOKEN=your_token
doctl auth init -t "$DIGITALOCEAN_TOKEN"
```

## 3. Provision infrastructure

```bash
cd /Users/sandeepdiddi/Documents/NIITSyllabriq/infra/terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your:

- region
- SSH key IDs
- registry name
- bucket names
- whether Llama GPU should be enabled
- production DNS hostnames you intend to use

Then run:

```bash
terraform init
terraform plan
terraform apply
```

## 4. Capture outputs

After apply:

```bash
terraform output
```

Save:

- DOKS cluster name
- registry endpoint
- Postgres URI
- bucket names
- optional Llama private IP

Keep these values in a secure password vault because several of them become GitHub Actions secrets.

## 5. Create GitHub secrets

In GitHub repo settings, add:

- `DIGITALOCEAN_ACCESS_TOKEN`
- `DOCR_REGISTRY`
- `DOKS_CLUSTER_NAME`
- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `SPACES_ACCESS_KEY`
- `SPACES_SECRET_KEY`
- `SPACES_ENDPOINT`
- `SPACES_BUCKET_TRAINING`
- `SPACES_BUCKET_REQUIREMENTS`
- `SPACES_BUCKET_EXPORTS`
- `APP_HOST`
- `API_HOST`
- `ALLOWED_ORIGINS`
- `OLLAMA_BASE_URL`
- `OLLAMA_GENERATION_MODEL`
- `OLLAMA_EMBED_MODEL`

If using hosted Llama:

- `OLLAMA_BASE_URL` should point to the private inference host or proxy URL

Recommended GitHub Environment:

- create a `production` environment
- require manual approval before the deploy workflow runs
- store all deployment secrets in that environment rather than at repo-global scope

## 6. First deployment

Push your code to GitHub, then run:

- GitHub Actions
- workflow: `Deploy to DigitalOcean`
- environment: `production`

Before that first run, make sure your DOKS cluster already has:

- an ingress controller installed
- TLS/certificate management installed if you want HTTPS on day one

The deployment workflow assumes the cluster networking layer is already prepared and then deploys the application workloads on top of it.

The workflow will:

- build backend image
- build frontend image
- push both to DOCR
- save kubeconfig
- render manifests
- apply manifests

## 7. Verify rollout

```bash
doctl kubernetes cluster kubeconfig save YOUR_CLUSTER_NAME
kubectl get ns
kubectl get pods -n niitsyllabriq
kubectl get svc -n niitsyllabriq
kubectl get ingress -n niitsyllabriq
kubectl rollout status deployment/niitsyllabriq-api -n niitsyllabriq
kubectl rollout status deployment/niitsyllabriq-frontend -n niitsyllabriq
```

## 8. Point DNS

Point your domain records to the load balancer hostname or IP that backs the ingress.

Recommended:

- `app.yourdomain.com`
- `api.yourdomain.com`

## 9. Database migration check

The backend container already runs Alembic at startup. Still verify:

```bash
kubectl logs deployment/niitsyllabriq-api -n niitsyllabriq
```

## 10. If using hosted Llama

SSH to the GPU Droplet and complete model bootstrap:

```bash
ssh root@YOUR_GPU_DROPLET_IP
```

Then install and bootstrap inference. Example Ollama setup:

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

Recommended hardening:

- bind Ollama to the private interface only
- restrict inbound access to the VPC CIDR or DOKS node ranges
- front it with Nginx or Caddy if you need TLS or auth between services

After that:

- confirm private model endpoint responds
- update `OLLAMA_BASE_URL` or your internal inference URL secret if needed
- redeploy the API

## 11. Production readiness checklist

- Terraform state saved securely
- all GitHub secrets configured
- domain pointed correctly
- monitoring alerts configured
- DB backup verified
- Spaces access tested
- login flow tested
- requirement upload tested
- design generation tested
- review workflow tested
- export tested
