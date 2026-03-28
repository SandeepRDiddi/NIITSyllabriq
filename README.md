# NIIT Design Automation

Local-first requirement-to-design automation platform with:

- requirement ingestion from text, markdown, PDF, and DOCX
- similarity search against historical requirements and designs
- NIIT template-based draft generation
- optional local LLM enhancement through Ollama
- authentication and role-based access control
- training library upload for prior PDF/doc design documents
- one primary reviewer and two final reviewers
- weighted design quality scoring
- markdown, Word, and PDF export
- React frontend
- Postgres and Alembic migration support
- desktop packaging assets for reviewer machines
- workflow-event reporting at database level

## Features

### Workflow

1. Upload a customer requirement.
2. Normalize the requirement into structured JSON.
3. Search historical requirements for similar work.
4. Reuse similar content when the similarity threshold is met.
5. Generate a design draft in the NIIT template.
6. Route the draft to a primary reviewer.
7. Route approved drafts to two final reviewers.
8. Export the final approved design.

### Local model support

This service works without Ollama by falling back to deterministic heuristics.  
If Ollama is running locally, it will use:

- generation model: `qwen2.5:7b-instruct`
- embedding model: `nomic-embed-text`

You can change these with environment variables.

## Quick Start

### Run with Python

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

API docs:

- [http://localhost:8000/docs](http://localhost:8000/docs)

Seed accounts:

- `admin@niit.com / Admin@123`
- `designer@niit.com / Designer@123`
- `primary.reviewer@niit.com / Reviewer@123`
- `final.reviewer1@niit.com / Reviewer@123`
- `final.reviewer2@niit.com / Reviewer@123`

### Run React frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend URL:

- [http://localhost:5173](http://localhost:5173)
- End-to-end operator guide: [PRODUCTION_FLOW_GUIDE.md](/Users/sandeepdiddi/Documents/NIITSyllabriq/PRODUCTION_FLOW_GUIDE.md)

### Run with Docker

```bash
docker compose up --build
```

If Ollama is installed on the host, also make sure:

```bash
ollama pull qwen2.5:7b-instruct
ollama pull nomic-embed-text
ollama serve
```

## API Flow

### 1. Seed sample requirement

```bash
curl -X POST http://localhost:8000/seed/sample
```

### 2. Upload a requirement

```bash
curl -X POST "http://localhost:8000/requirements/upload?customer_name=CustomerA&title=AutomationDesign&created_by=sandeep" \
  -F "file=@sample_requirement.txt"
```

### 3. Generate design

```bash
curl -X POST http://localhost:8000/designs/generate/1 \
  -H "Content-Type: application/json" \
  -d '{"requested_by":"sandeep"}'
```

### 4. View review tasks

```bash
curl "http://localhost:8000/reviews"
```

### 5. Submit primary approval

```bash
curl -X POST http://localhost:8000/reviews/1/submit \
  -H "Content-Type: application/json" \
  -d '{"reviewer_name":"primary.reviewer@niit.com","decision":"approve","comments":"Looks good"}'
```

### 6. Submit both final approvals

```bash
curl -X POST http://localhost:8000/reviews/2/submit \
  -H "Content-Type: application/json" \
  -d '{"reviewer_name":"final.reviewer1@niit.com","decision":"approve","comments":"Approved"}'

curl -X POST http://localhost:8000/reviews/3/submit \
  -H "Content-Type: application/json" \
  -d '{"reviewer_name":"final.reviewer2@niit.com","decision":"approve","comments":"Approved"}'
```

### 7. Export final design

```bash
curl -OJ "http://localhost:8000/designs/1/export?version=final"
```

### 8. Upload a training document

```bash
curl -X POST "http://localhost:8000/training/upload?title=PortalBaseline" \
  -H "Authorization: Bearer <token>" \
  -F "file=@historical_design.pdf"
```

### 9. Reporting summary

```bash
curl http://localhost:8000/reports/summary \
  -H "Authorization: Bearer <admin-token>"
```

## Production Notes

This repository gives you a deployable MVP backend with production-oriented structure, but for a true enterprise production rollout you should still add:

- SSO or LDAP authentication
- encrypted document storage
- audit logging to a central system
- background job queue for large-file processing
- virus scanning for uploads
- retention and backup policies
- stronger PDF rendering if customer formatting must match corporate branding exactly

## Suggested Deployment Modes

### Single desktop

- FastAPI
- SQLite
- Ollama
- local file storage
- Electron shell in `desktop/`

### Shared low-cost office server

- FastAPI
- Postgres
- shared storage
- Ollama on one workstation with a GPU

### Hybrid

- local Ollama generation on desktops
- central FastAPI workflow and review server

## Database Migration

Use Alembic for Postgres or controlled schema changes:

```bash
alembic upgrade head
```

## Desktop Packaging

The Electron shell is in `desktop/`.

```bash
cd desktop
npm install
npm start
```

To build installers:

```bash
npm run package
```

## Project Structure

```text
app/
  api/
  core/
  db/
  models/
  schemas/
  services/
  storage/
  templates/
tests/
```
