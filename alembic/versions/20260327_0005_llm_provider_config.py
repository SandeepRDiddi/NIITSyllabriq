"""llm provider config"""

from alembic import op
import sqlalchemy as sa


revision = "20260327_0005"
down_revision = "20260327_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "llmproviderconfig",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("api_key", sa.String(), nullable=False),
        sa.Column("base_url", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("updated_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_llmproviderconfig_provider"), "llmproviderconfig", ["provider"], unique=False)
    op.create_index(op.f("ix_llmproviderconfig_is_active"), "llmproviderconfig", ["is_active"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_llmproviderconfig_is_active"), table_name="llmproviderconfig")
    op.drop_index(op.f("ix_llmproviderconfig_provider"), table_name="llmproviderconfig")
    op.drop_table("llmproviderconfig")
