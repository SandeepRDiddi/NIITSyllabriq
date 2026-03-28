"""initial schema"""

from alembic import op
import sqlalchemy as sa


revision = "20260327_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_user_email"), "user", ["email"], unique=False)
    op.create_index(op.f("ix_user_role"), "user", ["role"], unique=False)

    op.create_table(
        "requirement",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_name", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("source_filename", sa.String(), nullable=False),
        sa.Column("source_path", sa.String(), nullable=False),
        sa.Column("raw_text", sa.String(), nullable=False),
        sa.Column("normalized_json", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_requirement_created_by"), "requirement", ["created_by"], unique=False)

    op.create_table(
        "designdocument",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("requirement_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("template_version", sa.String(), nullable=False),
        sa.Column("reused_content", sa.Boolean(), nullable=False),
        sa.Column("similarity_score", sa.Float(), nullable=False),
        sa.Column("draft_content", sa.String(), nullable=False),
        sa.Column("final_content", sa.String(), nullable=True),
        sa.Column("draft_path", sa.String(), nullable=True),
        sa.Column("final_path", sa.String(), nullable=True),
        sa.Column("traceability_map", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_designdocument_created_by"), "designdocument", ["created_by"], unique=False)
    op.create_index(op.f("ix_designdocument_requirement_id"), "designdocument", ["requirement_id"], unique=False)
    op.create_index(op.f("ix_designdocument_status"), "designdocument", ["status"], unique=False)

    op.create_table(
        "retrievedreference",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("design_document_id", sa.Integer(), nullable=False),
        sa.Column("source_requirement_id", sa.Integer(), nullable=False),
        sa.Column("source_design_id", sa.Integer(), nullable=True),
        sa.Column("source_title", sa.String(), nullable=False),
        sa.Column("similarity_score", sa.Float(), nullable=False),
        sa.Column("reused_sections", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_retrievedreference_design_document_id"), "retrievedreference", ["design_document_id"], unique=False)
    op.create_index(op.f("ix_retrievedreference_source_design_id"), "retrievedreference", ["source_design_id"], unique=False)
    op.create_index(op.f("ix_retrievedreference_source_requirement_id"), "retrievedreference", ["source_requirement_id"], unique=False)

    op.create_table(
        "scorecard",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("design_document_id", sa.Integer(), nullable=False),
        sa.Column("requirement_coverage_score", sa.Float(), nullable=False),
        sa.Column("template_completeness_score", sa.Float(), nullable=False),
        sa.Column("technical_consistency_score", sa.Float(), nullable=False),
        sa.Column("reuse_relevance_score", sa.Float(), nullable=False),
        sa.Column("risk_quality_score", sa.Float(), nullable=False),
        sa.Column("review_readiness_score", sa.Float(), nullable=False),
        sa.Column("llm_evaluation_score", sa.Float(), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("missing_requirements", sa.String(), nullable=False),
        sa.Column("contradictions", sa.String(), nullable=False),
        sa.Column("notes", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("design_document_id"),
    )
    op.create_index(op.f("ix_scorecard_design_document_id"), "scorecard", ["design_document_id"], unique=False)

    op.create_table(
        "reviewtask",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("design_document_id", sa.Integer(), nullable=False),
        sa.Column("reviewer_name", sa.String(), nullable=False),
        sa.Column("review_type", sa.String(), nullable=False),
        sa.Column("assigned_by", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("comments", sa.String(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reviewtask_design_document_id"), "reviewtask", ["design_document_id"], unique=False)
    op.create_index(op.f("ix_reviewtask_reviewer_name"), "reviewtask", ["reviewer_name"], unique=False)
    op.create_index(op.f("ix_reviewtask_review_type"), "reviewtask", ["review_type"], unique=False)
    op.create_index(op.f("ix_reviewtask_status"), "reviewtask", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_reviewtask_status"), table_name="reviewtask")
    op.drop_index(op.f("ix_reviewtask_review_type"), table_name="reviewtask")
    op.drop_index(op.f("ix_reviewtask_reviewer_name"), table_name="reviewtask")
    op.drop_index(op.f("ix_reviewtask_design_document_id"), table_name="reviewtask")
    op.drop_table("reviewtask")
    op.drop_index(op.f("ix_scorecard_design_document_id"), table_name="scorecard")
    op.drop_table("scorecard")
    op.drop_index(op.f("ix_retrievedreference_source_requirement_id"), table_name="retrievedreference")
    op.drop_index(op.f("ix_retrievedreference_source_design_id"), table_name="retrievedreference")
    op.drop_index(op.f("ix_retrievedreference_design_document_id"), table_name="retrievedreference")
    op.drop_table("retrievedreference")
    op.drop_index(op.f("ix_designdocument_status"), table_name="designdocument")
    op.drop_index(op.f("ix_designdocument_requirement_id"), table_name="designdocument")
    op.drop_index(op.f("ix_designdocument_created_by"), table_name="designdocument")
    op.drop_table("designdocument")
    op.drop_index(op.f("ix_requirement_created_by"), table_name="requirement")
    op.drop_table("requirement")
    op.drop_index(op.f("ix_user_role"), table_name="user")
    op.drop_index(op.f("ix_user_email"), table_name="user")
    op.drop_table("user")
