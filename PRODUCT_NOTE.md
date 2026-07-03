# Syllabriq — Product Note

---

## Executive Summary

**Syllabriq** is an enterprise-grade design automation platform purpose-built to accelerate the creation, governance, and delivery of structured solution design documents. It eliminates the repetitive, error-prone work of drafting designs from scratch by combining retrieval-augmented generation (RAG), configurable LLM providers, multi-gate approval workflows, and a comprehensive leadership dashboard — all within a privacy-first, local-capable architecture.

Syllabriq has been fully designed, developed, and tested. It is deployment-ready across desktop, Docker-based internal servers, and Kubernetes clusters.

---

## The Problem

Organisations that deliver custom learning programmes, training designs, or structured solution documents face a consistent set of operational bottlenecks:

| Pain Point | Business Impact |
|---|---|
| Designers draft similar documents repeatedly from scratch | High rework cost, slow turnaround |
| Historical project knowledge is stored in siloed files | Reuse is accidental, not systematic |
| Design quality varies significantly across teams | Inconsistent client experience |
| Approval and review cycles are tracked via email or spreadsheets | No audit trail; governance risk |
| Leadership has no visibility into throughput, quality, or AI spend | Blind spots in cost and capacity planning |

Syllabriq addresses all five directly.

---

## Product Overview

Syllabriq delivers a complete end-to-end workflow in a single platform:

```
Customer Requirement → Automated Design Draft → Quality Scoring
        → Primary Review → Dual Final Approval → Governed Export
                                    ↕
              Audit Trail | Leadership Dashboard | LLM Cost Tracking
```

Every step in this workflow is tracked, governed, and measurable.

---

## Core Capabilities

### 1. Requirement Ingestion

Designers submit customer requirements via file upload (PDF, DOCX, TXT, Markdown) or direct text entry — accommodating inputs from email, call notes, Teams messages, or Slack threads. The system normalises all inputs into a consistent structured format before processing.

### 2. Training Library & Knowledge Reuse

Administrators upload historical design documents to a managed training library. Syllabriq automatically extracts, chunks, and indexes these documents. When a new design is generated, the similarity engine retrieves the most relevant historical work — making institutional knowledge a first-class input, not an afterthought.

### 3. AI-Powered Design Generation

At the core of Syllabriq is a template-driven LLM generation engine. Designs are produced against a structured template with enforced sections (programme introduction, indicative design, prerequisites, key outcomes, detailed module breakdown, learning pedagogy). The system prompt encodes all template rules, ensuring output consistency regardless of which LLM provider is active.

**Supported LLM Providers (switchable at runtime):**

| Provider | Model | Best For |
|---|---|---|
| Ollama (local) | qwen2.5:7b-instruct | Fully offline / air-gapped deployments |
| Groq | llama-3.3-70b-versatile | Speed-optimised cloud (~30s per design) |
| Anthropic Claude | claude-3-5-sonnet-latest | High-quality nuanced output |
| OpenAI | gpt-4o | Enterprise cloud preference |
| OpenAI-Compatible | Custom endpoint | Bring-your-own provider flexibility |

No code restart is needed to switch providers — administrators change this in the UI.

### 4. 7-Dimension Quality Scoring

Every generated design is automatically evaluated across seven dimensions before it reaches a reviewer:

| Dimension | What It Measures |
|---|---|
| Requirement Coverage | Are all functional items from the brief present? |
| Template Completeness | Are all required sections populated? |
| Technical Consistency | Are the stated topics addressed in the design? |
| Reuse Relevance | Was relevant prior work surfaced and applied? |
| Design Quality | Are action verbs used? Tables present? Prerequisites stated? |
| Review Readiness | Is the design free of placeholders, gaps, and minimum length? |
| LLM Evaluation | Independent model evaluation of draft against requirement |

The weighted aggregate score guides reviewers and leadership on design maturity before time is spent in review.

### 5. Multi-Gate Approval Workflow

Syllabriq enforces a structured, two-stage approval process:

- **Primary Review** — One primary reviewer validates the draft. Rejection returns the design to the designer for rework.
- **Final Review** — Two independent final reviewers must both approve independently. A single dissent initiates a rework loop.

Designs cannot be exported in final form until the dual-signature gate is cleared. Every approval and rejection is timestamped and attributed.

**Design lifecycle states:**
`DRAFT_GENERATED → UNDER_PRIMARY_REVIEW → UNDER_FINAL_REVIEW → FINAL_APPROVED`

### 6. Governed Export

- **Draft stage:** Markdown and DOCX export available for internal iteration
- **Final approved stage:** DOCX and PDF export unlocked, branded with organisation palette
- Final exports are locked to the approved version; no post-approval edits are possible without a new workflow cycle

### 7. Immutable Audit Trail

Every significant action is logged — requirement uploads, design generations, similarity searches, review decisions, and exports — with actor email, timestamp, entity reference, and status. This log is queryable by administrators and satisfies governance and compliance documentation requirements.

### 8. Leadership & Operations Dashboard

**Leadership Dashboard (10 KPI cards):**

