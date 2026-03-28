# NIIT Design Automation Production Flow Guide

## Goal

This guide shows the exact end-to-end flow you asked for:

1. Upload one existing PDF design document as the seed knowledge document.
2. Upload a new customer requirement.
3. Generate a draft design using reuse-first logic.
4. Send it through primary review and two final reviews.
5. Export the final design.
6. Track every step in the database for reporting.

## Production-Style Components

### Backend
- FastAPI API
- SQLModel domain models
- Alembic migrations
- Postgres or SQLite
- Local Ollama integration

### Frontend
- React dashboard
- Role-based login
- Training document upload
- Requirement upload
- Design generation
- Review task handling
- Reporting summary

### Desktop
- Electron shell for reviewer machines

## Roles

### Admin
- manages users
- uploads training documents
- uploads requirements
- monitors reports

### Designer
- uploads training documents
- uploads requirements
- generates designs

### Primary Reviewer
- reviews generated draft
- approves or rejects

### Final Reviewer
- gives final sign-off

## End-to-End Scenario

### Step 1: Start services

Backend:

```bash
cd /Users/sandeepdiddi/Documents/NIITSyllabriq
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

Frontend:

```bash
cd /Users/sandeepdiddi/Documents/NIITSyllabriq/frontend
npm install
npm run dev
```

Optional desktop shell:

```bash
cd /Users/sandeepdiddi/Documents/NIITSyllabriq/desktop
npm install
npm start
```

## Step 2: Login

Use:

- `admin@niit.com / Admin@123`

This gives access to:

- training document upload
- requirement upload
- design generation
- reporting summary

## Step 3: Upload one simple PDF for training

In the UI:

1. Open the `Upload Training PDF` section.
2. Enter a title like `Customer Portal Design Baseline`.
3. Upload your PDF.
4. Submit.

What happens:

- the PDF is parsed
- text is normalized
- the document is saved as a `TrainingDocument`
- a `training_document_uploaded` event is written to the database

DB entities updated:

- `trainingdocument`
- `workflowevent`

## Step 4: Upload a new customer requirement

In the UI:

1. Open `Upload New Requirement`.
2. Enter customer name and requirement title.
3. Upload the new requirement file.
4. Submit.

What happens:

- the requirement is parsed and normalized
- the requirement is stored
- a `requirement_uploaded` event is written

DB entities updated:

- `requirement`
- `workflowevent`

## Step 5: Generate design

In the UI:

1. Find the requirement in `Requirements`.
2. Click `Generate Design`.

What happens:

- similarity search runs against:
  - earlier requirements
  - uploaded training documents
- if the training PDF is most similar, its sections are selected for reuse
- the NIIT template is filled
- local Ollama enhances the draft if available
- scoring runs
- primary review task is created
- `design_generated` event is written

DB entities updated:

- `designdocument`
- `retrievedreference`
- `scorecard`
- `reviewtask`
- `workflowevent`

## Step 6: Primary review

Login as:

- `primary.reviewer@niit.com / Reviewer@123`

In the UI:

1. Open `Review Tasks`.
2. Approve or reject the primary review.

What happens:

- review task status changes
- design status changes to either:
  - `PRIMARY_REJECTED`
  - `UNDER_FINAL_REVIEW`
- if approved, two final review tasks are created
- `review_submitted` event is written

## Step 7: Final review

Login as:

- `final.reviewer1@niit.com / Reviewer@123`
- `final.reviewer2@niit.com / Reviewer@123`

Each reviewer:

1. Opens their assigned tasks
2. Approves or rejects

What happens:

- both approvals are required
- if both approve, design status becomes `FINAL_APPROVED`
- final markdown is saved
- exports become available
- `review_submitted` events are written

## Step 8: Export final design

Use the design card to export:

- Markdown
- DOCX
- PDF

What happens:

- file is generated
- `design_exported` event is written

## DB-Level Reporting

The system tracks all major actions in the database.

### Main business tables

- `trainingdocument`
- `requirement`
- `designdocument`
- `retrievedreference`
- `scorecard`
- `reviewtask`
- `workflowevent`
- `user`

### What `workflowevent` gives you

This is the core reporting/audit table.

Each event records:

- event type
- entity type
- entity id
- actor email
- status
- JSON details
- timestamp

### Example event types

- `training_document_uploaded`
- `requirement_uploaded`
- `design_generated`
- `review_submitted`
- `design_exported`

## Reporting APIs

### Summary

```bash
curl http://localhost:8000/reports/summary \
  -H "Authorization: Bearer <admin-token>"
```

Returns:

- number of training docs
- number of requirements
- number of designs
- pending review counts
- final approved count
- average design score
- recent events

### Events

```bash
curl "http://localhost:8000/reports/events?entity_type=design_document" \
  -H "Authorization: Bearer <admin-token>"
```

Use this for:

- audit trails
- SLA analysis
- throughput tracking
- reviewer activity reporting

## Suggested SQL Reporting Queries

### Count designs by status

```sql
select status, count(*)
from designdocument
group by status
order by count(*) desc;
```

### Average quality score

```sql
select round(avg(overall_score), 2) as avg_score
from scorecard;
```

### Reviewer workload

```sql
select reviewer_name, review_type, status, count(*) as total
from reviewtask
group by reviewer_name, review_type, status
order by reviewer_name, review_type;
```

### End-to-end audit for one design

```sql
select event_type, entity_type, entity_id, actor_email, status, created_at
from workflowevent
where entity_type in ('design_document', 'review_task')
order by created_at;
```

### Which training document was reused

```sql
select design_document_id, source_type, source_training_document_id, source_title, similarity_score
from retrievedreference
where source_type = 'training_document';
```

## What To Demo With One PDF

Use this script for a stakeholder demo:

1. Upload one historical PDF design document.
2. Show it appearing in `Training Library`.
3. Upload a fresh requirement.
4. Generate the design.
5. Show the design similarity score and references.
6. Log in as primary reviewer and approve.
7. Log in as both final reviewers and approve.
8. Export to PDF or DOCX.
9. Open the reporting summary and recent workflow events.
10. Show SQL or API output proving every step was captured.

## Recommended Production Deployment

### Application tier
- FastAPI behind Nginx
- React built as static assets
- Electron app for desktops if needed

### Data tier
- Postgres for production
- nightly backups
- role-based DB access

### AI tier
- Ollama on local or internal GPU workstations
- fallback heuristic mode when local LLM is unavailable

### Security tier
- replace local passwords with SSO/LDAP
- store JWT secret securely
- restrict CORS
- encrypt backups and storage

## Reality Check

This repository is now much closer to a production-style app, but enterprise production still usually needs:

- SSO or LDAP
- centralized logging and monitoring
- queue workers
- virus scanning
- branded document layouts
- disaster recovery and backup automation
- load and security testing
