# Architecture

This document describes the end-to-end architecture of NIITSyllabriq, including the ingestion pipeline, retrieval and generation flow, review lifecycle, and reporting model.

## 1. System Context

```mermaid
flowchart TB
    U1["Admin / Designer"] --> FE["React Frontend / Electron Desktop"]
    U2["Primary Reviewer"] --> FE
    U3["Final Reviewers"] --> FE

    FE --> API["FastAPI Application"]
    API --> DB["Postgres / SQLite"]
    API --> FS["Document Storage"]
    API --> OLLAMA["Ollama / Local LLM Runtime"]

    EXT1["Customer Requirement Files"] --> API
    EXT2["Historical Design PDFs / Docs"] --> API

    DB --> REP["Reporting & Audit Views"]
```

## 2. Logical Components

```mermaid
flowchart LR
    A["Authentication & RBAC"] --> B["Requirement Ingestion"]
    A --> C["Training Library Ingestion"]
    A --> D["Design Workflow"]
    A --> E["Reporting APIs"]

    B --> F["Normalization Service"]
    C --> F

    F --> G["Similarity Service"]
    G --> H["Template + Draft Generator"]
    H --> I["Scoring Service"]
    I --> J["Review Workflow Engine"]
    J --> K["Export Service"]

    B --> L["Workflow Event Logger"]
    C --> L
    G --> L
    H --> L
    I --> L
    J --> L
    K --> L
```

## 3. End-to-End Requirement-to-Design Flow

```mermaid
sequenceDiagram
    participant Designer
    participant UI as React / Electron UI
    participant API as FastAPI API
    participant Parser as Parsing Service
    participant Similarity as Similarity Engine
    participant LLM as Ollama
    participant DB as Database
    participant Primary as Primary Reviewer
    participant Final1 as Final Reviewer 1
    participant Final2 as Final Reviewer 2

    Designer->>UI: Upload historical design PDF
    UI->>API: POST /training/upload
    API->>Parser: Extract text + normalize
    API->>DB: Save trainingdocument
    API->>DB: Save workflowevent

    Designer->>UI: Upload new requirement
    UI->>API: POST /requirements/upload
    API->>Parser: Extract text + normalize
    API->>DB: Save requirement
    API->>DB: Save workflowevent

    Designer->>UI: Generate design
    UI->>API: POST /designs/generate/{id}
    API->>Similarity: Search prior requirements + training docs
    Similarity->>DB: Read historical corpus
    API->>LLM: Optional draft enhancement
    API->>DB: Save designdocument, references, scorecard, reviewtask
    API->>DB: Save workflowevent

    Primary->>UI: Review primary task
    UI->>API: POST /reviews/{task_id}/submit
    API->>DB: Update review status
    API->>DB: Create final review tasks if approved
    API->>DB: Save workflowevent

    Final1->>UI: Approve / reject
    UI->>API: POST /reviews/{task_id}/submit
    API->>DB: Update review status
    API->>DB: Save workflowevent

    Final2->>UI: Approve / reject
    UI->>API: POST /reviews/{task_id}/submit
    API->>DB: Update review status
    API->>DB: Mark final approval if both approved
    API->>DB: Save workflowevent

    Designer->>UI: Export approved design
    UI->>API: GET /designs/{design_id}/export
    API->>DB: Save workflowevent
```

## 4. Data Flow

```mermaid
flowchart LR
    R["Raw Requirement File"] --> P1["Parser"]
    T["Training PDF / Doc"] --> P2["Parser"]

    P1 --> NR["Normalized Requirement JSON"]
    P2 --> NT["Normalized Training JSON"]

    NR --> S["Similarity Search"]
    NT --> S
    H["Historical Requirements"] --> S
    D["Historical Designs"] --> S

    S --> M["Matched References"]
    NR --> G["Draft Generator"]
    M --> G
    G --> SC["Scoring + Traceability"]
    SC --> RV["Review Workflow"]
    RV --> EX["Export Layer"]
    RV --> EV["Workflow Event Log"]
```

## 5. Review State Model

```mermaid
stateDiagram-v2
    [*] --> RequirementReceived
    RequirementReceived --> DraftGenerated
    DraftGenerated --> UnderPrimaryReview
    UnderPrimaryReview --> PrimaryRejected
    UnderPrimaryReview --> UnderFinalReview
    UnderFinalReview --> FinalReworkRequired
    UnderFinalReview --> FinalApproved
    FinalApproved --> Exported
```

## 6. Persistence Model

Primary operational tables:

- `user`
- `trainingdocument`
- `requirement`
- `designdocument`
- `retrievedreference`
- `scorecard`
- `reviewtask`
- `workflowevent`

### Purpose of each table

- `trainingdocument`: stores historical or baseline documents uploaded for reuse
- `requirement`: stores normalized customer requirement inputs
- `designdocument`: stores generated draft and final design outputs
- `retrievedreference`: stores which prior requirement or training doc was reused
- `scorecard`: stores scoring and coverage results
- `reviewtask`: stores assigned approval tasks and review outcomes
- `workflowevent`: stores an immutable-style audit trail of important actions

## 7. Reporting Architecture

```mermaid
flowchart LR
    A["Operational Tables"] --> B["Reporting Service"]
    B --> C["Summary API"]
    B --> D["Event History API"]
    C --> E["Dashboard Cards"]
    D --> F["Audit Timeline"]
    A --> G["SQL / BI Queries"]
```

## 8. Deployment Topologies

### Desktop-first

- FastAPI on local machine
- SQLite
- Ollama locally
- Electron shell

### Shared internal deployment

- FastAPI behind reverse proxy
- Postgres
- shared file storage
- React served internally
- Ollama on internal GPU or inference workstation

### Hybrid

- local generation where needed
- central API and Postgres for workflow and reporting

## 9. Security Boundaries

- Authentication gates every business API except health/login
- Role-based access controls separate design authors from reviewers
- Workflow events create a traceable operational history
- Local-first model support reduces exposure of sensitive documents to external hosted LLMs

## 10. Recommended Next Enterprise Enhancements

- SSO / LDAP
- queue-based background processing
- centralized logging and metrics
- antivirus / content scanning
- branded DOCX/PDF formatting layer
- object storage abstraction for large-file management
