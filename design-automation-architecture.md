# NIIT Design Automation Architecture

## 1. Goal

Build a local-first system that:

1. Accepts a customer requirement.
2. Checks existing design documents for similar work.
3. Reuses and enhances the closest matching design document when available.
4. Generates a new design from templates and LLM support when no good match exists.
5. Sends the draft to a human reviewer.
6. Sends approved drafts to two final reviewers.
7. Scores the quality and completeness of the design document.
8. Runs on employee desktops or on a low-cost shared deployment.

## 2. Recommended Workflow

### Stage A: Intake

Input:
- Customer requirement document
- Metadata: customer, domain, product, version, priority

System actions:
- Parse the requirement document into structured sections:
  - business goal
  - scope
  - functional requirements
  - non-functional requirements
  - assumptions
  - constraints
  - integrations
  - risks

Output:
- Normalized requirement JSON

### Stage B: Similarity Search

System actions:
- Chunk all existing design documents.
- Create embeddings for each chunk.
- Store embeddings in a local vector store.
- Compare the new requirement against prior designs.

Decision:
- If similarity score is above a threshold, retrieve top matching design documents and relevant sections.
- If similarity score is below the threshold, start a fresh design generation flow.

Recommended threshold:
- Start with `0.78` to `0.85` cosine similarity and tune after testing.

Output:
- Top 3 similar documents
- Reusable sections
- Similarity confidence score

### Stage C: Draft Generation

Path 1: Similar design exists
- Start with the standard NIIT template.
- Pull in matching sections from older designs.
- Ask the LLM to adapt those sections to the new requirement.
- Mark reused sections with provenance metadata for traceability.

Path 2: No similar design exists
- Start with the standard NIIT template.
- Ask the LLM to generate all sections from the normalized requirement.
- Run rule-based validation to check missing template sections.

Draft sections should include:
- Executive summary
- Problem statement
- Scope
- Functional design
- Non-functional design
- Architecture overview
- Data flow
- Integrations
- Assumptions
- Risks
- Open questions
- Test and validation considerations

Output:
- Draft design document
- Traceability map from requirement to design sections

### Stage D: Human-in-the-Loop Review

Reviewer 1:
- Reviews draft for business alignment and technical sanity.
- Can edit, comment, approve, or reject.

If rejected:
- Send back to draft stage with review comments.

If approved:
- Lock version and forward to final review.

### Stage E: Final Review

Reviewer 2 and Reviewer 3:
- Review independently or sequentially.
- Both must approve before release.

Recommended policy:
- One reviewer focuses on solution quality.
- One reviewer focuses on compliance/template/customer-readiness.

Output:
- Final approved design package

### Stage F: Delivery

System actions:
- Export to Word/PDF/Markdown as required.
- Attach review history and score summary.
- Produce a final release version.

## 3. Human Approval Workflow

Recommended states:

1. `REQUIREMENT_RECEIVED`
2. `DOCUMENT_MATCH_FOUND`
3. `DRAFT_GENERATED`
4. `UNDER_PRIMARY_REVIEW`
5. `PRIMARY_REJECTED`
6. `PRIMARY_APPROVED`
7. `UNDER_FINAL_REVIEW`
8. `FINAL_REWORK_REQUIRED`
9. `FINAL_APPROVED`
10. `DELIVERED`

Recommended approval rules:
- Primary reviewer approval is mandatory.
- Two final reviewers must approve.
- Any reject sends the document back with comments.
- Keep full version history for audit.

## 4. Scoring the Design Document

The score should not be a single LLM opinion. Use a weighted scoring model.

### Suggested score categories

1. Requirement coverage: 30%
- Are all customer requirements addressed?
- Is anything missed?

2. Template completeness: 20%
- Are all required NIIT template sections present?
- Are mandatory headings filled correctly?

3. Technical consistency: 20%
- Do architecture, integrations, assumptions, and constraints align?
- Are there contradictions?

4. Reuse relevance: 10%
- If prior content was reused, was it actually relevant?

5. Risk and assumption quality: 10%
- Are important risks and assumptions captured?

6. Review readiness: 10%
- Is the document clear enough for human review and customer delivery?

### Scoring method

Combine:
- Rule-based checks
- Retrieval coverage checks
- LLM evaluator
- Human reviewer override

Example final score:

`final_score = 0.4 * rules + 0.35 * requirement_coverage + 0.25 * llm_evaluation`

Recommended output:
- overall score out of 100
- section-wise score
- missing requirement list
- contradiction list
- reviewer confidence note

## 5. Suggested Local-First Technical Architecture

## Components

### 1. Document ingestion service
- Reads Word, PDF, Markdown, and text
- Extracts content and metadata

Suggested tools:
- Python
- `python-docx`
- `pypdf`
- `unstructured`

### 2. Template engine
- Stores the standard NIIT design template
- Fills sections with retrieved or generated content

Suggested tools:
- Jinja2
- Markdown or DOCX template generation

### 3. Embedding and similarity engine
- Converts requirements and documents into embeddings
- Stores vectors locally

Suggested tools:
- `bge-small-en-v1.5`
- `nomic-embed-text`
- local vector DB like Chroma or FAISS

### 4. Local LLM generation engine
- Generates or enhances design sections
- Runs fully on local machine when required

Suggested local models:
- `Mistral 7B Instruct`
- `Llama 3.1 8B Instruct`
- `Qwen2.5 7B Instruct`

