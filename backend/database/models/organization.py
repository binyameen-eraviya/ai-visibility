import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.migrations.organization import Organization as OrganizationTable
from backend.utils.custom_exceptions import NotFound as DataNotFoundException


class Organization:
    async def find_by_id(db: AsyncSession, organization_id: uuid.UUID):
        """
        Retrieve organization by ID.
        
        Args:
            db: Async database session
            organization_id: UUID of the organization
            
        Returns:
            Organization object
            
        Raises:
            DataNotFoundException: If organization not found
        """
        try:
            stmt = select(OrganizationTable).where(OrganizationTable.id == organization_id)
            result = await db.execute(stmt)
            organization = result.scalars().first()
            if not organization:
                raise DataNotFoundException("Organization not found")
            return organization
        except DataNotFoundException:
            # Let intentional errors bubble up
            raise
        except Exception as e:
            raise Exception(f"Error fetching organization by ID: {str(e)}")

    async def create(db: AsyncSession, name: str, attrs: dict = None):
        """
        Create a new organization.
        
        Args:
            db: Async database session
            name: Organization name
            attrs: Additional attributes (optional)
            
        Returns:
            Organization: Created organization object
            
        Raises:
            Exception: For database operation failures
        """
        try:
            organization_data = {
                "id": uuid.uuid4(),
                "name": name,
                "attrs": attrs or {}
            }
            
            organization = OrganizationTable(**organization_data)
            db.add(organization)
            await db.commit()
            await db.refresh(organization)
            return organization
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error creating organization: {str(e)}")

    async def update_attrs(db: AsyncSession, organization_id: uuid.UUID, attrs: dict):
        """
        Update organization attributes.
        
        Args:
            db: Async database session
            organization_id: UUID of the organization
            attrs: New attributes to update
            
        Returns:
            None
            
        Raises:
            DataNotFoundException: If organization not found
        """
        try:
            stmt = select(OrganizationTable).where(OrganizationTable.id == organization_id)
            result = await db.execute(stmt)
            organization = result.scalars().first()
            if not organization:
                raise DataNotFoundException("Organization not found")
            
            organization.attrs = attrs
            organization.updated_at = datetime.now()
            await db.commit()
            return None
        except DataNotFoundException:
            raise
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error updating organization: {str(e)}")

    async def get_users_count(db: AsyncSession, organization_id: uuid.UUID):
        """
        Get count of users in organization.
        
        Args:
            db: Async database session
            organization_id: UUID of the organization
            
        Returns:
            int: Number of users in organization
            
        Raises:
            DataNotFoundException: If organization not found
        """
        try:
            from backend.database.migrations.user import User as UserTable
            
            # Verify organization exists
            await Organization.find_by_id(db, organization_id)
            
            stmt = select(UserTable).where(
                UserTable.organization_id == organization_id,
                UserTable.deleted_at.is_(None)
            )
            result = await db.execute(stmt)
            users = result.scalars().all()
            
            return len(users)
        except DataNotFoundException:
            raise
        except Exception as e:
            raise Exception(f"Error counting organization users: {str(e)}")