| Metric | Description |
|---|---|
| Active Users | Current platform adoption headcount |
| Designs Generated | Total AI-assisted design drafts created |
| Successfully Approved | Designs cleared through full review cycle |
| Approval Success Rate | % of generated designs reaching final approval |
| Average Design Score | Aggregate quality score across all designs |
| Final Downloads | Count of exported approved deliverables |
| Rejected / Rework Count | Designs requiring revision cycles |
| LLM Calls | Total AI inference requests made |
| Tokens Used | Cumulative token consumption |
| Estimated LLM Spend | Cost estimate across all providers |

Visual outputs include: generation funnel chart, approval mix breakdown, token spend by user (top 5), and a recent activity timeline.

Admin Reports panel provides a summary of pending reviews, average scores, pipeline breakdown, and the full workflow event stream.

---

## User Roles & Access Control

| Role | Capabilities |
|---|---|
| **Admin** | Full system access: user management, LLM configuration, training library, reporting, data management |
| **Designer** | Submit requirements, trigger design generation, view all designs, download drafts |
| **Primary Reviewer** | Review and approve or reject draft designs; access quality scorecard and similarity references |
| **Final Reviewer** | Dual-signature final approval; independently validates final designs |
| **Leadership** | Read-only access to leadership dashboard, usage analytics, and reporting |

Role assignment is managed by administrators and takes effect immediately.

---

## Technology Architecture

### Backend
- **FastAPI** — high-performance async REST API
- **SQLModel / SQLAlchemy** — type-safe ORM with Pydantic schema validation
- **Alembic** — database migration management
- **JWT + bcrypt** — authentication and secure password handling
- **SQLite** (development) / **PostgreSQL** (production)

### Frontend
- **React 18 + TypeScript** — component-driven UI
- **Vite** — fast build tooling

### Desktop
- **Electron 33** — cross-platform desktop shell (macOS, Windows, Linux)
- **Electron Builder** — installer packaging

### AI & Document Processing
- Ollama (local embeddings: nomic-embed-text; generation: qwen2.5:7b-instruct)
- python-docx (DOCX generation with brand styling)
- pypdf (PDF text extraction)
- reportlab (PDF output formatting)

### Infrastructure
- **Docker Compose** — multi-service orchestration (Ollama, PostgreSQL, FastAPI, React frontend)
- **Kubernetes manifests** — available for enterprise-scale deployment
- **DigitalOcean Droplet** — documented single-server cloud deployment path

---

## Deployment Options

| Mode | Best Fit | LLM | Database |
|---|---|---|---|
| **Local Desktop** | Individual designer / air-gapped | Ollama (local) | SQLite |
| **Docker Compose (Internal)** | Team / department server | Ollama or Groq | PostgreSQL |
| **Cloud Droplet (Demo / Pilot)** | Proof-of-concept, client demo | Groq API | PostgreSQL |
| **Kubernetes (Enterprise)** | Organisation-scale rollout | Any provider | PostgreSQL (persistent) |

The platform is designed to move through these stages progressively as adoption grows, with no application code changes required between modes.

---

## Security & Compliance Posture

- JWT-based authentication with role-scoped access enforcement on every API endpoint
- Passwords stored as bcrypt hashes; no plaintext credential storage
- Approved designs are immutably locked after the final review gate
- All actor actions are recorded in the audit event log with full attribution
- Local-first LLM option (Ollama) means sensitive design content never leaves the organisation's infrastructure
- Configurable CORS policy via `ALLOWED_ORIGINS` environment variable
- PostgreSQL with persistent volumes for production data integrity

---

## Business Value Summary

| Outcome | How Syllabriq Delivers It |
|---|---|
| **Faster design turnaround** | AI generation reduces drafting from days to minutes |
| **Consistent design quality** | Template enforcement and quality scoring at generation time |
| **Institutional knowledge reuse** | RAG pipeline retrieves and injects relevant historical work |
| **Reduced governance risk** | Dual-signature approval and immutable audit log |
| **Cost transparency** | Per-user, per-provider LLM cost tracking on leadership dashboard |
| **Deployment flexibility** | Runs offline, on-prem, or cloud — same codebase, no vendor lock-in |
| **Leadership visibility** | Adoption funnel, quality metrics, and AI spend in one dashboard |

---

## Intended Audiences

- **Learning & Development teams** delivering structured training programme designs
- **Pre-sales and solution design teams** producing repeated structured proposals
- **Operations and delivery managers** seeking governance and audit capability
- **Technology and AI leaders** evaluating LLM cost, quality, and compliance

---

## Current Status

| Phase | Status |
|---|---|
| Requirements & Architecture | Complete |
| Backend Development | Complete |
| Frontend Development | Complete |
| Electron Desktop Build | Complete |
| Docker / Kubernetes Configuration | Complete |
| Quality Scoring Engine | Complete |
| Approval Workflow | Complete |
| Leadership Dashboard | Complete |
| LLM Usage & Cost Tracking | Complete |
| Audit Trail & Event Logging | Complete |
| Testing (Unit + Integration) | Complete |
| Deployment Documentation | Inprogress |
| **Production Deployment** | Inprogress  |

---


