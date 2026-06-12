import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.enums import SourceType, UrlType, DomainClassifier
from backend.database.migrations.domain_classification import (
    DomainClassification as DomainClassificationTable,
)


class DomainClassification:
    async def get_many(db: AsyncSession, domains: list) -> dict:
        """Return {domain: row} for every cached domain in `domains`."""
        if not domains:
            return {}
        try:
            stmt = select(DomainClassificationTable).where(
                DomainClassificationTable.domain.in_(list(set(domains)))
            )
            result = await db.execute(stmt)
            return {row.domain: row for row in result.scalars().all()}
        except Exception as e:
            raise Exception(f"Error fetching domain classifications: {str(e)}")

    async def upsert(
        db: AsyncSession,
        domain: str,
        domain_type: SourceType,
        classified_by: DomainClassifier,
        url_type: UrlType = None,
    ):
        """Cache a domain classification (idempotent on domain)."""
        try:
            fields = {
                "domain_type": domain_type,
                "url_type": url_type,
                "classified_by": classified_by,
            }
            stmt = insert(DomainClassificationTable).values(
                id=uuid.uuid4(),
                domain=domain,
                **fields,
            ).on_conflict_do_update(
                constraint="uq_domain_classifications_domain",
                set_=fields,
            ).returning(DomainClassificationTable)
            result = await db.execute(stmt)
            row = result.scalars().first()
            await db.commit()
            return row
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error upserting domain classification: {str(e)}")
