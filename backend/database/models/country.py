import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.migrations.country import Country as CountryTable
from backend.utils.custom_exceptions import NotFound as DataNotFoundException

class Country:
    async def find_by_id(db: AsyncSession, country_id: uuid.UUID):
        try:
            stmt = select(CountryTable).where(CountryTable.id == country_id)
            result = await db.execute(stmt)
            country = result.scalars().first()
            if not country:
                raise DataNotFoundException("Country not found")
            return country
        except DataNotFoundException:
            raise
        except Exception as e:
            raise Exception(f"Error fetching country by ID: {str(e)}")

    async def find_default(db: AsyncSession, preferred_code: str = "US"):
        """Pick a sensible default country (US if present, else first by code).

        Used when a scrape request omits country_id -- the tracking config still
        needs one, and country is ignored until proxies land (Milestone 4).
        """
        try:
            stmt = select(CountryTable).where(CountryTable.code == preferred_code)
            result = await db.execute(stmt)
            country = result.scalars().first()
            if country:
                return country

            stmt = select(CountryTable).order_by(CountryTable.code)
            result = await db.execute(stmt)
            country = result.scalars().first()
            if not country:
                raise DataNotFoundException("No countries configured")
            return country
        except DataNotFoundException:
            raise
        except Exception as e:
            raise Exception(f"Error fetching default country: {str(e)}")

    async def get_list(db: AsyncSession, active_only: bool = False):
        try:
            stmt = select(CountryTable).order_by(CountryTable.code)
            if active_only:
                stmt = stmt.where(CountryTable.is_active.is_(True))
            result = await db.execute(stmt)
            countries = result.scalars().all()
            return countries
        except Exception as e:
            raise Exception(f"Error fetching country list: {str(e)}")
