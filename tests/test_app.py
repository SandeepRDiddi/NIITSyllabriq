import io
import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_niit_design_automation.db"
os.environ["LLM_PROVIDER"] = "ollama"
os.environ["GROQ_API_KEY"] = ""
os.environ["PRIMARY_REVIEWERS"] = "primary.reviewer@niit.com"
os.environ["FINAL_REVIEWERS"] = "final.reviewer1@niit.com,final.reviewer2@niit.com"

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.db.session import engine, init_db
from app.main import app
from app.models.training import TrainingChunk


db_path = Path("test_niit_design_automation.db")
if db_path.exists():
    db_path.unlink()
init_db()
client = TestClient(app)


def auth_headers(email: str, password: str):
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_healthcheck():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["llm_provider"] == "ollama"
    assert payload["generation_model"] == "qwen2.5:7b-instruct"
    assert payload["embedding_model"] == "nomic-embed-text"
    assert "ollama_reachable" in payload


def test_requirement_to_final_approval_flow():
    admin_headers = auth_headers("admin@niit.com", "Admin@123")
    primary_headers = auth_headers("primary.reviewer@niit.com", "Reviewer@123")
    final_one_headers = auth_headers("final.reviewer1@niit.com", "Reviewer@123")
    final_two_headers = auth_headers("final.reviewer2@niit.com", "Reviewer@123")

    training_upload = client.post(
        "/training/upload",
        params={"title": "Portal Design Baseline"},
        headers=admin_headers,
        files={
            "file": (
                "baseline.txt",
                io.BytesIO(
                    (
                        b"Customer portal baseline design.\n"
                        b"- Reuse similar design documents\n"
                        b"- Use local LLMs when no similar design exists\n"
                        b"- One primary reviewer\n"
                        b"- Two final reviewers\n"
                        b"- Score accuracy and completeness\n"
                    )
                ),
                "text/plain",
            )
        },
    )
    assert training_upload.status_code == 200

    upload = client.post(
        "/requirements/upload",
        params={
            "customer_name": "CustomerX",
            "title": "Local Automation Design",
        },
        headers=admin_headers,
        files={
            "file": (
                "requirement.txt",
                io.BytesIO(
                    (
                        b"Customer needs a local-first design automation platform.\n"
                        b"- Reuse similar design documents\n"
                        b"- Use local LLMs when no similar design exists\n"
                        b"- One primary reviewer\n"
                        b"- Two final reviewers\n"
                        b"- Score accuracy and completeness\n"
                    )
                ),
                "text/plain",
            )
        },
    )
    assert upload.status_code == 200
    with Session(engine) as session:
        chunks = session.exec(select(TrainingChunk)).all()
        assert len(chunks) >= 1
    requirement_id = upload.json()["id"]

    generated = client.post(
        f"/designs/generate/{requirement_id}",
        json={"requested_by": "admin@niit.com"},
        headers=admin_headers,
    )
    assert generated.status_code == 200
    design_payload = generated.json()
    assert design_payload["status"] == "UNDER_PRIMARY_REVIEW"
    assert design_payload["scorecard"]["overall_score"] >= 0
    assert any(ref["source_type"] in {"training_document", "requirement"} for ref in design_payload["references"])

    early_pdf_export = client.get(
        f"/designs/{design_payload['id']}/export",
        params={"version": "final", "file_format": "pdf"},
        headers=admin_headers,
    )
    assert early_pdf_export.status_code == 409

    reviews = client.get("/reviews", headers=primary_headers)
    assert reviews.status_code == 200
    tasks = reviews.json()
    primary = next(task for task in tasks if task["review_type"] == "primary")

    primary_approval = client.post(
        f"/reviews/{primary['id']}/submit",
        headers=primary_headers,
        json={
            "reviewer_name": "primary.reviewer@niit.com",
            "decision": "approve",
            "comments": "Primary review approved",
        },
    )
    assert primary_approval.status_code == 200
    assert primary_approval.json()["status"] == "APPROVED"

    first_final_review = client.get("/reviews", headers=final_one_headers).json()
    first_final_task = next(task for task in first_final_review if task["review_type"] == "final")
    response = client.post(
        f"/reviews/{first_final_task['id']}/submit",
        headers=final_one_headers,
        json={
            "reviewer_name": "final.reviewer1@niit.com",
            "decision": "approve",
            "comments": "Final approved",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"

    second_final_review = client.get("/reviews", headers=final_two_headers).json()
    second_final_task = next(task for task in second_final_review if task["review_type"] == "final")
    response = client.post(
        f"/reviews/{second_final_task['id']}/submit",
        headers=final_two_headers,
        json={
            "reviewer_name": "final.reviewer2@niit.com",
            "decision": "approve",
            "comments": "Final approved",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"

    designs = client.get("/designs", headers=admin_headers).json()
    design_id = designs[0]["id"]
    design = client.get(f"/designs/{design_id}", headers=admin_headers)
    assert design.status_code == 200
    assert design.json()["status"] == "FINAL_APPROVED"

    export = client.get(
        f"/designs/{design_id}/export",
        params={"version": "final", "file_format": "pdf"},
        headers=admin_headers,
    )
    assert export.status_code == 200

    reports = client.get("/reports/summary", headers=admin_headers)
    assert reports.status_code == 200
    summary = reports.json()
    assert summary["training_documents_count"] >= 1
    assert summary["requirements_count"] >= 1
    assert summary["designs_count"] >= 1
    assert summary["final_approved_count"] >= 1

    events = client.get("/reports/events", headers=admin_headers)
    assert events.status_code == 200
    event_types = {event["event_type"] for event in events.json()}
    assert "training_document_uploaded" in event_types
    assert "requirement_uploaded" in event_types
    assert "design_generated" in event_types
    assert "review_submitted" in event_types
    assert "design_exported" in event_types


def teardown_module():
    if db_path.exists():
        db_path.unlink()
