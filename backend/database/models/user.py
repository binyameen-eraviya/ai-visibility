import uuid
from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.enums import UserRole
from backend.database.migrations.user import User as UserTable
from backend.utils.custom_exceptions import (
    NotFound as DataNotFoundException,
    Unauthorized as UserNotVerifiedException,
)

class User:
    async def find_by_id(db: AsyncSession, user_id: uuid.UUID):
        try:
            stmt = select(UserTable).where(UserTable.id == user_id)
            result = await db.execute(stmt)
            user = result.scalars().first()
            if not user:
                raise DataNotFoundException("User not found")
            return user
        except DataNotFoundException:
            raise
        except Exception as e:
            raise Exception(f"Error fetching user by ID: {str(e)}")

    async def find_by_email(db: AsyncSession, email: str):
        try:
            stmt = select(UserTable).where(UserTable.email == email)
            result = await db.execute(stmt)
            user = result.scalars().first()
            if not user:
                raise DataNotFoundException("User not found")
            return user
        except DataNotFoundException:
            raise  # Let DataNotFoundException bubble up to be handled by calling code
        except Exception as e:
            raise Exception(f"Error fetching user by email: {str(e)}")

    async def find_by_credentials(db: AsyncSession, email: str, password: str):
        try:
            stmt = select(UserTable).where(UserTable.email == email)
            result = await db.execute(stmt)
            user = result.scalars().first()
            # First ensure user exists and the password is correct. This prevents
            # revealing verification status when the password is wrong.
            from backend.service.auth_handler import AuthHandler
            if not user or not AuthHandler.verify_password(password, user.password):
                raise DataNotFoundException("User not found")

            # Now check verification status and raise a clear exception if not verified
            if not user.verified_at:
                raise UserNotVerifiedException("User not verified")

            return user
        except DataNotFoundException:
            raise
        except UserNotVerifiedException:
            raise
        except Exception as e:
            raise Exception(f"Error fetching user by credentials: {str(e)}")

    async def create(
        db: AsyncSession,
        name: str,
        email: str,
        organization_id: uuid.UUID,
        password: str,
        signup_token: str,
        role: str = None,
        verified_at: datetime = None,
    ):
        try:
            user_data = {
                "id": uuid.uuid4(),
                "name": name,
                "email": email,
                "organization_id": organization_id,
                "password": password,
                "signup_token": signup_token,
            }
            if verified_at:
                user_data["verified_at"] = verified_at
            if role:
                user_data["role"] = role

            user = UserTable(**user_data)
            db.add(user)
            await db.commit()
            return user
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error creating user: {str(e)}")

    async def signup_verify_by_token(db: AsyncSession, email: str, token: str):
        try:
            stmt = select(UserTable).where(
                UserTable.email == email,
                UserTable.signup_token == token
            )
            result = await db.execute(stmt)
            user = result.scalars().first()
            if not user:
                raise DataNotFoundException("User not found")  # intentionally silent

            user.verified_at = datetime.now()
            await db.commit()
            return None
        except DataNotFoundException:
            # re-raise so it can be handled cleanly in the interactor
            raise
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error verifying signup by token: {str(e)}")

    async def delete(db: AsyncSession, user_id: uuid.UUID):
        try:
            stmt = select(UserTable).where(UserTable.id == user_id)
            result = await db.execute(stmt)
            user = result.scalars().first()
            if not user or user.role == UserRole.SUPER_ADMIN:
                raise DataNotFoundException("User not found")

            await db.delete(user)
            await db.commit()
            return None
        except DataNotFoundException:
            raise
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error deleting user: {str(e)}")

    async def get_list(db: AsyncSession):
        try:
            stmt = select(UserTable).order_by(desc(UserTable.created_at))
            result = await db.execute(stmt)
            users = result.scalars().all()
            return users
        except Exception as e:
            raise Exception(f"Error fetching user list: {str(e)}")

    async def find_by_organization_id(db: AsyncSession, organization_id: uuid.UUID):
        try:
            stmt = select(UserTable).where(
                UserTable.organization_id == organization_id
            ).order_by(desc(UserTable.created_at))
            result = await db.execute(stmt)
            users = result.scalars().all()
            return users
        except Exception as e:
            raise Exception(f"Error fetching users by organization ID: {str(e)}")

    async def update_role(db: AsyncSession, user_id: uuid.UUID, role: str):
        try:
            stmt = select(UserTable).where(UserTable.id == user_id)
            result = await db.execute(stmt)
            user = result.scalars().first()
            if not user or user.role == UserRole.SUPER_ADMIN:
                raise DataNotFoundException("User not found")

            user.role = role
            await db.commit()
            return None
        except DataNotFoundException:
            raise
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error updating user role: {str(e)}")

    async def set_reset_token(db: AsyncSession, email: str, reset_token: str, expires_at: datetime):
        """Set password reset token in user attrs."""
        try:
            stmt = select(UserTable).where(UserTable.email == email)
            result = await db.execute(stmt)
            user = result.scalars().first()
            if not user:
                raise DataNotFoundException("User not found")

            # Store reset token data in attrs JSON field
            if not user.attrs:
                user.attrs = {}
            
            user.attrs["reset_token"] = reset_token
            user.attrs["reset_token_expires"] = expires_at.isoformat()
            await db.commit()
            return user
        except DataNotFoundException:
            raise
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error setting reset token: {str(e)}")

    async def find_by_reset_token(db: AsyncSession, reset_token: str):
        """Find user by reset token stored in attrs."""
        try:
            # Filter in SQL on the JSON attrs column instead of loading all users.
            stmt = select(UserTable).where(
                UserTable.attrs["reset_token"].as_string() == reset_token
            )
            result = await db.execute(stmt)
            user = result.scalars().first()
            if not user:
                raise DataNotFoundException("Invalid reset token")
            return user
        except DataNotFoundException:
            raise
        except Exception as e:
            raise Exception(f"Error finding user by reset token: {str(e)}")

    async def reset_password(db: AsyncSession, email: str, reset_token: str, new_password: str):
        """Reset user password using email and reset token from attrs."""
        try:
            stmt = select(UserTable).where(UserTable.email == email)
            result = await db.execute(stmt)
            user = result.scalars().first()
            if not user:
                raise DataNotFoundException("Invalid email or reset token")

            # Check if reset token exists and matches
            user_reset_token = user.attrs.get("reset_token") if user.attrs else None
            if not user_reset_token or user_reset_token != reset_token:
                raise DataNotFoundException("Invalid email or reset token")

            # Check if token is expired
            reset_expires_str = user.attrs.get("reset_token_expires") if user.attrs else None
            if reset_expires_str:
                reset_expires = datetime.fromisoformat(reset_expires_str)
                if reset_expires < datetime.now(timezone.utc):
                    raise DataNotFoundException("Reset token has expired")

            # Update password and clear reset token from attrs
            user.password = new_password
            if user.attrs:
                user.attrs.pop("reset_token", None)
                user.attrs.pop("reset_token_expires", None)
            
            await db.commit()
            return user
        except DataNotFoundException:
            raise
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error resetting password: {str(e)}")
