"""scrape_accounts: account pool table (Milestone 2)

Revision ID: b1d4e7a2c9f3
Revises: 8f2c41d9a0b1
Create Date: 2026-06-11

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "b1d4e7a2c9f3"
down_revision = "8f2c41d9a0b1"
branch_labels = None
depends_on = None

scrape_account_status_enum = postgresql.ENUM(
    "ACTIVE", "COOLDOWN", "BANNED", "DISABLED",
    name="scrape_account_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    scrape_account_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "scrape_accounts",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("platform_id", sa.UUID(), nullable=False),
        sa.Column("email", sa.TEXT(), nullable=False),
        sa.Column("cookies", sa.JSON(), nullable=True),
        sa.Column("daily_quota_used", sa.INTEGER(), server_default=sa.text("0"), nullable=False),
        sa.Column("daily_quota_limit", sa.INTEGER(), server_default=sa.text("10"), nullable=False),
        sa.Column("cooldown_until", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("status", scrape_account_status_enum, server_default="ACTIVE", nullable=False),
        sa.Column("attrs", sa.JSON(), nullable=True),
        sa.Column("last_used_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["platform_id"], ["platforms.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_scrape_accounts_platform_status",
        "scrape_accounts",
        ["platform_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_scrape_accounts_platform_status", table_name="scrape_accounts")
    op.drop_table("scrape_accounts")

    bind = op.get_bind()
    scrape_account_status_enum.drop(bind, checkfirst=True)
