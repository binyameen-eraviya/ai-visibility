import uuid

from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.enums import TrackingFrequency
from backend.database.migrations.tracking_config import TrackingConfig as TrackingConfigTable
from backend.utils.custom_exceptions import (
    NotFound as DataNotFoundException,
    BadRequest as BadRequestException,
)

class TrackingConfig:
    async def find_by_id(db: AsyncSession, tracking_config_id: uuid.UUID):
        try:
            stmt = select(TrackingConfigTable).where(TrackingConfigTable.id == tracking_config_id)
            result = await db.execute(stmt)
            config = result.scalars().first()
            if not config:
                raise DataNotFoundException("Tracking config not found")
            return config
        except DataNotFoundException:
            raise
        except Exception as e:
            raise Exception(f"Error fetching tracking config by ID: {str(e)}")

    async def find_by_scope(
        db: AsyncSession,
        prompt_id: uuid.UUID,
        platform_id: uuid.UUID,
        country_id: uuid.UUID,
    ):
        """Return the config for a prompt+platform+country, or None if absent."""
        try:
            stmt = select(TrackingConfigTable).where(
                TrackingConfigTable.prompt_id == prompt_id,
                TrackingConfigTable.platform_id == platform_id,
                TrackingConfigTable.country_id == country_id,
            )
            result = await db.execute(stmt)
            return result.scalars().first()
        except Exception as e:
            raise Exception(f"Error fetching tracking config by scope: {str(e)}")

    async def find_by_project(db: AsyncSession, project_id: uuid.UUID):
        try:
            stmt = select(TrackingConfigTable).where(
                TrackingConfigTable.project_id == project_id
            ).order_by(desc(TrackingConfigTable.created_at))
            result = await db.execute(stmt)
            configs = result.scalars().all()
            return configs
        except Exception as e:
            raise Exception(f"Error fetching tracking configs by project: {str(e)}")

    async def find_active(db: AsyncSession, frequency: TrackingFrequency = None):
        """Active configs, optionally filtered by frequency (for the scheduler)."""
        try:
            stmt = select(TrackingConfigTable).where(TrackingConfigTable.is_active.is_(True))
            if frequency is not None:
                stmt = stmt.where(TrackingConfigTable.frequency == frequency)
            result = await db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            raise Exception(f"Error fetching active tracking configs: {str(e)}")

    async def create(
        db: AsyncSession,
        project_id: uuid.UUID,
        prompt_id: uuid.UUID,
        platform_id: uuid.UUID,
        country_id: uuid.UUID,
        frequency: TrackingFrequency = TrackingFrequency.DAILY,
    ):
        try:
            config = TrackingConfigTable(
                id=uuid.uuid4(),
                project_id=project_id,
                prompt_id=prompt_id,
                platform_id=platform_id,
                country_id=country_id,
                frequency=frequency,
            )
            db.add(config)
            await db.commit()
            await db.refresh(config)
            return config
        except IntegrityError:
            await db.rollback()
            raise BadRequestException(
                "Tracking config already exists for this prompt/platform/country"
            )
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error creating tracking config: {str(e)}")

    async def bulk_create(db: AsyncSession, project_id: uuid.UUID, configs: list):
        """Insert many configs at once; silently skips duplicates.

        Args:
            configs: list of dicts with prompt_id, platform_id, country_id,
                     and optional frequency.
        """
        try:
            values = [
                {
                    "id": uuid.uuid4(),
                    "project_id": project_id,
                    "prompt_id": c["prompt_id"],
                    "platform_id": c["platform_id"],
                    "country_id": c["country_id"],
                    "frequency": c.get("frequency") or TrackingFrequency.DAILY,
                }
                for c in configs
            ]
            if not values:
                return []

            stmt = insert(TrackingConfigTable).values(values).on_conflict_do_nothing(
                index_elements=["prompt_id", "platform_id", "country_id"]
            ).returning(TrackingConfigTable)
            result = await db.execute(stmt)
            created = result.scalars().all()
            await db.commit()
            return created
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error bulk creating tracking configs: {str(e)}")

    async def toggle_active(db: AsyncSession, tracking_config_id: uuid.UUID):
        try:
            config = await TrackingConfig.find_by_id(db, tracking_config_id)

            config.is_active = not config.is_active
            await db.commit()
            await db.refresh(config)
            return config
        except DataNotFoundException:
            raise
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error toggling tracking config: {str(e)}")
