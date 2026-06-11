from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.user import User as UserDB
from backend.utils.schema.request import SignupVerify
from backend.utils.schema.response import UserResponse, VerificationResponse
from backend.utils.custom_exceptions import NotFound as DataNotFoundException


async def call(db: AsyncSession, payload: SignupVerify):
    """
    Handle email verification process.
    Verifies user's email using the token sent in verification email.
    
    Args:
        db: Async database session
        payload: SignupVerify data containing email and verification token
        
    Returns:
        dict: Success response with user details
        
    Raises:
        HTTPException: For validation errors or verification failures
    """
    try:
        # Normalize email
        payload.email = payload.email.lower().strip()
        payload.token = payload.token.strip()
        
        # Input validation
        if not payload.email or not payload.token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and verification token are required"
            )
        
        # Find user by email first
        try:
            user = await UserDB.find_by_email(db, payload.email)
        except DataNotFoundException:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user is already verified
        if user.verified_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already verified"
            )
        
        # Verify the token matches
        if user.signup_token != payload.token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )
        
        # Verify the user's email
        await UserDB.signup_verify_by_token(db, payload.email, payload.token)
        
        # Get updated user data
        verified_user = await UserDB.find_by_email(db, payload.email)
        
        # Create response using proper schema
        user_response = UserResponse(
            id=verified_user.id,
            name=verified_user.name,
            email=verified_user.email,
            role=verified_user.role,
            verified_at=verified_user.verified_at
        )
        
        # Return structured response using VerificationResponse schema
        return VerificationResponse(
            message="Email verified successfully",
            user=user_response,
            verified_at=verified_user.verified_at,
            next_step="You can now login to your account"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