Recommended runtime:
- Ollama for easiest desktop setup
- LM Studio for GUI-based local usage
- vLLM only if you later move to stronger shared hardware

### 5. Workflow engine
- Tracks state transitions
- Assigns review tasks
- Stores approvals and comments

Suggested options:
- Simple: FastAPI + SQLite
- Slightly richer: FastAPI + Postgres
- Automation/orchestration: n8n or Flowise

### 6. UI
- Upload requirements
- Show similar documents
- Show generated design draft
- Collect approvals and comments
- Show scoring dashboard

Suggested stack:
- React frontend
- FastAPI backend
- SQLite for desktop/local single-user deployment

## 6. Best Deployment Options

### Option A: Desktop-local for each reviewer

Best for:
- strict privacy
- low budget
- offline or near-offline use

Stack:
- Electron or desktop web app
- FastAPI backend
- SQLite
- Ollama
- Chroma/FAISS

Pros:
- fully local
- low recurring cost
- private data stays on user machine

Cons:
- each desktop needs setup
- model performance depends on laptop hardware
- document library sync becomes harder

### Option B: Shared low-cost internal server

Best for:
- better collaboration
- central document reuse library
- easier workflow management

Stack:
- FastAPI
- Postgres
- Chroma/pgvector
- Ollama on one GPU machine or CPU server
- simple web app

Low-cost hosting options:
- existing office desktop/workstation as internal server
- mini PC with enough RAM
- reused gaming PC with NVIDIA GPU

Pros:
- one shared source of truth
- easier approval workflow
- easier version control

Cons:
- needs internal server management
- not fully local to each reviewer

### Option C: Hybrid

Best overall recommendation.

Approach:
- Local generation on each reviewer desktop for sensitive drafts.
- Shared metadata and review workflow in a central low-cost server.
- Shared vector index for approved historical documents.

This gives:
- privacy for drafting
- collaboration for approvals
- strong document reuse

## 7. Recommended MVP

Start with a simple MVP before building a full platform.

### MVP scope

1. Upload requirement document.
2. Convert requirement into structured JSON.
3. Search similar existing designs.
4. Generate draft in NIIT template.
5. Show score and missing sections.
6. Route to one reviewer.
7. Route approved version to two final reviewers.
8. Export final document.

### MVP tech stack

- Frontend: React
- Backend: FastAPI
- Database: SQLite initially
- Embeddings: `nomic-embed-text` via Ollama
- Generation: `qwen2.5:7b-instruct` or `llama3.1:8b-instruct` via Ollama
- Vector store: Chroma
- File storage: local filesystem

## 8. Data Model

### Core entities

`Requirement`
- id
- customer_name
- source_file
- normalized_json
- created_by
- created_at

`DesignDocument`
- id
- requirement_id
- template_version
- draft_path
- final_path
- status
- score
- created_at

`RetrievedReference`
- id
- design_document_id
- source_document_id
- similarity_score
- reused_sections

`ReviewTask`
- id
- design_document_id
- reviewer_name
- review_type (`primary`, `final`)
- status
- comments
- reviewed_at

`ScoreCard`
- id
- design_document_id
- requirement_coverage_score
- template_completeness_score
- technical_consistency_score
- reuse_relevance_score
- risk_quality_score
- review_readiness_score
- overall_score

## 9. Guardrails

To reduce bad designs:

- Never let the LLM produce a final deliverable without human approval.
- Always show which old document sections were reused.
- Keep citation links from generated sections back to requirement inputs or source docs.
- Add mandatory checks for missing requirements.
- Add a policy that low-confidence outputs cannot move to final review.

Suggested blocking conditions:
- requirement coverage below 80%
- template completeness below 95%
- unresolved contradictions present
- open questions above threshold

## 10. Cost-Effective Local Model Guidance

### If laptops are modest
- Use `qwen2.5:7b-instruct` or `mistral:7b`
- Use smaller embedding model
- Expect slower but usable generation

### If desktops have good GPUs
- Use `llama3.1:8b`
- Consider higher-quality reranking model

### If no GPU
- Keep generation limited to section-by-section drafting
- Prefer retrieval-heavy design generation instead of full long-form generation

## 11. Suggested Implementation Phases

### Phase 1: Foundation
- Set up template storage
- Set up document ingestion
- Build similarity search
- Build basic draft generator

### Phase 2: Review workflow
- Add approval states
- Add review assignments
- Add comments and revision loop

### Phase 3: Scoring
- Add rule engine
- Add requirement traceability
- Add LLM evaluator
- Add score dashboard

### Phase 4: Deployment hardening
- Desktop packaging
- Shared server option
- Backup and sync
- Access control

## 12. What I Recommend For You

Best first version:

- Build a local-first web app with FastAPI + React.
- Use Ollama for local models.
- Use Chroma for similarity search.
- Use SQLite first, then move to Postgres only if multi-user traffic grows.
- Keep the generation flow retrieval-first, not pure LLM-first.
- Make human approval mandatory before final delivery.
- Use weighted scoring instead of only LLM scoring.

## 13. Next Buildable Deliverables

The next practical artifacts to create are:

1. Product requirements document for this automation system
2. Solution architecture document
3. Workflow/state diagram
4. Database schema
5. API specification
6. MVP implementation scaffold

If you want, the next step should be to generate the MVP solution architecture and scaffold the project structure in code.
