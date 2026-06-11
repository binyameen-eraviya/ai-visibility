import os
import secrets
import re
import logging
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.user import User as UserDB
from backend.database.models.organization import Organization as OrganizationDB
from backend.service.auth_handler import AuthHandler
from backend.service.email import email_service
from backend.utils.schema.request import UserSignup
from backend.utils.schema.response import SignupResponse, UserResponse
from backend.utils.custom_exceptions import NotFound as DataNotFoundException
from backend.utils.enums import UserRole

logger = logging.getLogger(__name__)


async def call(db: AsyncSession, payload: UserSignup) -> SignupResponse:
    """Handle user signup process - creates organization and registers user as admin."""
    try:
        _validate_signup_input(payload)
        await _check_user_exists(db, payload.email)
        
        organization = await _create_organization(db, payload)
        created_user, signup_token = await _create_user(db, payload, organization.id)

        # Dev convenience: skip email verification entirely so a freshly
        # signed-up user can log in immediately. Never bypasses verification
        # outside APP_ENV=development.
        if os.getenv("APP_ENV") == "development":
            created_user = await UserDB.verify(db, created_user.id)
            return _create_signup_response(
                created_user,
                organization.id,
                email_sent=False,
                verification_required=False,
                next_step="Account auto-verified (APP_ENV=development). You can log in now.",
            )

        email_sent = _send_verification_email(payload.email, payload.user_name, signup_token)
        return _create_signup_response(created_user, organization.id, email_sent)
        
    except HTTPException:
        raise
    except IntegrityError as e:
        if "unique constraint" in str(e).lower() and "email" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid data provided"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


def _validate_signup_input(payload: UserSignup) -> None:
    """Validate and normalize signup input data."""
    payload.email = payload.email.lower().strip()
    payload.user_name = payload.user_name.strip()
    payload.organization_name = payload.organization_name.strip()
    if not payload.email or not payload.password or not payload.user_name or not payload.organization_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User name, email, organization name, and password are required"
        )
    
    # Password strength validation
    if len(payload.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )

    # Basic email format validation
    # Use a conservative regex to catch obvious invalid addresses.
    email_pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    if not re.match(email_pattern, payload.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email address format"
        )


async def _check_user_exists(db: AsyncSession, email: str) -> None:
    """Check if user already exists with the given email."""
    try:
        await UserDB.find_by_email(db, email)
        # If we reach here, user exists
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )
    except DataNotFoundException:
        pass
    except HTTPException:
        # The 409 above is itself an HTTPException -- let it propagate rather
        # than being swallowed and re-wrapped as a 500 below.
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error checking existing user: " + str(e)
        )


async def _create_organization(db: AsyncSession, payload: UserSignup):
    """Create organization for the new user."""
    return await OrganizationDB.create(
        db=db,
        name=payload.organization_name,
        attrs={"created_by_signup": True}
    )


async def _create_user(db: AsyncSession, payload: UserSignup, organization_id: str) -> tuple:
    """Create user with hashed password and verification token."""
    hashed_password = AuthHandler.get_password_hash(payload.password)
    signup_token = secrets.token_urlsafe(32)
    created_user = await UserDB.create(
        db=db,
        name=payload.user_name,
        email=payload.email,
        organization_id=organization_id,
        password=hashed_password,
        signup_token=signup_token,
        role=UserRole.ADMIN.value,
        verified_at=None
    )
    
    return created_user, signup_token


def _send_verification_email(email: str, name: str, token: str) -> bool:
    """Send verification email to the user."""
    try:
        email_service.send_signup_verification(
            to_email=email,
            user_name=name,
            verification_token=token
        )
        return True
    except Exception as e:
        logger.warning("Failed to send verification email to %s: %s", email, e)
        return False


def _create_signup_response(
    user,
    organization_id: str,
    email_sent: bool,
    verification_required: bool = True,
    next_step: str = None,
) -> SignupResponse:
    """Create the signup response object."""
    user_response = UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        verified_at=user.verified_at
    )

    if next_step is None:
        next_step = "Please check your email for verification instructions" if email_sent else "Please contact support for verification"

    return SignupResponse(
        message="User registered successfully",
        user=user_response,
        organization_id=organization_id,
        email_sent=email_sent,
        verification_required=verification_required,
        next_step=next_step,
    )
