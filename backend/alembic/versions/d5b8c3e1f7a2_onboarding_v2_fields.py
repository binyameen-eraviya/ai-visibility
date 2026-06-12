"""onboarding v2: brand profile + auto-detected fields on projects and brands

Revision ID: d5b8c3e1f7a2
Revises: c4a7e9d21b53
Create Date: 2026-06-12

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "d5b8c3e1f7a2"
down_revision = "c4a7e9d21b53"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # projects: brand profile + auto-detected context
    op.add_column("projects", sa.Column("description", sa.TEXT(), nullable=True))
    op.add_column("projects", sa.Column("industry", sa.TEXT(), nullable=True))
    op.add_column("projects", sa.Column("brand_identity", sa.JSON(), nullable=True))
    op.add_column("projects", sa.Column("products_services", sa.JSON(), nullable=True))
    op.add_column("projects", sa.Column("detected_location", sa.TEXT(), nullable=True))
    op.add_column("projects", sa.Column("detected_language", sa.TEXT(), server_default=sa.text("'en'"), nullable=False))
    op.add_column("projects", sa.Column("detected_timezone", sa.TEXT(), nullable=True))
    op.add_column("projects", sa.Column("favicon_url", sa.TEXT(), nullable=True))

    # brands: own site + favicon
    op.add_column("brands", sa.Column("website_url", sa.TEXT(), nullable=True))
    op.add_column("brands", sa.Column("favicon_url", sa.TEXT(), nullable=True))


def downgrade() -> None:
    op.drop_column("brands", "favicon_url")
    op.drop_column("brands", "website_url")
    op.drop_column("projects", "favicon_url")
    op.drop_column("projects", "detected_timezone")
    op.drop_column("projects", "detected_language")
    op.drop_column("projects", "detected_location")
    op.drop_column("projects", "products_services")
    op.drop_column("projects", "brand_identity")
    op.drop_column("projects", "industry")
    op.drop_column("projects", "description")
