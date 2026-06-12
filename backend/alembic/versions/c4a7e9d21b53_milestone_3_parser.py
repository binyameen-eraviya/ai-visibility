"""milestone 3 parser: url_type/classifier enums, parser columns, gap_scores + domain_classifications

Revision ID: c4a7e9d21b53
Revises: b1d4e7a2c9f3
Create Date: 2026-06-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "c4a7e9d21b53"
down_revision = "b1d4e7a2c9f3"
branch_labels = None
depends_on = None

url_type_enum = postgresql.ENUM(
    "LISTICLE", "ARTICLE", "HOMEPAGE", "PRODUCT_PAGE", "COMPARISON",
    "HOW_TO", "DISCUSSION", "OTHER",
    name="url_type",
    create_type=False,
)
domain_classifier_enum = postgresql.ENUM(
    "KNOWN_LIST", "LLM", "BRAND_MATCH", "MANUAL",
    name="domain_classifier",
    create_type=False,
)
# Reference to the (already existing) source_type enum for new columns/tables.
source_type_enum = postgresql.ENUM(name="source_type", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()

    # New enum types.
    url_type_enum.create(bind, checkfirst=True)
    domain_classifier_enum.create(bind, checkfirst=True)

    # Extend the existing source_type enum (PG 12+ allows ADD VALUE in a tx; the
    # new values are not used within this same migration so it's safe).
    op.execute("ALTER TYPE source_type ADD VALUE IF NOT EXISTS 'INSTITUTIONAL'")
    op.execute("ALTER TYPE source_type ADD VALUE IF NOT EXISTS 'COMPETITOR'")

    # answers.web_search_used
    op.add_column("answers", sa.Column("web_search_used", sa.BOOLEAN(), nullable=True))

    # sources.url_type
    op.add_column(
        "sources",
        sa.Column("url_type", url_type_enum, server_default="OTHER", nullable=False),
    )

    # source_metrics.url_type / retrieved_pct / citation_rate
    op.add_column(
        "source_metrics",
        sa.Column("url_type", url_type_enum, server_default="OTHER", nullable=False),
    )
    op.add_column(
        "source_metrics",
        sa.Column("retrieved_pct", sa.FLOAT(), server_default=sa.text("0"), nullable=False),
    )
    op.add_column(
        "source_metrics",
        sa.Column("citation_rate", sa.FLOAT(), server_default=sa.text("0"), nullable=False),
    )

    # daily_metrics.web_search_pct
    op.add_column(
        "daily_metrics",
        sa.Column("web_search_pct", sa.FLOAT(), server_default=sa.text("0"), nullable=False),
    )

    # gap_scores table
    op.create_table(
        "gap_scores",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("domain", sa.TEXT(), nullable=False),
        sa.Column("date", sa.DATE(), nullable=False),
        sa.Column("gap_score", sa.INTEGER(), server_default=sa.text("0"), nullable=False),
        sa.Column("competitor_mentions", sa.INTEGER(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "domain", "date", name="uq_gap_scores_project_domain_date"),
    )
    op.create_index("ix_gap_scores_project_date", "gap_scores", ["project_id", "date"], unique=False)

    # domain_classifications table (LLM-classification cache)
    op.create_table(
        "domain_classifications",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("domain", sa.TEXT(), nullable=False),
        sa.Column("domain_type", source_type_enum, server_default="OTHER", nullable=False),
        sa.Column("url_type", url_type_enum, nullable=True),
        sa.Column("classified_by", domain_classifier_enum, server_default="LLM", nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("domain", name="uq_domain_classifications_domain"),
    )


def downgrade() -> None:
    op.drop_table("domain_classifications")
    op.drop_index("ix_gap_scores_project_date", table_name="gap_scores")
    op.drop_table("gap_scores")

    op.drop_column("daily_metrics", "web_search_pct")
    op.drop_column("source_metrics", "citation_rate")
    op.drop_column("source_metrics", "retrieved_pct")
    op.drop_column("source_metrics", "url_type")
    op.drop_column("sources", "url_type")
    op.drop_column("answers", "web_search_used")

    bind = op.get_bind()
    domain_classifier_enum.drop(bind, checkfirst=True)
    url_type_enum.drop(bind, checkfirst=True)
    # Note: values added to source_type (INSTITUTIONAL, COMPETITOR) are NOT
    # removed -- Postgres has no DROP VALUE; leaving them is harmless.
