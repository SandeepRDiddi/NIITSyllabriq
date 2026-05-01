# NIITSyllabriq Infrastructure Proposal

## Proposal Summary

This proposal defines a DigitalOcean-based hosting model for delivering NIITSyllabriq as a commercial SaaS offering to clients.

The recommended architecture is designed for:

- high availability
- controlled operating cost
- clean separation of application and AI inference workloads
- enterprise upgrade paths

## Hosting Tiers

### Tier 1: Standard SaaS

Includes:

- shared multi-tenant app deployment
- DOKS application cluster
- managed PostgreSQL HA
- Spaces document storage
- standard monitoring and backups
- no dedicated hosted Llama inference

Best for:

- small to mid-sized clients
- design automation without dedicated AI hosting

### Tier 2: Premium SaaS

Includes everything in Standard, plus:

- dedicated hosted Llama inference on GPU Droplet
- stricter scaling thresholds
- priority support windows
- dedicated client storage buckets and quotas

Best for:

- clients who want hosted AI as part of the subscription

### Tier 3: Enterprise Single-Tenant

Includes:

- isolated DigitalOcean project
- dedicated DOKS cluster
- dedicated PostgreSQL
- dedicated Spaces buckets
- optional dedicated GPU inference
- optional DR region

Best for:

- compliance-sensitive or large-volume clients

## SLA Positioning

### Standard SaaS

- target uptime commitment: `99.5%`
- support response: next business day

### Premium SaaS

- target uptime commitment: `99.9%`
- support response: within 4 business hours

### Enterprise Single-Tenant

- target uptime commitment: `99.9%` or higher by contract
- support response: custom

## Commercial Notes

- Hosted GPU inference should be billed as a premium add-on
- Disaster recovery in a second region should be a premium add-on
- Single-tenant environments should include implementation/setup fees

## Recommended Sales Framing

Sell the product in two parts:

1. platform subscription
2. AI inference add-on

This protects your margin because GPU hosting costs are materially different from standard application hosting costs.
