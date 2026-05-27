"""llm usage events"""

from alembic import op
import sqlalchemy as sa


revision = "20260327_0004"
down_revision = "20260327_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "llmusageevent",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("user_email", sa.String(), nullable=False),
        sa.Column("entity_type", sa.String(), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False),
        sa.Column("completion_tokens", sa.Integer(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), nullable=False),
        sa.Column("estimated_cost", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_llmusageevent_provider"), "llmusageevent", ["provider"], unique=False)
    op.create_index(op.f("ix_llmusageevent_model"), "llmusageevent", ["model"], unique=False)
    op.create_index(op.f("ix_llmusageevent_user_email"), "llmusageevent", ["user_email"], unique=False)
    op.create_index(op.f("ix_llmusageevent_entity_type"), "llmusageevent", ["entity_type"], unique=False)
    op.create_index(op.f("ix_llmusageevent_entity_id"), "llmusageevent", ["entity_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_llmusageevent_entity_id"), table_name="llmusageevent")
    op.drop_index(op.f("ix_llmusageevent_entity_type"), table_name="llmusageevent")
    op.drop_index(op.f("ix_llmusageevent_user_email"), table_name="llmusageevent")
    op.drop_index(op.f("ix_llmusageevent_model"), table_name="llmusageevent")
    op.drop_index(op.f("ix_llmusageevent_provider"), table_name="llmusageevent")
    op.drop_table("llmusageevent")
