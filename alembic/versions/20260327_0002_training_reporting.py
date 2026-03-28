"""training and reporting schema"""

from alembic import op
import sqlalchemy as sa


revision = "20260327_0002"
down_revision = "20260327_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trainingdocument",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("source_filename", sa.String(), nullable=False),
        sa.Column("source_path", sa.String(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("raw_text", sa.String(), nullable=False),
        sa.Column("normalized_json", sa.String(), nullable=False),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("uploaded_by", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_trainingdocument_uploaded_by"), "trainingdocument", ["uploaded_by"], unique=False)
    op.create_index(op.f("ix_trainingdocument_status"), "trainingdocument", ["status"], unique=False)

    op.create_table(
        "workflowevent",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("entity_type", sa.String(), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("actor_email", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("details_json", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workflowevent_actor_email"), "workflowevent", ["actor_email"], unique=False)
    op.create_index(op.f("ix_workflowevent_entity_id"), "workflowevent", ["entity_id"], unique=False)
    op.create_index(op.f("ix_workflowevent_entity_type"), "workflowevent", ["entity_type"], unique=False)
    op.create_index(op.f("ix_workflowevent_event_type"), "workflowevent", ["event_type"], unique=False)
    op.create_index(op.f("ix_workflowevent_status"), "workflowevent", ["status"], unique=False)

    op.add_column("retrievedreference", sa.Column("source_training_document_id", sa.Integer(), nullable=True))
    op.add_column("retrievedreference", sa.Column("source_type", sa.String(), nullable=False, server_default="requirement"))
    op.create_index(op.f("ix_retrievedreference_source_training_document_id"), "retrievedreference", ["source_training_document_id"], unique=False)
    op.create_index(op.f("ix_retrievedreference_source_type"), "retrievedreference", ["source_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_retrievedreference_source_type"), table_name="retrievedreference")
    op.drop_index(op.f("ix_retrievedreference_source_training_document_id"), table_name="retrievedreference")
    op.drop_column("retrievedreference", "source_type")
    op.drop_column("retrievedreference", "source_training_document_id")

    op.drop_index(op.f("ix_workflowevent_status"), table_name="workflowevent")
    op.drop_index(op.f("ix_workflowevent_event_type"), table_name="workflowevent")
    op.drop_index(op.f("ix_workflowevent_entity_type"), table_name="workflowevent")
    op.drop_index(op.f("ix_workflowevent_entity_id"), table_name="workflowevent")
    op.drop_index(op.f("ix_workflowevent_actor_email"), table_name="workflowevent")
    op.drop_table("workflowevent")

    op.drop_index(op.f("ix_trainingdocument_status"), table_name="trainingdocument")
    op.drop_index(op.f("ix_trainingdocument_uploaded_by"), table_name="trainingdocument")
    op.drop_table("trainingdocument")
