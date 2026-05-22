"""training document chunks"""

from alembic import op
import sqlalchemy as sa


revision = "20260327_0003"
down_revision = "20260327_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trainingchunk",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("training_document_id", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("embedding_json", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_trainingchunk_training_document_id"), "trainingchunk", ["training_document_id"], unique=False)
    op.create_index(op.f("ix_trainingchunk_chunk_index"), "trainingchunk", ["chunk_index"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_trainingchunk_chunk_index"), table_name="trainingchunk")
    op.drop_index(op.f("ix_trainingchunk_training_document_id"), table_name="trainingchunk")
    op.drop_table("trainingchunk")
