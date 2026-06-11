from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.user import User as UserDB
from backend.service.auth_handler import AuthHandler
from backend.utils.schema.request import PasswordReset
from backend.utils.schema.response import PasswordResetCompleteResponse
from backend.utils.custom_exceptions import NotFound as DataNotFoundException


async def call(db: AsyncSession, payload: PasswordReset) -> PasswordResetCompleteResponse:
    """Complete password reset using email and reset token combination."""
    try:
        payload.email = payload.email.lower().strip()
        payload.token = payload.token.strip()
        payload.new_password = payload.new_password.strip()
        
        if not payload.email or not payload.token or not payload.new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email, reset token and new password are required"
            )
        
        if len(payload.new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long"
            )
        
        # Hash the new password
        hashed_password = AuthHandler.get_password_hash(payload.new_password)
        
        # Reset password using email and token combination
        try:
            user = await UserDB.reset_password(db, payload.email, payload.token, hashed_password)
        except DataNotFoundException:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email, reset token, or token has expired"
            )
        
        return PasswordResetCompleteResponse(
            message="Password reset successfully",
            user_id=user.id,
            next_step="You can now login with your new password"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
