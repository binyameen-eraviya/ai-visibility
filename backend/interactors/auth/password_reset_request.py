import secrets
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.user import User as UserDB
from backend.service.email import email_service
from backend.utils.schema.request import PasswordResetRequest
from backend.utils.schema.response import PasswordResetResponse
from backend.utils.custom_exceptions import NotFound as DataNotFoundException


async def call(db: AsyncSession, payload: PasswordResetRequest) -> PasswordResetResponse:
    """Request password reset - sends email with reset token."""
    try:
        payload.email = payload.email.lower().strip()
        
        if not payload.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required"
            )
        
        # Check if user exists
        try:
            user = await UserDB.find_by_email(db, payload.email)
        except DataNotFoundException:
            # For security, don't reveal if email exists or not
            return PasswordResetResponse(
                message="If an account with this email exists, you will receive a password reset link",
                email_sent=False,
                next_step="Check your email for reset instructions"
            )
        
        # Generate reset token (expires in 1 hour)
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        # Save reset token to database
        await UserDB.set_reset_token(db, payload.email, reset_token, expires_at)
        
        # Send reset email
        email_sent = False
        try:
            email_service.send_password_reset(
                to_email=payload.email,
                user_name=user.name,
                reset_token=reset_token
            )
            email_sent = True
        except Exception as e:
            print(f"Failed to send reset email to {payload.email}: {str(e)}")
        
        return PasswordResetResponse(
            message="If an account with this email exists, you will receive a password reset link",
            email_sent=email_sent,
            next_step="Check your email for reset instructions"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
