# Initializes essential data like Super Admin, platforms, and countries in the database.
import os, uuid
import asyncio
from datetime import datetime

from sqlalchemy import select

from backend.database.db import get_db
from backend.utils.enums import UserRole, AdapterType
from backend.service.auth_handler import AuthHandler
from backend.database.models.user import User as UserDB
from backend.database.migrations.user import User as UserTable
from backend.database.migrations.organization import Organization as OrganizationTable
from backend.database.migrations.platform import Platform as PlatformTable
from backend.database.migrations.country import Country as CountryTable

PLATFORMS = [
    {"name": "chatgpt", "display_name": "ChatGPT"},
    {"name": "perplexity", "display_name": "Perplexity"},
    {"name": "gemini", "display_name": "Gemini"},
    {"name": "ai_overview", "display_name": "Google AI Overviews"},
    {"name": "copilot", "display_name": "Microsoft Copilot"},
]

COUNTRIES = [
    {"code": "US", "name": "United States"},
    {"code": "GB", "name": "United Kingdom"},
    {"code": "DE", "name": "Germany"},
    {"code": "CA", "name": "Canada"},
    {"code": "AU", "name": "Australia"},
    {"code": "PK", "name": "Pakistan"},
]


async def seed_platforms(db):
    try:
        stmt = select(PlatformTable.name)
        result = await db.execute(stmt)
        existing = set(result.scalars().all())

        added = 0
        for p in PLATFORMS:
            if p["name"] not in existing:
                db.add(PlatformTable(
                    id=uuid.uuid4(),
                    name=p["name"],
                    display_name=p["display_name"],
                    adapter_type=AdapterType.SCRAPER,
                    is_active=True,
                ))
                added += 1
        await db.commit()
        print(f"Platforms seeded ({added} added, {len(existing)} existing).")
    except Exception as e:
        await db.rollback()
        print(f"failed to seed platforms: {e}")


async def seed_countries(db):
    try:
        stmt = select(CountryTable.code)
        result = await db.execute(stmt)
        existing = set(result.scalars().all())

        added = 0
        for c in COUNTRIES:
            if c["code"] not in existing:
                db.add(CountryTable(
                    id=uuid.uuid4(),
                    code=c["code"],
                    name=c["name"],
                    is_active=True,
                ))
                added += 1
        await db.commit()
        print(f"Countries seeded ({added} added, {len(existing)} existing).")
    except Exception as e:
        await db.rollback()
        print(f"failed to seed countries: {e}")


async def seed():
    # manually get session from get_db generator
    async for db in get_db():
        super_admin_id = uuid.uuid4()
        try:
            # Check if a super admin exists
            stmt = select(UserTable).where(UserTable.role == UserRole.SUPER_ADMIN.value)
            result = await db.execute(stmt)
            super_admin = result.scalars().first()

            if not super_admin:
                print("Super Admin does not exist at this time")

                org = OrganizationTable(
                    id=uuid.uuid4(), name="Super Admin Organization", attrs={}
                )
                db.add(org)
                await db.commit()
                await db.refresh(org)

                new_admin = await UserDB.create(
                    db,
                    name="Super Admin",
                    email=os.getenv("SUPER_ADMIN_EMAIL"),
                    password=AuthHandler.get_password_hash(
                        os.getenv("SUPER_ADMIN_PASSWORD")
                    ),
                    role=UserRole.SUPER_ADMIN.value,
                    signup_token="super-admin",
                    verified_at=datetime.now(),
                    organization_id=org.id,
                )

                print("Super Admin created.")
            else:
                print("Super Admin already exists.")

        except Exception as e:
            print(f"failed to create Super Admin: {e}")

        await seed_platforms(db)
        await seed_countries(db)


if __name__ == "__main__":
    asyncio.run(seed())
